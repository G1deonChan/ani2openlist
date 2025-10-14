# GitHub Actions Workflows

本目录包含项目的 GitHub Actions 工作流配置。

## 工作流列表

### 1. Python Tests (`python-tests.yml`)

**触发条件**:
- Push 到 `main` 或 `develop` 分支
- Pull Request 到 `main` 或 `develop` 分支

**功能**:
- 在多个操作系统上运行测试（Ubuntu, Windows, macOS）
- 测试多个 Python 版本（3.8, 3.9, 3.10, 3.11）
- 生成代码覆盖率报告
- 上传覆盖率到 Codecov

**状态**: ✅ 活跃

---

### 2. Docker Build and Publish (`docker-publish.yml`)

**触发条件**:
- 发布新的 Release
- 手动触发（workflow_dispatch）

**功能**:
- 构建多架构 Docker 镜像（amd64, arm64, arm/v7）
- 自动推送到 DockerHub
- 自动生成版本标签
- 更新 DockerHub 仓库描述

**所需 Secrets**:
- `DOCKERHUB_USERNAME` - DockerHub 用户名
- `DOCKERHUB_TOKEN` - DockerHub Access Token

**生成的标签**:
- `latest` - 最新稳定版（main 分支）
- `v1.2.3` - 完整版本号

> 📝 已优化标签策略，只生成必要的标签。详见 [Docker 标签策略说明](../../docs/DOCKER_TAGS.md)

**状态**: ✅ 活跃

---

## 配置 Secrets

### DockerHub Secrets

1. 进入仓库设置: `Settings` → `Secrets and variables` → `Actions`

2. 添加以下 Secrets:

   | Secret 名称 | 描述 | 获取方式 |
   |------------|------|---------|
   | `DOCKERHUB_USERNAME` | DockerHub 用户名 | 你的 DockerHub 账号用户名 |
   | `DOCKERHUB_TOKEN` | DockerHub Access Token | DockerHub → Account Settings → Security → New Access Token |

3. Token 权限: Read, Write, Delete

详细步骤见: [GitHub Actions Docker 配置指南](../docs/GITHUB_ACTIONS_DOCKER.md)

---

## 手动触发工作流

### Docker Build and Publish

1. 进入 Actions 页面
2. 选择 "Docker Build and Publish"
3. 点击 "Run workflow"
4. 选择分支
5. 点击绿色的 "Run workflow" 按钮

---

## 工作流状态查看

### 通过 GitHub CLI

```bash
# 查看所有工作流运行
gh run list

# 查看特定工作流
gh run list --workflow=docker-publish.yml

# 查看运行详情
gh run view <run-id>

# 查看日志
gh run view <run-id> --log
```

### 通过 Web

访问: `https://github.com/G1deonChan/ani2openlist/actions`

---

## Release 工作流

### 创建 Release 触发 Docker 构建

#### 方法 1: GitHub CLI

```bash
gh release create v1.0.0 \
  --title "Release v1.0.0" \
  --notes "Release notes here"
```

#### 方法 2: GitHub Web

1. 进入仓库主页
2. 点击右侧 "Releases"
3. 点击 "Create a new release"
4. 填写:
   - Tag: `v1.0.0`
   - Release title: `Release v1.0.0`
   - Description: 更新说明
5. 点击 "Publish release"

#### 方法 3: Git Tag

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

然后在 GitHub 上将 tag 转为 Release。

---

## 版本号规范

遵循语义化版本规范（Semantic Versioning）:

- **主版本号** (Major): 不兼容的 API 变更
- **次版本号** (Minor): 向后兼容的功能新增
- **修订号** (Patch): 向后兼容的问题修正

示例:
- `v1.0.0` - 首次正式发布
- `v1.1.0` - 添加新功能
- `v1.1.1` - 修复 bug
- `v2.0.0` - 重大更新

预发布版本:
- `v1.0.0-alpha.1` - Alpha 版本
- `v1.0.0-beta.1` - Beta 版本
- `v1.0.0-rc.1` - Release Candidate

---

## 故障排查

### Docker 构建失败

**问题**: Invalid username or password

**解决**:
1. 检查 `DOCKERHUB_USERNAME` Secret
2. 重新生成 `DOCKERHUB_TOKEN`
3. 确保 Token 有 Write 权限

**问题**: 多架构构建超时

**解决**:
1. 减少构建架构（移除 arm/v7）
2. 优化 Dockerfile 缓存
3. 检查 `.dockerignore`

### 测试失败

**问题**: Import errors

**解决**:
1. 检查 `requirements.txt`
2. 确保依赖版本兼容
3. 检查 Python 版本兼容性

---

## 工作流优化

### 缓存策略

Docker 构建使用 Registry 缓存:

```yaml
cache-from: type=registry,ref=username/ani2openlist:buildcache
cache-to: type=registry,ref=username/ani2openlist:buildcache,mode=max
```

这可以显著加速后续构建。

### 并行构建

测试工作流在多个平台和 Python 版本上并行运行，加快反馈速度。

---

## 添加新工作流

1. 在 `.github/workflows/` 创建新的 YAML 文件
2. 定义触发条件和步骤
3. 提交并推送
4. 在 Actions 页面查看

示例模板:

```yaml
name: My Workflow

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run script
        run: echo "Hello World"
```

---

## 相关文档

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [工作流语法](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Docker 配置指南](../docs/GITHUB_ACTIONS_DOCKER.md)
- [Docker 部署指南](../docs/DOCKER.md)

---

## 维护者

- [@G1deonChan](https://github.com/G1deonChan)

如有问题，请在 [Issues](https://github.com/G1deonChan/ani2openlist/issues) 中反馈。
