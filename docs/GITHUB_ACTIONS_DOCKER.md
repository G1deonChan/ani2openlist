# GitHub Actions Docker 自动构建配置指南

本项目已配置 GitHub Actions 自动构建和发布 Docker 镜像到 DockerHub。

## 前置要求

1. **DockerHub 账号**
   - 注册 DockerHub 账号：https://hub.docker.com/signup
   - 创建一个仓库或使用自动创建

2. **DockerHub Access Token**
   - 登录 DockerHub
   - 进入 Account Settings → Security
   - 点击 "New Access Token"
   - 输入描述（如 "GitHub Actions"）
   - 选择权限：Read, Write, Delete
   - 复制生成的 Token（只显示一次）

## 配置 GitHub Secrets

在 GitHub 仓库中配置以下 Secrets：

1. **进入仓库设置**
   ```
   GitHub 仓库 → Settings → Secrets and variables → Actions → New repository secret
   ```

2. **添加以下 Secrets**

   | Secret 名称 | 说明 | 示例值 |
   |------------|------|--------|
   | `DOCKERHUB_USERNAME` | DockerHub 用户名 | `yourusername` |
   | `DOCKERHUB_TOKEN` | DockerHub Access Token | `dckr_pat_xxxxx...` |

### 详细步骤

#### 1. 添加 DOCKERHUB_USERNAME

1. 点击 "New repository secret"
2. Name: `DOCKERHUB_USERNAME`
3. Value: 你的 DockerHub 用户名
4. 点击 "Add secret"

#### 2. 添加 DOCKERHUB_TOKEN

1. 点击 "New repository secret"
2. Name: `DOCKERHUB_TOKEN`
3. Value: 从 DockerHub 复制的 Access Token
4. 点击 "Add secret"

## 触发自动构建

### 方式 1: 创建 Release（推荐）

1. **通过 GitHub 网页**
   - 进入仓库主页
   - 点击右侧 "Releases" → "Create a new release"
   - 填写信息：
     - Tag: `v1.0.0`（遵循语义化版本）
     - Release title: `Release v1.0.0`
     - Description: 更新说明
   - 点击 "Publish release"

2. **使用 GitHub CLI**
   ```bash
   # 安装 gh CLI: https://cli.github.com/
   
   # 创建 Release
   gh release create v1.0.0 \
     --title "Release v1.0.0" \
     --notes "Release notes here"
   ```

3. **使用 Git 标签**
   ```bash
   # 创建标签
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   
   # 然后在 GitHub 上将标签转为 Release
   ```

### 方式 2: 手动触发

1. 进入仓库 Actions 页面
2. 选择 "Docker Build and Publish" workflow
3. 点击 "Run workflow"
4. 选择分支（默认 main）
5. 点击绿色的 "Run workflow" 按钮

## 生成的镜像标签

根据 Release 版本自动生成标签：

| Release 版本 | 生成的标签 |
|-------------|-----------|
| `v1.0.0` | `1.0.0`, `latest` |
| `v1.0.1` | `1.0.1`, `latest` |
| `v2.0.0` | `2.0.0`, `latest` |
| `v1.0.0-beta.1` | `1.0.0-beta.1` |

> 📝 标签策略已优化，只生成必要的标签。如需修改，请参考 [Docker 标签策略说明](DOCKER_TAGS.md)

## 构建架构

自动构建支持以下架构：
- `linux/amd64` (x86_64)
- `linux/arm64` (ARMv8)
- `linux/arm/v7` (ARMv7)

## 验证构建

### 1. 查看 Actions 日志

1. 进入仓库 Actions 页面
2. 选择最新的 workflow 运行
3. 查看详细日志

### 2. 检查 DockerHub

1. 登录 DockerHub
2. 查看仓库：`https://hub.docker.com/r/yourusername/ani2openlist`
3. 确认新标签已发布

### 3. 拉取并测试镜像

```bash
# 拉取最新镜像
docker pull yourusername/ani2openlist:latest

# 查看镜像信息
docker image inspect yourusername/ani2openlist:latest

# 测试运行
docker run --rm yourusername/ani2openlist:latest python --version
```

