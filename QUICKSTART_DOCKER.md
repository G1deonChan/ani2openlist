# 🚀 Docker 部署快速启动指南

欢迎使用 Ani2Openlist Docker 版本！按照以下步骤即可快速部署。

## 📋 前置检查清单

- [ ] 已安装 Docker（[下载 Docker](https://docs.docker.com/get-docker/)）
- [ ] 已注册 DockerHub 账号（[注册 DockerHub](https://hub.docker.com/signup)）
- [ ] 已创建 DockerHub Access Token
- [ ] 已配置 GitHub Secrets

## 🎯 三步完成部署

### 步骤 1: 配置 GitHub Secrets

1. 进入你的 GitHub 仓库
2. 点击 `Settings` → `Secrets and variables` → `Actions`
3. 添加两个 Secrets:
   - `DOCKERHUB_USERNAME`: 你的 DockerHub 用户名
   - `DOCKERHUB_TOKEN`: 你的 DockerHub Access Token

📖 详细说明: [docs/GITHUB_ACTIONS_DOCKER.md](docs/GITHUB_ACTIONS_DOCKER.md)

### 步骤 2: 更新文档中的用户名

将以下文件中的 `yourusername` 替换为你的 DockerHub 用户名:

```bash
# Windows PowerShell
$files = @(
    "README.md",
    "docs/DOCKER.md",
    "docs/GITHUB_ACTIONS_DOCKER.md",
    "docker-compose.yml"
)
foreach ($file in $files) {
    (Get-Content $file) -replace 'yourusername', '你的用户名' | Set-Content $file
}
```

或者手动编辑这些文件。

### 步骤 3: 创建 Release 触发构建

```bash
# 使用 GitHub CLI
gh release create v1.0.0 --title "Release v1.0.0" --notes "首个 Docker 版本发布"

# 或在 GitHub 网页上操作
# 仓库页面 → Releases → Create a new release
```

## ✅ 验证部署

### 1. 检查 GitHub Actions

进入 `Actions` 页面，查看 "Docker Build and Publish" 工作流是否成功。

### 2. 检查 DockerHub

访问 `https://hub.docker.com/r/你的用户名/ani2openlist`，确认镜像已发布。

### 3. 本地测试

```bash
# 拉取镜像
docker pull 你的用户名/ani2openlist:latest

# 准备配置文件
cp config.yaml.example config.yaml
# 编辑 config.yaml...

# 启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 访问 Web UI
# 浏览器打开: http://localhost:5000
```

## 🎉 完成！

现在你可以:
- 🌐 访问 Web UI: http://localhost:5000
- 📝 查看日志: `docker-compose logs -f`
- 🔄 更新镜像: `docker-compose pull && docker-compose up -d`
- 🛑 停止服务: `docker-compose down`

## 📚 更多文档

- [完整 Docker 部署指南](docs/DOCKER.md)
- [GitHub Actions 配置详解](docs/GITHUB_ACTIONS_DOCKER.md)
- [配置完成总结](DOCKER_SETUP_COMPLETE.md)

## 🆘 遇到问题？

1. 查看 [常见问题解答](docs/DOCKER.md#常见问题)
2. 在 [GitHub Issues](https://github.com/G1deonChan/ani2openlist/issues) 中提问
3. 查看工作流日志排查问题

---

**祝你使用愉快！** 🎊
