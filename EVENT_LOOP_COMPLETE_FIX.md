# Event Loop 错误最终完整解决方案

## 🎯 问题演变历程

### 第一阶段：Event loop is closed
```
第一次执行: ✅ SUCCESS
第二次执行: ❌ ERROR - Event loop is closed
```
**原因**: httpx.AsyncClient 未关闭，持有旧循环引用

### 第二阶段：Client has been closed
```
第一次执行: ✅ SUCCESS
清理客户端...
第二次执行: ❌ ERROR - Cannot send a request, as the client has been closed
```
**原因**: 关闭了客户端但没有清除缓存，下次复用了已关闭的客户端

### 最终方案：关闭 + 清除缓存

## ✅ 完整解决方案

### 核心思路

1. **任务完成后**：关闭所有 HTTP 客户端
2. **清除缓存**：让 `RequestUtils` 忘记这些客户端
3. **下次任务时**：自动创建全新的客户端

### 实现细节

#### 1. RequestUtils.close_all_async_clients()

**文件**: `ani2openlist/utils/http.py`

```python
@classmethod
async def close_all_async_clients(cls) -> None:
    """
    关闭所有异步 HTTP 客户端并清除缓存
    用于清理资源，防止事件循环关闭时出现警告
    下次调用 get_client() 时会自动创建新的客户端
    """
    # 1. 关闭所有缓存的客户端
    for client in cls.__clients.values():
        try:
            await client.close_async_client()
        except Exception:
            pass
    
    # 2. ⭐ 关键：清除缓存字典
    cls.__clients.clear()
    
    # 3. 关闭弱引用集合中的客户端
    for client in list(cls.__client_list):
        try:
            await client.close_async_client()
        except Exception:
            pass
```

**关键点**: `cls.__clients.clear()` 确保下次 `get_client()` 会创建新客户端

#### 2. run_ani2openlist_async()

**文件**: `webui/app.py`

```python
async def run_ani2openlist_async():
    """异步运行 ani2openlist"""
    try:
        add_log('开始执行任务...')
        config = load_config(str(CONFIG_PATH))
        ani = Ani2Openlist(config=config)
        await ani.run()
        add_log('任务执行完成', 'success')
        return {'success': True, 'message': '任务执行成功'}
    except Exception as e:
        error_msg = f'任务执行失败: {str(e)}'
        add_log(error_msg, 'error')
        return {'success': False, 'message': error_msg}
    finally:
        # ⭐ 清理 HTTP 客户端并清除缓存
        try:
            await RequestUtils.close_all_async_clients()
        except Exception as e:
            logger.debug(f'清理 HTTP 客户端失败: {e}')
```

#### 3. 事件循环管理（保持不变）

**文件**: `webui/app.py`

```python
def _run_in_thread():
    """在独立线程中运行异步任务"""
    try:
        # 1. 创建新的事件循环策略
        if sys.platform == 'win32':
            policy = asyncio.WindowsSelectorEventLoopPolicy()
        else:
            policy = asyncio.DefaultEventLoopPolicy()
        
        # 2. 创建全新的事件循环
        loop = policy.new_event_loop()
        
        # 3. 设置为当前线程的事件循环
        asyncio.set_event_loop(loop)
        
        try:
            # 4. 运行异步任务
            result = loop.run_until_complete(run_ani2openlist_async())
            task_status['last_result'] = result
        finally:
            # 5. 清理异步生成器
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:
                pass
            
            # 6. 关闭默认执行器
            try:
                loop.run_until_complete(loop.shutdown_default_executor())
            except Exception:
                pass
            
            # 7. 关闭循环
            loop.close()
            
            # 8. 清除线程引用
            asyncio.set_event_loop(None)
            
    except Exception as e:
        error_msg = f'任务执行失败: {str(e)}'
        add_log(error_msg, 'error')
        task_status['last_result'] = {'success': False, 'message': error_msg}
    finally:
        task_status['running'] = False
```

## 🔄 执行流程

### 第一次任务执行

```
1. 创建新事件循环 loop1
2. 创建 Ani2Openlist 实例
   └─> OpenlistClient.__init__()
       └─> RequestUtils.get_client()
           └─> 缓存中没有，创建 HTTPClient A
               └─> 创建 AsyncClient A
3. 运行任务（成功）
4. finally 块：
   └─> await RequestUtils.close_all_async_clients()
       ├─> await AsyncClient A.aclose()  ✅ 关闭连接
       └─> cls.__clients.clear()         ✅ 清除缓存
5. 关闭 loop1
```

### 第二次任务执行

```
1. 创建新事件循环 loop2
2. 创建 Ani2Openlist 实例
   └─> OpenlistClient.__init__()
       └─> RequestUtils.get_client()
           └─> 缓存已清空！创建新的 HTTPClient B
               └─> 创建新的 AsyncClient B（使用 loop2）
3. 运行任务（成功）✅
4. finally 块：
   └─> await RequestUtils.close_all_async_clients()
       ├─> await AsyncClient B.aclose()  ✅ 关闭连接
       └─> cls.__clients.clear()         ✅ 清除缓存
5. 关闭 loop2
```