## 常见问题

### 1. 构建失败：Invalid username or password

**原因**: DockerHub 凭据配置错误

**解决方案**:
- 检查 `DOCKERHUB_USERNAME` 是否正确
- 重新生成 `DOCKERHUB_TOKEN`
- 确保 Token 有 Write 权限

### 2. 构建失败：Repository not found

**原因**: DockerHub 仓库不存在

**解决方案**:
- 首次推送会自动创建仓库（如果有权限）
- 或手动在 DockerHub 创建仓库

### 3. 推送超时

**原因**: 网络问题或镜像过大

**解决方案**:
- 检查 `.dockerignore` 文件
- 优化 Dockerfile 层缓存
- 重新触发 workflow

### 4. 多架构构建失败

**原因**: 某些依赖不支持特定架构

**解决方案**:
- 在 `.github/workflows/docker-publish.yml` 中移除不支持的架构
- 或在 Dockerfile 中添加架构判断

```yaml
# 只构建 amd64 和 arm64
platforms: linux/amd64,linux/arm64
```

## 工作流配置详解

### 触发条件

```yaml
on:
  release:
    types: [published]  # Release 发布时触发
  workflow_dispatch:    # 允许手动触发
```

### 构建步骤

1. **Checkout** - 检出代码
2. **QEMU** - 设置多架构模拟
3. **Buildx** - 设置 Docker Buildx
4. **Login** - 登录 DockerHub
5. **Metadata** - 提取版本标签
6. **Build & Push** - 构建并推送镜像
7. **Update Description** - 更新仓库描述

### 缓存优化

工作流使用 Registry 缓存加速构建：

```yaml
cache-from: type=registry,ref=username/ani2openlist:buildcache
cache-to: type=registry,ref=username/ani2openlist:buildcache,mode=max
```

## 最佳实践

### 1. 版本管理

遵循语义化版本规范（Semantic Versioning）：

- `v1.0.0` - 主要版本（不兼容的 API 变更）
- `v1.1.0` - 次要版本（向后兼容的功能新增）
- `v1.0.1` - 修订版本（向后兼容的问题修正）

### 2. Release 说明

提供详细的 Release Notes：

```markdown
## 新功能
- 添加 Docker 支持
- 新增 Web UI

## 改进
- 优化性能
- 改进日志

## 修复
- 修复配置读取问题

## 破坏性变更
- 配置文件格式变更
```

### 3. 测试

Release 前确保测试通过：

```bash
# 本地构建测试
docker build -t ani2openlist:test .

# 运行测试
docker run --rm ani2openlist:test python -m pytest

# 测试运行
docker run --rm -p 5000:5000 ani2openlist:test
```

### 4. 安全

- 定期更新 Access Token
- 使用最小权限原则
- 不要在代码中硬编码凭据

## 监控构建

### GitHub Actions

```bash
# 使用 GitHub CLI 查看工作流状态
gh run list --workflow=docker-publish.yml

# 查看最新运行日志
gh run view --log
```

### DockerHub Webhooks（可选）

配置 Webhook 接收推送通知：

1. DockerHub 仓库 → Webhooks
2. 添加 Webhook URL
3. 接收构建通知

## 自定义配置

### 修改镜像名称

编辑 `.github/workflows/docker-publish.yml`:

```yaml
env:
  IMAGE_NAME: your-custom-name  # 修改这里
```

### 修改触发条件

```yaml
on:
  release:
    types: [published, prereleased]  # 包括预发布
  push:
    tags:
      - 'v*'  # 推送 v* 标签时触发
```

### 修改支持架构

```yaml
platforms: linux/amd64  # 只构建 amd64
```

## 相关链接

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [DockerHub Access Tokens](https://docs.docker.com/docker-hub/access-tokens/)
- [语义化版本](https://semver.org/lang/zh-CN/)

## 支持

如有问题，请在 [GitHub Issues](https://github.com/yourusername/ani2openlist/issues) 中提问。
