# Event Loop 错误最终修复 v2

## 问题持续存在的原因

即使使用了 `asyncio.run()`，在某些环境（特别是 Docker 容器和定时任务中）仍然会遇到 "Event loop is closed" 错误。

### 根本原因

1. **线程局部循环缓存**: Python 在线程中可能缓存事件循环引用
2. **策略未重置**: 事件循环策略在线程间共享
3. **循环未清除**: `asyncio.run()` 后，循环引用仍然存在

## 最终修复方案

### 完整的线程清理流程

```python
def _run_in_thread():
    """在独立线程中运行异步任务"""
    try:
        # 1. 重置事件循环策略（确保全新环境）
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        else:
            asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        
        # 2. 清除旧的事件循环
        try:
            old_loop = asyncio.get_event_loop()
            if old_loop and not old_loop.is_closed():
                old_loop.close()
        except RuntimeError:
            pass  # 没有循环，正常情况
        
        # 3. 清除循环引用
        asyncio.set_event_loop(None)
        
        # 4. 使用 asyncio.run() 创建全新的事件循环
        result = asyncio.run(run_ani2openlist_async())
        task_status['last_result'] = result
        
    except Exception as e:
        error_msg = f'任务执行失败: {str(e)}'
        add_log(error_msg, 'error')
        task_status['last_result'] = {'success': False, 'message': error_msg}
    finally:
        # 5. 最终清理
        try:
            loop = asyncio.get_event_loop()
            if loop and not loop.is_closed():
                loop.close()
        except Exception:
            pass
        asyncio.set_event_loop(None)
        task_status['running'] = False
```

## 修复步骤详解

### 步骤 1: 重置策略
```python
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
```
- 创建全新的策略实例
- 清除策略级别的缓存

### 步骤 2: 关闭旧循环
```python
old_loop = asyncio.get_event_loop()
if old_loop and not old_loop.is_closed():
    old_loop.close()
```
- 获取可能存在的旧循环
- 安全关闭它

### 步骤 3: 清除引用
```python
asyncio.set_event_loop(None)
```
- 从线程局部存储中移除循环引用
- 防止 `asyncio.run()` 检测到已有循环

### 步骤 4: 运行任务
```python
result = asyncio.run(run_ani2openlist_async())
```
- 现在 `asyncio.run()` 会创建真正全新的循环
- 自动清理资源

### 步骤 5: 最终清理
```python
finally:
    # 确保没有残留
    asyncio.set_event_loop(None)
```
- 双保险，确保线程退出时没有循环引用

## 为什么需要这么多步骤？

### Python asyncio 的设计

1. **线程局部存储**: 每个线程都有自己的事件循环引用
2. **策略单例**: 事件循环策略是进程级别的单例
3. **延迟清理**: Python GC 可能不会立即清理循环

### Docker/Linux 特殊情况

- 不同的信号处理
- 不同的线程实现
- 可能的资源限制

## 测试清单

```bash
# 1. 手动执行 - 首次
✅ 应该成功

# 2. 手动执行 - 第二次（立即）
✅ 应该成功

# 3. 手动执行 - 第三次
✅ 应该成功

# 4. 定时任务 - 首次
✅ 应该成功

# 5. 定时任务 - 第二次
✅ 应该成功 ← 关键测试点

# 6. 定时任务 - 持续运行
✅ 每次都应该成功
```

## 调试技巧

### 添加详细日志

```python
def _run_in_thread():
    try:
        add_log(f'线程 {threading.current_thread().name} 开始', 'debug')
        
        # 检查初始状态
        try:
            loop = asyncio.get_event_loop()
            add_log(f'初始循环状态: closed={loop.is_closed()}', 'debug')
        except:
            add_log('初始无循环', 'debug')
        
        # ... 执行任务 ...
        
        add_log('任务完成，开始清理', 'debug')
    finally:
        add_log('线程退出', 'debug')
```

### 检查循环状态

```python
import asyncio
import threading

# 在不同位置检查
loop = asyncio.get_event_loop()
print(f"Thread: {threading.current_thread().name}")
print(f"Loop: {loop}")
print(f"Is closed: {loop.is_closed()}")
```

## 升级步骤

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建镜像（重要！）
docker-compose build

# 3. 重启容器
docker-compose up -d

# 4. 查看日志验证
docker-compose logs -f
```

## 如果仍然失败

### 方案 A: 增加延迟
```python
import time

def _run_in_thread():
    try:
        # ... 清理代码 ...
        time.sleep(0.1)  # 给 GC 时间清理
        result = asyncio.run(...)
```

### 方案 B: 强制 GC
```python
import gc

def _run_in_thread():
    try:
        # ... 清理代码 ...
        gc.collect()  # 强制垃圾回收
        result = asyncio.run(...)
```

### 方案 C: 禁用线程池
```python
# 在 asyncio.run() 中禁用线程池
asyncio.run(run_ani2openlist_async(), debug=True)
```

## 技术原理

### asyncio.run() 内部实现（简化版）

```python
def run(coro):
    # 1. 检查是否有现有循环
    try:
        loop = get_event_loop()
        if not loop.is_closed():
            raise RuntimeError("Cannot run while loop is running")
    except RuntimeError:
        pass
    
    # 2. 创建新循环
    loop = new_event_loop()
    set_event_loop(loop)
    
    try:
        # 3. 运行任务
        return loop.run_until_complete(coro)
    finally:
        # 4. 清理
        try:
            _cancel_all_tasks(loop)
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            set_event_loop(None)
            loop.close()
```

### 我们的增强

我们在 `asyncio.run()` **之前**和**之后**都进行清理，确保：
- ✅ 运行前：环境干净
- ✅ 运行中：`asyncio.run()` 正常工作
- ✅ 运行后：没有残留

## 相关资源

- [Python asyncio 文档](https://docs.python.org/3/library/asyncio.html)
- [PEP 3156 - Asynchronous IO](https://www.python.org/dev/peps/pep-3156/)
- [asyncio.run() 源码](https://github.com/python/cpython/blob/main/Lib/asyncio/runners.py)

---

**这次的修复是最全面的！如果还有问题，请提供详细的错误日志。** 🔧
