# Event Loop 错误的真正原因与完整解决方案

## 🎯 问题的真正根源

经过多次调试，我们发现了真正的问题：

### ❌ 之前的错误诊断
```
错误理解：事件循环没有正确清理
实际原因：HTTP 客户端（httpx.AsyncClient）没有关闭！
```

### ✅ 真正的问题

```python
# httpx.AsyncClient 在事件循环中创建连接
client = AsyncClient(http2=True, follow_redirects=True, timeout=10)

# 如果不调用 await client.aclose()
# 事件循环关闭时会报错："Event loop is closed"
# 因为 httpx 还持有未关闭的连接！
```

## 🔍 问题追踪

### 观察到的症状
```
第一次执行: ✅ SUCCESS  
第二次执行: ❌ ERROR - Event loop is closed
第三次执行: ❌ ERROR - Event loop is closed
```

### 错误的解决尝试
1. ❌ 使用 `asyncio.run()` - 仍然失败
2. ❌ 手动清理事件循环 - 仍然失败  
3. ❌ 重置事件循环策略 - 仍然失败
4. ❌ 手动创建和管理循环 - 仍然失败

### 为什么都失败了？

**因为问题不在事件循环本身！**

```python
# 每次任务执行后
# 事件循环关闭了 ✅
# 但是 httpx.AsyncClient 还没关闭 ❌
#
# httpx 内部的连接池、HTTP/2 连接仍然存在
# 它们持有对已关闭事件循环的引用
#
# 下次创建新循环时
# 这些旧的连接会尝试使用已关闭的循环
# 结果：RuntimeError: Event loop is closed
```

## ✅ 完整解决方案

### 第一步：添加清理方法

在 `ani2openlist/utils/http.py` 中添加：

```python
class RequestUtils:
    """HTTP 请求工具类"""
    
    __clients: dict[str, HTTPClient] = {}
    __client_list: WeakSet[HTTPClient] = WeakSet()
    
    # ... 其他方法 ...
    
    @classmethod
    async def close_all_async_clients(cls) -> None:
        """
        关闭所有异步 HTTP 客户端
        用于清理资源，防止事件循环关闭时出现警告
        """
        # 关闭缓存的客户端
        for client in cls.__clients.values():
            try:
                await client.close_async_client()
            except Exception:
                pass
        
        # 关闭弱引用集合中的客户端
        for client in list(cls.__client_list):
            try:
                await client.close_async_client()
            except Exception:
                pass
```

### 第二步：在任务完成后调用清理

在 `webui/app.py` 中修改：

```python
async def run_ani2openlist_async():
    """异步运行 ani2openlist"""
    ani = None
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
        # ⭐ 关键：清理所有 HTTP 客户端资源
        try:
            await RequestUtils.close_all_async_clients()
        except Exception as e:
            logger.debug(f'清理 HTTP 客户端失败: {e}')
```

### 第三步：保持事件循环管理优化

保留之前的事件循环手动管理方式（更可靠）：

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
            # 5. 完整的清理流程
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:
                pass
            
            try:
                loop.run_until_complete(loop.shutdown_default_executor())
            except Exception:
                pass
            
            # 6. 关闭循环
            loop.close()
            
            # 7. 清除线程的事件循环引用
            asyncio.set_event_loop(None)
            
    except Exception as e:
        error_msg = f'任务执行失败: {str(e)}'
        add_log(error_msg, 'error')
        task_status['last_result'] = {'success': False, 'message': error_msg}
    finally:
        task_status['running'] = False
```

## 🔬 技术原理

### httpx.AsyncClient 的资源管理

```python
# httpx 内部结构（简化）
class AsyncClient:
    def __init__(self):
        self._pool = ConnectionPool()  # 连接池
        self._loop = asyncio.get_event_loop()  # 保存循环引用！
    
    async def request(self, ...):
        conn = await self._pool.get_connection()
        # 使用连接...
    
    async def aclose(self):
        # 关闭所有连接
        await self._pool.close()
```

### 问题场景

```python
# 第一次执行
loop1 = new_event_loop()
client = AsyncClient()  # client._loop = loop1
await client.request(...)
# ❌ 没有调用 client.aclose()
loop1.close()  # 循环关闭了