## 📊 修复前后对比

### ❌ 修复前（第二阶段）

```python
# 任务完成后
await client.aclose()  # ✅ 关闭了客户端
# ❌ 但没有清除缓存！

# 下次任务
client = RequestUtils.get_client(url)
# 返回缓存中的 client（已关闭）
await client.request(...)
# 💥 ERROR: Cannot send a request, as the client has been closed
```

### ✅ 修复后（当前）

```python
# 任务完成后
await client.aclose()    # ✅ 关闭客户端
cls.__clients.clear()    # ✅ 清除缓存

# 下次任务
client = RequestUtils.get_client(url)
# 缓存为空，创建新的 client
await client.request(...)
# ✅ SUCCESS
```

## 🧪 测试步骤

```bash
# 1. 重新构建 Docker 镜像（必须！）
docker-compose build --no-cache

# 2. 停止旧容器
docker-compose down

# 3. 启动新容器
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

### 测试场景

在 Web UI 中测试以下场景：

```
✅ 场景 1: 手动执行第一次
   预期: SUCCESS

✅ 场景 2: 手动执行第二次（立即点击）
   预期: SUCCESS

✅ 场景 3: 手动执行第三次
   预期: SUCCESS

✅ 场景 4: 设置定时任务（如 2 分钟后）
   预期: 任务设置成功

✅ 场景 5: 等待定时任务第一次执行
   预期: SUCCESS

✅ 场景 6: 等待定时任务第二次执行
   预期: SUCCESS

✅ 场景 7: 定时任务期间手动执行
   预期: SUCCESS
```

## 📝 修改的文件列表

1. **ani2openlist/utils/http.py**
   - 修改 `RequestUtils.close_all_async_clients()`
   - 添加 `cls.__clients.clear()` 清除缓存

2. **webui/app.py**
   - 在 `run_ani2openlist_async()` 的 `finally` 块中调用清理方法
   - 导入 `RequestUtils` 和 `logger`
   - 保持优化的事件循环管理

## 🎓 关键要点

### 1. 资源管理 = 清理 + 遗忘

```python
# ❌ 只清理，不遗忘
await client.aclose()
# 缓存仍然持有引用

# ✅ 清理 + 遗忘
await client.aclose()
cache.clear()  # 让系统忘记它
```

### 2. 缓存失效策略

```python
# 单例/缓存模式的正确清理
class Singleton:
    __instances = {}
    
    @classmethod
    def get_instance(cls):
        if key not in cls.__instances:
            cls.__instances[key] = cls()
        return cls.__instances[key]
    
    @classmethod
    def cleanup(cls):
        # 1. 清理每个实例
        for instance in cls.__instances.values():
            instance.close()
        # 2. 清除缓存
        cls.__instances.clear()  # ⭐ 关键！
```

### 3. 完整的生命周期

```
创建 → 使用 → 清理 → 遗忘
 ↓      ↓      ↓      ↓
new   run   close  clear
```

## 💡 如果仍有问题

### 调试方法

```python
# 在 RequestUtils.get_client() 中添加日志
@classmethod
def get_client(cls, url: str = "") -> HTTPClient:
    if url:
        _, domain, port = URLUtils.get_resolve_url(url)
        key = f"{domain}:{port}"
        if key not in cls.__clients:
            print(f"✨ 创建新客户端: {key}")
            cls.__clients[key] = HTTPClient()
        else:
            print(f"♻️  复用客户端: {key}")
        return cls.__clients[key]
    # ...
```

### 检查清单

- [ ] 确认 `close_all_async_clients()` 包含 `cls.__clients.clear()`
- [ ] 确认 `run_ani2openlist_async()` 的 `finally` 块调用了清理方法
- [ ] 确认 Docker 镜像已重新构建（`--no-cache`）
- [ ] 确认容器已重启（`down` 然后 `up`）

## 🚀 预期结果

执行此修复后，您应该看到：

```
时间              级别     消息
2025-10-14 13:15  INFO    开始执行任务...
2025-10-14 13:15  SUCCESS 任务执行完成
2025-10-14 13:16  INFO    开始执行任务...
2025-10-14 13:16  SUCCESS 任务执行完成  ← 第二次成功！
2025-10-14 13:17  INFO    开始执行任务...
2025-10-14 13:17  SUCCESS 任务执行完成  ← 第三次也成功！
```

**不再有任何错误！** ✅

---

**这次修复同时解决了两个问题：**
1. ✅ 关闭 HTTP 客户端（防止循环引用）
2. ✅ 清除缓存（防止复用已关闭的客户端）

**理论上这是最完美的解决方案！** 🎉
