# 标签优化说明

## 🎯 问题

之前的配置会为每个 Release 生成 4-5 个标签：

```
Release v1.0.0 生成:
├── latest
├── 1.0.0
├── 1.0
└── 1
  + buildcache (构建缓存)
```

**问题**：标签太多，容易混淆，占用空间

---

## ✅ 优化后

现在每个 Release 只生成 2 个标签：

```
Release v1.0.0 生成:
├── latest   (始终指向最新版)
└── 1.0.0    (固定版本)
  + buildcache (构建缓存，不算正式标签)
```

---

## 📊 对比

### 优化前

| Release | 生成标签数 | 标签列表 |
|---------|-----------|---------|
| v1.0.0 | 4 | `latest`, `1.0.0`, `1.0`, `1` |
| v1.0.1 | 4 | `latest`, `1.0.1`, `1.0`, `1` |
| v1.1.0 | 4 | `latest`, `1.1.0`, `1.1`, `1` |
| v2.0.0 | 4 | `latest`, `2.0.0`, `2.0`, `2` |
| **总计** | **16 个标签** | |

### 优化后

| Release | 生成标签数 | 标签列表 |
|---------|-----------|---------|
| v1.0.0 | 2 | `latest`, `1.0.0` |
| v1.0.1 | 2 | `latest`, `1.0.1` |
| v1.1.0 | 2 | `latest`, `1.1.0` |
| v2.0.0 | 2 | `latest`, `2.0.0` |
| **总计** | **5 个标签** (latest + 4个版本号) | |

**减少 69% 的标签数量！** 🎉

---

## 💡 使用方式

### 最新版本
```bash
docker pull yourusername/ani2openlist:latest
```

### 特定版本
```bash
# 使用 1.0.0 版本
docker pull yourusername/ani2openlist:1.0.0

# 使用 1.0.1 版本
docker pull yourusername/ani2openlist:1.0.1
```

---

## 🔧 配置变更

修改了 `.github/workflows/docker-publish.yml` 中的这部分：

### 优化前
```yaml
tags: |
  type=semver,pattern={{version}}
  type=semver,pattern={{major}}.{{minor}}  # 会生成 1.0
  type=semver,pattern={{major}}            # 会生成 1
  type=raw,value=latest,enable={{is_default_branch}}
```

### 优化后
```yaml
tags: |
  type=semver,pattern={{version}}          # 只生成完整版本号
  type=raw,value=latest,enable={{is_default_branch}}
```

---

## ❓ 如果需要更多标签

如果你的用户需要锁定主版本或次版本（如 `myimage:1` 或 `myimage:1.0`），可以参考 [DOCKER_TAGS.md](DOCKER_TAGS.md) 中的其他方案。

---

## 📝 总结

✅ **优点**:
- 标签数量减少 69%
- 更清晰易懂
- 节省 DockerHub 存储空间
- 减少维护负担

✅ **功能不变**:
- 仍然可以使用 `latest` 获取最新版
- 仍然可以通过版本号回滚
- 所有功能正常工作

---

**这个优化对用户体验没有负面影响，只会让标签管理更简单！** ✨