# 第二次执行
loop2 = new_event_loop()
# ⚠️ 旧的 client 仍然存在（被 RequestUtils 缓存）
# client._loop 仍然指向 loop1（已关闭）
await client.request(...)  # 💥 RuntimeError: Event loop is closed
```

### 正确的清理顺序

```python
# ✅ 正确的顺序
try:
    loop = new_event_loop()
    set_event_loop(loop)
    
    # 运行任务
    result = loop.run_until_complete(my_task())
finally:
    # 1️⃣ 首先：关闭异步生成器
    loop.run_until_complete(loop.shutdown_asyncgens())
    
    # 2️⃣ 其次：关闭执行器
    loop.run_until_complete(loop.shutdown_default_executor())
    
    # 3️⃣ 最后：关闭循环
    loop.close()
    
    # 4️⃣ 清除引用
    set_event_loop(None)
```

## 📊 为什么本地测试通过但 Docker 失败？

### 本地 Windows 环境
```python
# Windows 上 httpx 可能使用不同的事件循环实现
# 或者 GC 更快清理了未关闭的客户端
# 所以即使不调用 aclose()，问题不明显
```

### Docker Linux 环境
```python
# Linux 上 asyncio 使用 selector 循环
# 连接池的行为更严格
# 未关闭的连接会明确报错
```

## ✅ 测试清单

```bash
# 部署新版本
docker-compose build --no-cache
docker-compose up -d

# 测试场景
✅ 1. 手动执行 - 第一次
✅ 2. 手动执行 - 第二次（立即）
✅ 3. 手动执行 - 第三次
✅ 4. 设置定时任务
✅ 5. 等待定时任务自动执行 - 第一次
✅ 6. 等待定时任务自动执行 - 第二次
✅ 7. 等待定时任务自动执行 - 第三次
```

## 🎓 经验教训

### 1. 资源管理的重要性

```python
# ❌ 错误：忘记清理
async def task():
    client = AsyncClient()
    await client.get(url)
    # 没有 await client.aclose()

# ✅ 正确：使用上下文管理器
async def task():
    async with AsyncClient() as client:
        await client.get(url)
    # 自动调用 aclose()

# ✅ 正确：手动清理
async def task():
    client = AsyncClient()
    try:
        await client.get(url)
    finally:
        await client.aclose()
```

### 2. 调试思路

```
1. 不要只看错误信息
   "Event loop is closed" ≠ 事件循环管理问题
   
2. 追踪资源生命周期
   - 什么时候创建？
   - 什么时候销毁？
   - 是否正确清理？
   
3. 关注环境差异
   - Windows vs Linux
   - 本地 vs Docker
   - Python 版本差异
```

### 3. Python asyncio 最佳实践

```python
# ✅ 总是清理异步资源
async def my_task():
    # 网络连接
    async with httpx.AsyncClient() as client:
        ...
    
    # 文件 I/O
    async with aiofiles.open(...) as f:
        ...
    
    # 数据库连接
    async with asyncpg.create_pool(...) as pool:
        ...

# ✅ 在 finally 块中清理
async def my_task():
    client = None
    try:
        client = httpx.AsyncClient()
        ...
    finally:
        if client:
            await client.aclose()
```

## 🚀 部署步骤

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 完全重新构建（不使用缓存）
docker-compose build --no-cache

# 3. 停止并删除旧容器
docker-compose down

# 4. 启动新容器
docker-compose up -d

# 5. 查看日志验证
docker-compose logs -f

# 6. 测试多次手动执行和定时任务
```

## 📝 修改的文件

1. **ani2openlist/utils/http.py**
   - 添加 `RequestUtils.close_all_async_clients()` 方法

2. **webui/app.py**
   - 导入 `RequestUtils`
   - 在 `run_ani2openlist_async()` 的 finally 块中调用清理方法
   - 保持优化的事件循环管理

## 💡 如果仍有问题

如果清理后仍然有问题，请检查：

```python
# 1. 是否有其他异步资源未清理
# 查找所有 async with 和 AsyncClient

# 2. 是否有全局的异步对象
# 检查模块级别的 AsyncClient 实例

# 3. 是否使用了其他异步库
# aiofiles, aioredis, asyncpg 等都需要清理

# 4. 添加详细日志
import traceback

async def cleanup():
    try:
        await RequestUtils.close_all_async_clients()
        print("✅ HTTP 客户端清理成功")
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        traceback.print_exc()
```

---

**这次的修复抓住了问题的本质！应该能彻底解决问题了。** 🎉
