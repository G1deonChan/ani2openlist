# 迁移指南：使用配置文件

本指南将帮助你将现有的 ani2openlist 代码迁移到使用配置文件的方式。

## 为什么要使用配置文件？

使用配置文件有以下优势：

1. **分离配置和代码**：配置更改不需要修改代码
2. **安全性更好**：敏感信息（密码、Token）不会暴露在代码中
3. **易于管理**：一个文件管理所有配置
4. **环境切换方便**：开发、测试、生产环境使用不同配置文件
5. **版本控制友好**：配置文件可以被 `.gitignore` 排除

## 迁移步骤

### 步骤 1: 创建配置文件

复制配置文件模板：

```bash
cp config.yaml.example config.yaml
```

### 步骤 2: 填写配置

编辑 `config.yaml` 文件，填入你的配置：

**旧的代码方式：**
```python
ani = Ani2Openlist(
    url="http://192.168.1.100:5244",
    username="admin",
    password="my_password",
    target_dir="/Anime",
    rss_update=True,
    src_domain="aniopen.an-i.workers.dev",
    rss_domain="api.ani.rip"
)
```

**对应的配置文件：**
```yaml
openlist:
  url: "http://192.168.1.100:5244"
  username: "admin"
  password: "my_password"
  target_dir: "/Anime"

ani:
  rss_update: true
  src_domain: "aniopen.an-i.workers.dev"
  rss_domain: "api.ani.rip"

logging:
  level: "INFO"
```

### 步骤 3: 更新代码

**旧的代码：**
```python
import asyncio
from ani2openlist import Ani2Openlist

async def main():
    ani = Ani2Openlist(
        url="http://192.168.1.100:5244",
        username="admin",
        password="my_password",
        target_dir="/Anime",
        rss_update=True
    )
    await ani.run()

if __name__ == "__main__":
    asyncio.run(main())
```

**新的代码：**
```python
import asyncio
from ani2openlist import Ani2Openlist, load_config

async def main():
    # 加载配置文件
    config = load_config("config.yaml")
    
    # 使用配置创建实例
    ani = Ani2Openlist(config=config)
    
    # 运行
    await ani.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## 迁移示例

### 示例 1: 基本使用

**旧代码：**
```python
from ani2openlist import Ani2Openlist

ani = Ani2Openlist(
    url="http://localhost:5244",
    token="your-token",
    target_dir="/Anime"
)
```

**新代码：**
```python
from ani2openlist import Ani2Openlist, load_config

config = load_config("config.yaml")
ani = Ani2Openlist(config=config)
```

**config.yaml：**
```yaml
openlist:
  url: "http://localhost:5244"
  token: "your-token"
  target_dir: "/Anime"
```

### 示例 2: 按季度获取

**旧代码：**
```python
ani = Ani2Openlist(
    url="http://localhost:5244",
    username="admin",
    password="password",
    target_dir="/Anime",
    rss_update=False,
    year=2024,
    month=10
)
```

**新代码：**
```python
config = load_config("config.yaml")
ani = Ani2Openlist(config=config)
```

**config.yaml：**
```yaml
openlist:
  url: "http://localhost:5244"
  username: "admin"
  password: "password"
  target_dir: "/Anime"

ani:
  rss_update: false
  year: 2024
  month: 10
```

### 示例 3: 混合使用（代码覆盖配置）

如果你需要在某些情况下覆盖配置文件的值，可以这样做：

```python
config = load_config("config.yaml")

# 代码中的参数会覆盖配置文件中的值
ani = Ani2Openlist(
    config=config,
    year=2024,      # 覆盖配置文件中的 year
    month=10,       # 覆盖配置文件中的 month
    rss_update=False  # 覆盖配置文件中的 rss_update
)
```

## CLI 命令行迁移

### 旧的使用方式

如果你之前直接在命令行中传参数，现在可以使用配置文件：

**旧方式（假设的）：**
```bash
python -m ani2openlist --url http://localhost:5244 --username admin --password pass
```

**新方式：**
```bash
# 创建配置文件后，直接运行
python cli.py

# 或指定配置文件
python cli.py -c config.yaml

# 仍然支持命令行参数覆盖配置文件
python cli.py --year 2024 --month 10
```

## 兼容性说明

✅ **完全向后兼容**：旧的代码方式仍然可以使用，不需要强制迁移。

```python
# 这种方式仍然可以正常工作
ani = Ani2Openlist(
    url="http://localhost:5244",
    username="admin",
    password="password",
    target_dir="/Anime"
)
```

你可以选择：
1. 完全使用配置文件（推荐）
2. 完全使用代码参数（旧方式）
3. 混合使用（配置文件 + 代码参数覆盖）

## 最佳实践

### 1. 不要将配置文件提交到 Git

确保 `config.yaml` 在 `.gitignore` 中：

```gitignore
# Configuration files (contains sensitive data)
config.yaml
```

只提交 `config.yaml.example` 作为模板。

### 2. 为不同环境创建不同的配置文件

```
config.yaml              # 本地开发环境
config.prod.yaml         # 生产环境
config.test.yaml         # 测试环境
```

使用时指定配置文件：

```python
config = load_config("config.prod.yaml")
```

### 3. 使用环境变量增强安全性

对于敏感信息，可以结合环境变量：

```python
import os
from ani2openlist import Ani2Openlist, load_config

config = load_config("config.yaml")

# 从环境变量获取密码
ani = Ani2Openlist(
    config=config,
    password=os.getenv("ALIST_PASSWORD")
)
```

### 4. 验证配置

在使用配置前，验证必需的配置项是否存在：

```python
from ani2openlist import load_config

config = load_config("config.yaml")

# 检查必需的配置
required_keys = ["openlist.url", "openlist.target_dir"]
for key in required_keys:
    if not config.get(key):
        raise ValueError(f"缺少必需的配置项: {key}")
```

## 故障排查

### 问题 1: 找不到配置文件

**错误信息：**
```
FileNotFoundError: 配置文件不存在: config.yaml
```

**解决方案：**
```bash
# 复制示例配置文件
cp config.yaml.example config.yaml

# 或使用 load_config_or_default
config = load_config_or_default("config.yaml")
```

### 问题 2: YAML 格式错误

**错误信息：**
```
yaml.YAMLError: ...
```

**解决方案：**
- 检查缩进（使用空格，不是 Tab）
- 检查冒号后面是否有空格
- 使用 YAML 验证工具检查格式

### 问题 3: 配置值类型错误

确保配置值的类型正确：

```yaml
# 正确
ani:
  rss_update: true      # 布尔值
  year: 2024           # 数字
  
# 错误
ani:
  rss_update: "true"   # 字符串（错误）
  year: "2024"         # 字符串（错误）
```

## 需要帮助？

如果在迁移过程中遇到问题：

1. 查看 [docs/CONFIG.md](CONFIG.md) 获取详细的配置文档
2. 查看 [examples/](../examples/) 目录中的示例代码
3. 在 GitHub 上提交 Issue

## 总结

迁移到配置文件非常简单：

1. ✅ 复制 `config.yaml.example` 为 `config.yaml`
2. ✅ 填写你的配置信息
3. ✅ 在代码中使用 `load_config()` 加载配置
4. ✅ 将配置对象传递给 `Ani2Openlist(config=config)`

就是这么简单！🎉
