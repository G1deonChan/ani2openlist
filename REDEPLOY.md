# 🚀 快速重新部署指南

## 修复内容

解决了 "Event loop is closed" 和 "Client has been closed" 两个错误。

### 核心改进

1. ✅ **关闭 HTTP 客户端** - 防止事件循环引用
2. ✅ **清除 HTTP 客户端缓存** - 防止复用已关闭的客户端
3. ✅ **清除 Multiton 实例缓存** - 防止复用持有已关闭资源的实例 ⭐ 关键！
4. ✅ **优化事件循环管理** - 使用 `policy.new_event_loop()` 而非 `asyncio.run()`

## 部署步骤

### 在服务器上执行

```bash
# 1. 停止并删除旧容器
docker-compose down

# 2. 拉取最新代码（如果有 Git 仓库）
git pull origin main

# 或者手动上传修改的文件：
# - ani2openlist/utils/http.py
# - webui/app.py

# 3. 完全重新构建镜像（不使用缓存）
docker-compose build --no-cache

# 4. 启动新容器
docker-compose up -d

# 5. 查看日志验证
docker-compose logs -f
```

### 在本地测试（可选）

```powershell
# Windows PowerShell
cd d:\Documents\github\ani2openlist

# 重新构建
docker-compose build --no-cache

# 重启
docker-compose down
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 测试清单

打开 Web UI (http://你的IP:5000) 并测试：

- [ ] 手动执行第 1 次 → 应该 **SUCCESS**
- [ ] 手动执行第 2 次 → 应该 **SUCCESS** ✨
- [ ] 手动执行第 3 次 → 应该 **SUCCESS** ✨
- [ ] 设置定时任务（2 分钟后）
- [ ] 等待定时任务第 1 次执行 → 应该 **SUCCESS**
- [ ] 等待定时任务第 2 次执行 → 应该 **SUCCESS** ✨
- [ ] 在定时任务期间手动执行 → 应该 **SUCCESS** ✨

## 预期结果

### ✅ 修复后的正常日志

```
时间              级别     消息
13:15:00         INFO    开始执行任务...
13:15:02         SUCCESS 任务执行完成
13:16:00         INFO    开始执行任务...
13:16:02         SUCCESS 任务执行完成  ← 第二次成功！
13:17:00         INFO    开始执行任务...
13:17:02         SUCCESS 任务执行完成  ← 持续成功！
```

### ❌ 修复前的错误日志（不应再出现）

```
13:15:00  ERROR  Event loop is closed
13:16:00  ERROR  Cannot send a request, as the client has been closed
```

## 如果遇到问题

### 问题 1: 仍然报 "Event loop is closed"

**原因**: Docker 镜像没有重新构建

**解决**:
```bash
docker-compose down
docker-compose build --no-cache  # 必须使用 --no-cache
docker-compose up -d
```

### 问题 2: 仍然报 "Client has been closed"

**原因**: 代码没有正确更新

**检查**:
1. 确认 `ani2openlist/utils/http.py` 中有 `cls.__clients.clear()`
2. 确认 `webui/app.py` 中 `finally` 块调用了 `await RequestUtils.close_all_async_clients()`

### 问题 3: 其他错误

**调试步骤**:
```bash
# 查看完整日志
docker-compose logs --tail=100

# 进入容器检查
docker-compose exec ani2openlist bash

# 检查 Python 版本
python --version  # 应该是 3.10+

# 检查文件是否存在
ls -la /app/ani2openlist/utils/http.py
ls -la /app/webui/app.py
```

## 修改的文件

如果手动更新，需要修改这三个文件：

1. **ani2openlist/utils/multiton.py** ⭐ 重要
   - 添加了 `clear_instances()` 类方法

2. **ani2openlist/utils/http.py**
   - 在 `close_all_async_clients()` 方法中添加了 `cls.__clients.clear()`

3. **webui/app.py**
   - 导入了 `RequestUtils`、`logger` 和 `Multiton`
   - 在 `run_ani2openlist_async()` 的 `finally` 块中调用 `Multiton.clear_instances()`

## 技术细节

### 为什么要清除两层缓存？

```python
# 第 1 层：RequestUtils 缓存 HTTPClient
__clients: dict[str, HTTPClient] = {}

# 第 2 层：Multiton 缓存 OpenlistClient（持有 HTTPClient）
_instances: dict = {}

# 第一次任务后：
await client.aclose()  # 关闭 HTTPClient
# ❌ 但两个缓存都还在！

# 第二次任务（只清除第 1 层）：
RequestUtils.__clients.clear()  # ✅ 清除了
# ❌ 但 Multiton._instances 还缓存着 OpenlistClient
# ❌ OpenlistClient 内部的 self.__client 指向已关闭的 HTTPClient
await client.request()  # 💥 ERROR: Client has been closed

# 修复：清除两层缓存
await client.aclose()
RequestUtils.__clients.clear()  # 清除第 1 层
Multiton.clear_instances()      # ⭐ 清除第 2 层

# 第二次任务：
# OpenlistClient 从头创建
# HTTPClient 从头创建
await client.request()  # ✅ SUCCESS
```

## 验证成功的标志

连续执行 3-5 次任务，所有都显示 **SUCCESS**，没有任何 ERROR。

---

**准备好了！现在可以重新部署了！** 🎉
