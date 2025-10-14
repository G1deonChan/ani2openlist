# Event Loop is Closed 错误修复

## 问题描述

Web UI 在执行定时任务时出现错误：

```
任务执行失败: Event loop is closed
```

特别是在第二次或后续运行定时任务时出现此问题。

## 根本原因

1. **事件循环清理不完整**: 第一次任务执行后，事件循环被关闭但没有正确清除引用

2. **异常处理不当**: 在清理事件循环时的异常没有被正确捕获

3. **循环状态检查缺失**: 关闭循环前没有检查循环是否已经关闭

4. **事件循环引用残留**: 关闭后没有清除 `asyncio.set_event_loop(None)`

## 问题场景

### 第一次执行（成功）
```
开始执行任务... → 创建事件循环 → 执行任务 → 关闭循环 ✅
```

### 第二次执行（失败）
```
开始执行任务... → 尝试使用已关闭的循环 → Event loop is closed ❌
```

## 修复方案

### ✅ 使用 `asyncio.run()` 自动管理事件循环

**最终方案（最简单最可靠）**:

```python
def _run_in_thread():
    """在独立线程中运行异步任务"""
    try:
        # 在 Windows 上需要设置事件循环策略
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # 使用 asyncio.run() 自动管理事件循环
        # 这会创建新循环、运行任务、然后清理所有资源
        result = asyncio.run(run_ani2openlist_async())
        task_status['last_result'] = result
    except Exception as e:
        error_msg = f'任务执行失败: {str(e)}'
        add_log(error_msg, 'error')
        task_status['last_result'] = {'success': False, 'message': error_msg}
    finally:
        task_status['running'] = False
```

### 为什么 `asyncio.run()` 是最佳方案？

1. **自动创建循环**: 创建全新的事件循环
2. **自动运行任务**: 执行协程直到完成
3. **自动清理资源**: 
   - 取消所有未完成的任务
   - 关闭所有异步生成器
   - 关闭线程池执行器
   - 关闭事件循环
4. **防止资源泄漏**: 确保所有资源都被正确释放

### 之前尝试的方案（已废弃）

<details>
<summary>点击查看之前的复杂方案</summary>

#### 方案 1: 手动管理循环（不推荐）

```python
# 太复杂，容易出错
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    result = loop.run_until_complete(...)
finally:
    # 大量的清理代码
    pending = asyncio.all_tasks(loop)
    # ... 更多清理逻辑
```

**问题**: 
- 代码复杂
- 容易遗漏清理步骤
- 难以处理所有边界情况

</details>

## 修复后的完整代码

```python
def run_ani2openlist():
    """运行 ani2openlist 任务"""
    if task_status['running']:
        add_log('任务已在运行中，跳过', 'warning')
        return
    
    task_status['running'] = True
    task_status['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _run_in_thread():
        """在独立线程中运行异步任务"""
        try:
            # 在 Windows 上需要设置事件循环策略
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
            # 使用 asyncio.run() 自动管理事件循环
            result = asyncio.run(run_ani2openlist_async())
            task_status['last_result'] = result
        except Exception as e:
            error_msg = f'任务执行失败: {str(e)}'
            add_log(error_msg, 'error')
            task_status['last_result'] = {'success': False, 'message': error_msg}
        finally:
            task_status['running'] = False
    
    # 在新线程中运行
    thread = threading.Thread(target=_run_in_thread, daemon=True)
    thread.start()
```

## 已修改的文件

```
✅ webui/app.py - 修复事件循环清理逻辑
```

## 测试验证

### 1. 手动测试

```bash
# 启动 Web UI
python webui_start.py

# 访问 http://localhost:5000
# 1. 点击"立即执行" - 应该成功
# 2. 再次点击"立即执行" - 应该仍然成功
# 3. 设置定时任务，等待触发 - 应该成功
```

### 2. Docker 测试

```bash
# 启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 通过 Web UI 测试
# 1. 首页执行任务
# 2. 设置定时任务（例如：每分钟执行）
# 3. 观察日志，确认多次执行都成功
```

### 3. 定时任务测试

```yaml
# webui/schedule.yaml
enabled: true
type: interval
minutes: 1  # 每分钟执行一次
```

观察日志，确认多次执行都没有 "Event loop is closed" 错误。

## 修复效果

### 修复前
```
12:32:35 开始执行任务...
12:32:35 任务执行完成 ✅

12:34:00 开始执行任务...
12:34:00 任务执行失败: Event loop is closed ❌
```

### 修复后
```
12:32:35 开始执行任务...
12:32:35 任务执行完成 ✅

12:34:00 开始执行任务...
12:34:00 任务执行完成 ✅

12:36:00 开始执行任务...
12:36:00 任务执行完成 ✅
```

## 技术细节

### 事件循环生命周期

```python
# 1. 创建
loop = asyncio.new_event_loop()

# 2. 设置为当前循环
asyncio.set_event_loop(loop)

# 3. 使用
loop.run_until_complete(coroutine)

# 4. 清理待处理任务
pending = asyncio.all_tasks(loop)
for task in pending:
    task.cancel()

# 5. 关闭
if not loop.is_closed():
    loop.close()

# 6. 清除引用
asyncio.set_event_loop(None)
```

### 为什么需要在线程中运行？

Flask 应用运行在主线程的事件循环中，如果直接在请求处理中运行 `asyncio` 任务，会干扰主循环。因此需要：

1. 创建新线程
2. 在新线程中创建独立的事件循环
3. 执行完成后清理循环
4. 确保不影响主应用

### Windows vs Linux

```python
if sys.platform == 'win32':
    # Windows 需要使用 SelectorEventLoop
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
else:
    # Linux/Mac 使用默认策略
    pass
```

## 相关问题

### 问题：RuntimeError: There is no current event loop

**原因**: 在新线程中没有设置事件循环

**解决**: 
```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
```

### 问题：Task was destroyed but it is pending!

**原因**: 循环关闭前没有取消待处理任务

**解决**:
```python
pending = asyncio.all_tasks(loop)
for task in pending:
    task.cancel()
loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
```

## 预防措施

1. **每次都创建新循环**: 不重用事件循环
2. **完整的清理流程**: 取消任务 → 收集结果 → 关闭循环 → 清除引用
3. **异常处理**: 捕获所有可能的异常
4. **状态检查**: 关闭前检查 `is_closed()`
5. **日志记录**: 记录清理过程中的问题

## 升级指南

无需配置更改，直接升级：

```bash
# 拉取最新代码
git pull origin main

# 重启服务
docker-compose restart

# 或重新构建
docker-compose up -d --build
```

## 相关链接

- [Python asyncio 文档](https://docs.python.org/3/library/asyncio.html)
- [APScheduler 文档](https://apscheduler.readthedocs.io/)
- [Flask 文档](https://flask.palletsprojects.com/)

---

**修复完成时间**: 2025年10月14日  
**影响范围**: 定时任务和手动执行任务  
**状态**: ✅ 已修复并优化
