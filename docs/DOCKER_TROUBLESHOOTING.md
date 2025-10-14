# Docker 故障排查指南

## 常见错误及解决方案

### 1. TypeError: unsupported operand type(s) for |: 'type' and 'type'

**错误信息**:
```
File "/app/ani2openlist/core/logger.py", line 22, in <module>
    log_file: str | Path | None = None,
TypeError: unsupported operand type(s) for |: 'type' and 'type'
```

**原因**: 
- Python 版本不兼容
- `str | Path | None` 语法只在 Python 3.10+ 中支持
- 旧版 Dockerfile 使用的是 Python 3.9

**解决方案**: 
✅ **已修复** - Dockerfile 已更新为 Python 3.10

**验证修复**:
```bash
# 重新构建镜像
docker build -t ani2openlist:test .

# 运行测试
docker run --rm ani2openlist:test python --version
# 应该输出: Python 3.10.x
```

---

### 2. 配置文件未找到

**错误信息**:
```
FileNotFoundError: [Errno 2] No such file or directory: '/app/config.yaml'
```

**解决方案**:
```bash
# 确保挂载了配置文件
docker run -d \
  --name ani2openlist \
  -p 5000:5000 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  yourusername/ani2openlist:latest
```

---

### 3. 权限问题

**错误信息**:
```
PermissionError: [Errno 13] Permission denied: '/app/logs'
```

**解决方案**:
```bash
# 创建日志目录并设置权限
mkdir -p logs
chmod 755 logs

# 或在 docker-compose.yml 中添加用户映射
user: "${UID}:${GID}"
```

---

### 4. 端口已被占用

**错误信息**:
```
Error starting userland proxy: listen tcp4 0.0.0.0:5000: bind: address already in use
```

**解决方案**:
```bash
# 方案 1: 使用其他端口
docker run -d -p 5001:5000 ...

# 方案 2: 停止占用端口的服务
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

---

### 5. 健康检查失败

**错误信息**:
```
Health check failed
```

**排查步骤**:
```bash
# 1. 查看容器日志
docker logs ani2openlist

# 2. 进入容器检查
docker exec -it ani2openlist /bin/bash
curl http://localhost:5000/health

# 3. 检查配置文件
docker exec ani2openlist cat /app/config.yaml

# 4. 检查 Python 进程
docker exec ani2openlist ps aux | grep python
```

---

### 6. 依赖包安装失败

**错误信息**:
```
ERROR: Could not find a version that satisfies the requirement ...
```

**解决方案**:
```bash
# 清理 Docker 缓存重新构建
docker build --no-cache -t ani2openlist:test .
```

---

### 7. 网络连接问题

**错误信息**:
```
httpx.ConnectError: [Errno 111] Connection refused
```

**解决方案**:
```bash
# 检查容器网络
docker network ls
docker network inspect bridge

# 使用 host 网络模式（Linux）
docker run --network host ...

# 检查防火墙设置
# Windows: 检查 Windows Defender 防火墙
# Linux: 检查 iptables 或 firewalld
```

---

### 8. 内存不足

**错误信息**:
```
MemoryError
```

**解决方案**:
```bash
# 增加内存限制
docker run -m 1g --memory-swap 2g ...

# 或在 docker-compose.yml 中配置
deploy:
  resources:
    limits:
      memory: 1G
```

---

## 调试技巧

### 1. 查看详细日志

```bash
# 实时查看日志
docker logs -f ani2openlist

# 查看最近 100 行
docker logs --tail 100 ani2openlist

# 显示时间戳
docker logs -t ani2openlist
```

### 2. 进入容器调试

```bash
# 使用 bash
docker exec -it ani2openlist /bin/bash

# 使用 sh（如果 bash 不可用）
docker exec -it ani2openlist /bin/sh

# 执行单个命令
docker exec ani2openlist python --version
docker exec ani2openlist pip list
```

### 3. 检查容器状态

```bash
# 查看容器详情
docker inspect ani2openlist

# 查看资源使用
docker stats ani2openlist

# 查看端口映射
docker port ani2openlist

# 查看挂载卷
docker inspect -f '{{ .Mounts }}' ani2openlist
```

### 4. 测试网络连接

```bash
# 从容器内测试
docker exec ani2openlist curl -I http://localhost:5000/health

# 从宿主机测试
curl -I http://localhost:5000/health

# 测试 DNS
docker exec ani2openlist nslookup google.com
```

### 5. 重建容器

```bash
# 停止并删除容器
docker stop ani2openlist
docker rm ani2openlist

# 删除镜像
docker rmi yourusername/ani2openlist:latest

# 重新拉取
docker pull yourusername/ani2openlist:latest

# 重新启动
docker-compose up -d
```

---

## 完全清理

如果需要完全清理并重新开始：

```bash
# 停止所有容器
docker stop $(docker ps -aq)

# 删除所有容器
docker rm $(docker ps -aq)

# 删除所有镜像
docker rmi $(docker images -q)

# 清理构建缓存
docker builder prune -a

# 清理卷和网络
docker volume prune
docker network prune

# 或一次性清理所有（谨慎使用）
docker system prune -a --volumes
```

---

## 获取帮助

如果以上方案都无法解决问题：

1. **收集信息**:
   ```bash
   # Docker 版本
   docker --version
   docker-compose --version
   
   # 系统信息
   uname -a  # Linux/Mac
   systeminfo  # Windows
   
   # 容器日志
   docker logs ani2openlist > container.log 2>&1
   
   # 构建日志
   docker build -t ani2openlist:test . 2>&1 | tee build.log
   ```

2. **在 GitHub 创建 Issue**:
   - 提供错误信息
   - 附上日志文件
   - 说明操作系统和 Docker 版本
   - 描述复现步骤

3. **相关链接**:
   - [GitHub Issues](https://github.com/G1deonChan/ani2openlist/issues)
   - [Docker 文档](https://docs.docker.com/)
   - [Docker Compose 文档](https://docs.docker.com/compose/)

---

## 性能优化

### 减少镜像大小

```dockerfile
# 使用多阶段构建
FROM python:3.10-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
```

### 加速构建

```bash
# 使用国内镜像源
docker build --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple -t ani2openlist:test .

# 使用 BuildKit
DOCKER_BUILDKIT=1 docker build -t ani2openlist:test .
```

---

**记得定期更新镜像以获取最新修复！** 🔄
