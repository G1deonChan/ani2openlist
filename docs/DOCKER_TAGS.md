# Docker 标签策略说明

## 当前配置（已优化）

当前配置只会生成 **2 个标签**：

| 标签 | 说明 | 示例 |
|------|------|------|
| `latest` | 最新稳定版本 | `latest` |
| `{{version}}` | 完整版本号 | `1.0.0` |

### 优点
- ✅ 标签数量最少，清晰明了
- ✅ `latest` 始终指向最新稳定版
- ✅ 可以通过完整版本号回滚到任意版本
- ✅ 减少 DockerHub 存储空间

### 使用方式

```bash
# 使用最新版本
docker pull yourusername/ani2openlist:latest

# 使用特定版本
docker pull yourusername/ani2openlist:1.0.0
```

---

## 其他可选策略

### 方案 2: 添加主次版本号（原配置）

生成 **4 个标签**：

```yaml
tags: |
  type=semver,pattern={{version}}      # 1.0.0
  type=semver,pattern={{major}}.{{minor}}  # 1.0
  type=semver,pattern={{major}}        # 1
  type=raw,value=latest,enable={{is_default_branch}}  # latest
```

**优点**: 可以锁定主版本或次版本
**缺点**: 标签较多

**使用场景**:
```bash
# 始终使用 v1.x.x 的最新版本
docker pull yourusername/ani2openlist:1

# 始终使用 v1.0.x 的最新版本
docker pull yourusername/ani2openlist:1.0

# 使用特定版本
docker pull yourusername/ani2openlist:1.0.0
```

### 方案 3: 只保留 latest

生成 **1 个标签**：

```yaml
tags: |
  type=raw,value=latest,enable={{is_default_branch}}
```

**优点**: 最简单
**缺点**: 无法回滚到旧版本

### 方案 4: 添加开发分支标签

```yaml
tags: |
  type=semver,pattern={{version}}
  type=raw,value=latest,enable={{is_default_branch}}
  type=ref,event=branch  # 分支名作为标签
  type=ref,event=pr      # PR 编号作为标签
```

**适用于**: 需要测试开发版本的场景

---

## 标签说明

### buildcache 标签

`buildcache` 是构建缓存标签，用于加速后续构建：

```yaml
cache-from: type=registry,ref=${{ secrets.DOCKERHUB_USERNAME }}/${{ env.IMAGE_NAME }}:buildcache
cache-to: type=registry,ref=${{ secrets.DOCKERHUB_USERNAME }}/${{ env.IMAGE_NAME }}:buildcache,mode=max
```

**不会在 DockerHub 页面显示为正式镜像**，但会占用一定空间。

如果想移除缓存功能，可以删除这两行配置，但会导致每次构建都从头开始。

---

## 版本号规范

遵循语义化版本（Semantic Versioning）:

```
v主版本号.次版本号.修订号
```

### 何时更新版本号

- **主版本号** (Major): 不兼容的 API 变更
  - 例: `v1.0.0` → `v2.0.0`
  
- **次版本号** (Minor): 向后兼容的功能新增
  - 例: `v1.0.0` → `v1.1.0`
  
- **修订号** (Patch): 向后兼容的问题修正
  - 例: `v1.0.0` → `v1.0.1`

### 预发布版本

```
v1.0.0-alpha.1  # Alpha 测试版
v1.0.0-beta.1   # Beta 测试版
v1.0.0-rc.1     # Release Candidate
```

预发布版本不会更新 `latest` 标签。

---

## 如何修改标签策略

编辑 `.github/workflows/docker-publish.yml` 文件：

```yaml
- name: Extract metadata (tags, labels) for Docker
  id: meta
  uses: docker/metadata-action@v5
  with:
    images: ${{ secrets.DOCKERHUB_USERNAME }}/${{ env.IMAGE_NAME }}
    tags: |
      # 在这里修改标签规则
      type=semver,pattern={{version}}
      type=raw,value=latest,enable={{is_default_branch}}
```

---

## 清理旧标签

如果 DockerHub 上有太多不需要的标签，可以：

### 方法 1: 在 DockerHub 网页删除

1. 登录 DockerHub
2. 进入仓库页面
3. 点击 `Tags` 标签页
4. 选择要删除的标签
5. 点击删除按钮

### 方法 2: 使用 Docker Hub API

```bash
# 需要先登录获取 token
TOKEN=$(curl -s -H "Content-Type: application/json" -X POST \
  -d '{"username": "your-username", "password": "your-password"}' \
  https://hub.docker.com/v2/users/login/ | jq -r .token)

# 删除指定标签
curl -X DELETE \
  -H "Authorization: JWT ${TOKEN}" \
  https://hub.docker.com/v2/repositories/your-username/ani2openlist/tags/1/
```

### 方法 3: 使用 Docker Hub CLI

```bash
# 安装 hub-tool
https://github.com/docker/hub-tool

# 删除标签
docker hub tag rm your-username/ani2openlist:1
```

---

## 建议

对于大多数项目，推荐使用**当前配置**（只保留 `latest` 和完整版本号）：

✅ **优点**:
- 标签清晰明了
- 减少维护负担
- 节省存储空间
- 满足绝大多数使用场景

如果你需要用户能够锁定主版本或次版本（例如 `myimage:1` 或 `myimage:1.0`），可以改用方案 2。

---

## 当前配置生成的标签示例

假设你创建了以下 Releases：

| Release | 生成的标签 |
|---------|-----------|
| v1.0.0 | `1.0.0`, `latest` |
| v1.0.1 | `1.0.1`, `latest` |
| v1.1.0 | `1.1.0`, `latest` |
| v2.0.0 | `2.0.0`, `latest` |

每次只有 2 个新标签，`latest` 会自动更新为最新版本。

---

**需要修改标签策略吗？** 只需编辑 `.github/workflows/docker-publish.yml` 文件即可！
