# Docker 部署指南

## 快速开始

### 使用 Docker Run

```bash
# 拉取最新镜像
docker pull yourusername/ani2openlist:latest

# 创建配置文件目录
mkdir -p config logs

# 复制配置文件示例
cp config.yaml.example config.yaml
# 编辑 config.yaml 填入你的配置

# 运行容器
docker run -d \
  --name ani2openlist \
  -p 5000:5000 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/logs:/app/logs \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  yourusername/ani2openlist:latest
```

### 使用 Docker Compose（推荐）

1. **创建配置文件**

```bash
# 复制配置文件示例
cp config.yaml.example config.yaml
cp webui/schedule.yaml.example webui/schedule.yaml

# 编辑配置文件
nano config.yaml
```

2. **启动服务**

```bash
# 设置你的 DockerHub 用户名（可选）
export DOCKERHUB_USERNAME=yourusername

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `TZ` | 时区设置 | `Asia/Shanghai` |
| `PYTHONUNBUFFERED` | Python 输出缓冲 | `1` |

### 卷挂载

| 容器路径 | 说明 | 必需 |
|----------|------|------|
| `/app/config.yaml` | 主配置文件 | 是 |
| `/app/webui/schedule.yaml` | 调度配置文件 | 可选 |
| `/app/logs` | 日志目录 | 推荐 |

### 端口映射

| 容器端口 | 说明 |
|----------|------|
| `5000` | Web UI 端口 |

## 镜像标签

- `latest` - 最新稳定版本
- `1.0.0` - 特定版本号

> 📝 **标签策略已优化**：每个 Release 只生成 2 个标签（`latest` 和完整版本号），减少标签数量，更清晰易用。  
> 如需了解其他标签策略或修改配置，请参考 [Docker 标签策略说明](DOCKER_TAGS.md)

## 健康检查

容器内置健康检查，会定期检查服务状态：

```bash
# 检查容器健康状态
docker ps

# 查看健康检查日志
docker inspect --format='{{json .State.Health}}' ani2openlist
```

## 常见问题

> 💡 **完整的故障排查指南**: 查看 [Docker 故障排查文档](DOCKER_TROUBLESHOOTING.md) 获取详细的问题解决方案。

### 1. 配置文件权限问题

```bash
# 确保配置文件有正确的权限
chmod 644 config.yaml
chmod 644 webui/schedule.yaml
```

### 2. 日志目录权限问题

```bash
# 创建日志目录并设置权限
mkdir -p logs
chmod 755 logs
```

### 3. 更新镜像

```bash
# 使用 docker run
docker pull yourusername/ani2openlist:latest
docker stop ani2openlist
docker rm ani2openlist
# 然后重新运行容器

# 使用 docker-compose
docker-compose pull
docker-compose up -d
```

### 4. 查看日志

```bash
# docker run
docker logs -f ani2openlist

# docker-compose
docker-compose logs -f
```

### 5. 进入容器

```bash
# docker run
docker exec -it ani2openlist /bin/bash

# docker-compose
docker-compose exec ani2openlist /bin/bash
```

## 自动构建

项目配置了 GitHub Actions，当创建 Release 时会自动：

1. 构建多架构 Docker 镜像（amd64, arm64, arm/v7）
2. 推送到 DockerHub
3. 更新 DockerHub 仓库描述

### 创建 Release 触发构建

```bash
# 在 GitHub 上创建 Release
# 或使用 gh CLI
gh release create v1.0.0 --title "Release v1.0.0" --notes "Release notes"
```

## 性能优化

### 资源限制

```yaml
# 在 docker-compose.yml 中调整资源限制
deploy:
  resources:
    limits:
      cpus: '2'      # 最大 CPU 核心数
      memory: 1G     # 最大内存
    reservations:
      cpus: '0.5'    # 预留 CPU
      memory: 512M   # 预留内存
```

### 多容器部署

如果需要运行多个实例：

```bash
docker-compose up -d --scale ani2openlist=3
```

## 安全建议

1. **不要在镜像中包含敏感配置**
   - 使用卷挂载外部配置文件
   - 或使用环境变量

2. **定期更新镜像**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

3. **使用非 root 用户**（后续优化）

4. **限制容器资源**
   - 设置 CPU 和内存限制
   - 防止资源耗尽

## 监控和维护

### 查看资源使用情况

```bash
# 实时资源使用
docker stats ani2openlist

# 详细信息
docker inspect ani2openlist
```

### 清理无用资源

```bash
# 清理无用镜像
docker image prune -a

# 清理无用卷
docker volume prune

# 清理整个系统（谨慎使用）
docker system prune -a --volumes
```

## 支持的架构

- linux/amd64
- linux/arm64
- linux/arm/v7

## 相关链接

- [DockerHub 仓库](https://hub.docker.com/r/yourusername/ani2openlist)
- [GitHub 仓库](https://github.com/yourusername/ani2openlist)
- [问题反馈](https://github.com/yourusername/ani2openlist/issues)
