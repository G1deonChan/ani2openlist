# Git 提交指南

## 提交更改

所有 Docker 支持相关的文件已准备就绪。按照以下步骤提交更改：

### 1. 查看更改

```bash
git status
```

### 2. 添加文件

```bash
# 添加所有更改
git add .

# 或分别添加
git add .dockerignore
git add .gitignore
git add Dockerfile
git add docker-compose.yml
git add README.md
git add webui/app.py
git add .github/workflows/docker-publish.yml
git add .github/workflows/README.md
git add docs/DOCKER.md
git add docs/GITHUB_ACTIONS_DOCKER.md
git add DOCKER_SETUP_COMPLETE.md
git add QUICKSTART_DOCKER.md
```

### 3. 提交更改

```bash
git commit -m "feat: 添加 Docker 支持和 GitHub Actions 自动构建

- 添加 Dockerfile 和 docker-compose.yml 配置
- 配置 GitHub Actions 自动构建多架构 Docker 镜像
- Release 时自动推送镜像到 DockerHub
- 添加健康检查端点 /health
- 完善 Docker 部署文档
- 更新 README 添加 Docker 使用说明
- 优化 .dockerignore 和 .gitignore

支持架构: linux/amd64, linux/arm64, linux/arm/v7
"
```

### 4. 推送到 GitHub

```bash
git push origin main
```

### 5. 配置 GitHub Secrets

在推送后，立即配置 GitHub Secrets:

1. 进入仓库设置: `Settings` → `Secrets and variables` → `Actions`
2. 添加:
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_TOKEN`

### 6. 创建首个 Release

```bash
# 确保所有更改已提交并推送

# 创建 Release
gh release create v1.0.0 \
  --title "Release v1.0.0 - Docker 支持" \
  --notes "## 新功能

- ✨ 添加 Docker 容器支持
- 🚀 GitHub Actions 自动构建多架构镜像
- 📦 自动推送到 DockerHub
- 🏥 添加健康检查端点
- 📚 完善文档

## Docker 使用

\`\`\`bash
# 使用 Docker Compose
docker-compose up -d

# 或使用 Docker Run
docker run -d \\
  --name ani2openlist \\
  -p 5000:5000 \\
  -v \$(pwd)/config.yaml:/app/config.yaml \\
  -v \$(pwd)/logs:/app/logs \\
  yourusername/ani2openlist:latest
\`\`\`

## 支持的架构

- linux/amd64
- linux/arm64
- linux/arm/v7

## 文档

- [Docker 部署指南](docs/DOCKER.md)
- [GitHub Actions 配置](docs/GITHUB_ACTIONS_DOCKER.md)
- [快速启动](QUICKSTART_DOCKER.md)
"
```

## 提交信息规范

本次提交使用了 [约定式提交](https://www.conventionalcommits.org/zh-hans/) 规范:

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具更新

## 验证清单

提交前确认:

- [ ] 所有文件已添加到 git
- [ ] 提交信息清晰明确
- [ ] 代码没有语法错误
- [ ] 文档链接正确
- [ ] 配置文件示例完整

提交后确认:

- [ ] GitHub Secrets 已配置
- [ ] DockerHub Access Token 有效
- [ ] 用户名已在文档中更新
- [ ] Release 创建成功
- [ ] GitHub Actions 工作流运行成功
- [ ] Docker 镜像已推送到 DockerHub

## 回滚更改（如需要）

如果需要撤销这些更改:

```bash
# 查看提交历史
git log --oneline

# 回滚到之前的提交
git reset --hard <commit-hash>

# 强制推送（谨慎使用）
git push -f origin main
```

## 下一步

1. ✅ 提交代码
2. ✅ 推送到 GitHub
3. ✅ 配置 Secrets
4. ✅ 创建 Release
5. ⏳ 等待自动构建完成
6. ✅ 验证 DockerHub 镜像
7. ✅ 测试拉取和运行镜像
8. 🎉 完成！

---

**准备好了吗？** 执行上述命令开始吧！ 🚀
