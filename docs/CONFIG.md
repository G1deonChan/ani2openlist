# 配置文件使用指南

## 简介

从 v1.0.0 开始，ani2openlist 支持使用 YAML 配置文件来管理配置。这种方式比直接在代码中硬编码配置更加灵活和易于管理。

## 配置文件位置

默认情况下，程序会查找以下位置的配置文件：
- `config.yaml` （项目根目录）
- 或通过命令行参数 `-c` 指定的路径

## 创建配置文件

1. 复制示例配置文件：

```bash
cp config.yaml.example config.yaml
```

2. 编辑 `config.yaml` 文件：

```yaml
# Openlist 服务器配置
openlist:
  url: "http://localhost:5244"
  username: "admin"
  password: "your_password"
  target_dir: "/Anime"

# ANI Open 配置
ani:
  rss_update: true
  src_domain: "aniopen.an-i.workers.dev"
  rss_domain: "api.ani.rip"

# 日志配置
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## 配置项说明

### Openlist 配置 (openlist)

| 配置项 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| url | string | 是 | Openlist 服务器地址 | http://localhost:5244 |
| username | string | * | 用户名（与 token 二选一） | - |
| password | string | * | 密码（与 token 二选一） | - |
| token | string | * | Token 认证（优先级高于用户名密码） | - |
| target_dir | string | 是 | 挂载目录 | /Anime |

\* 注：`username+password` 或 `token` 必须提供其中一种认证方式

### ANI Open 配置 (ani)

| 配置项 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| rss_update | boolean | 否 | 是否使用 RSS 追更 | true |
| year | integer | 否 | 动画年份（rss_update=false 时） | - |
| month | integer | 否 | 动画季度：1/4/7/10（rss_update=false 时） | - |
| key_word | string | 否 | 自定义关键字 | - |
| src_domain | string | 否 | ANI Open 源域名 | aniopen.an-i.workers.dev |
| rss_domain | string | 否 | RSS 域名 | api.ani.rip |

### 日志配置 (logging)

| 配置项 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| level | string | 否 | 日志级别：DEBUG/INFO/WARNING/ERROR/CRITICAL | INFO |
| format | string | 否 | 日志格式 | %(asctime)s - %(name)s - %(levelname)s - %(message)s |
| file | string | 否 | 日志文件路径（不配置则只输出到控制台） | - |
| max_bytes | integer | 否 | 日志文件最大大小（字节） | 10485760 (10MB) |
| backup_count | integer | 否 | 保留的日志文件数量 | 5 |

## 使用方式

### 1. 命令行使用

```bash
# 使用默认配置文件 config.yaml
python cli.py

# 指定配置文件
python cli.py -c /path/to/config.yaml

# 命令行参数覆盖配置文件
python cli.py --url http://localhost:5244 --username admin
```

### 2. Python 代码使用

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

### 3. 混合使用（配置文件 + 代码参数）

```python
import asyncio
from ani2openlist import Ani2Openlist, load_config

async def main():
    # 加载配置文件
    config = load_config("config.yaml")
    
    # 代码参数会覆盖配置文件中的值
    ani = Ani2Openlist(
        config=config,
        year=2024,
        month=10,
        rss_update=False
    )
    
    await ani.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## 配置示例

### 示例 1：RSS 追更模式

```yaml
openlist:
  url: "http://localhost:5244"
  token: "your-openlist-token"
  target_dir: "/Anime"

ani:
  rss_update: true
  src_domain: "aniopen.an-i.workers.dev"
  rss_domain: "api.ani.rip"

logging:
  level: "INFO"
```

### 示例 2：指定季度

```yaml
openlist:
  url: "http://localhost:5244"
  username: "admin"
  password: "password"
  target_dir: "/Anime/2024/Fall"

ani:
  rss_update: false
  year: 2024
  month: 10
  src_domain: "aniopen.an-i.workers.dev"

logging:
  level: "DEBUG"
  file: "logs/ani2openlist.log"
```

### 示例 3：自定义关键字

```yaml
openlist:
  url: "http://192.168.1.100:5244"
  token: "openlist-xxxxxxxxxxxx"
  target_dir: "/Anime/Search"

ani:
  rss_update: false
  key_word: "chainsaw man"
  src_domain: "your-proxy.com"
  rss_domain: "your-rss-proxy.com"

logging:
  level: "WARNING"
```

## 配置优先级

当同时存在多个配置来源时，优先级如下（从高到低）：

1. 代码中直接传入的参数
2. 命令行参数
3. 配置文件中的值
4. 默认值

例如：

```python
config = load_config("config.yaml")  # url = "http://localhost:5244"
ani = Ani2Openlist(
    config=config,
    url="http://192.168.1.100:5244"  # 这个会覆盖配置文件中的 url
)
```

## 最佳实践

1. **使用配置文件**: 将敏感信息（密码、Token）和常用配置保存在配置文件中
2. **版本控制**: 将 `config.yaml` 添加到 `.gitignore`，只提交 `config.yaml.example`
3. **环境分离**: 为不同环境（开发、测试、生产）创建不同的配置文件
4. **日志管理**: 生产环境使用 INFO 或 WARNING 级别，开发时使用 DEBUG
5. **定期备份**: 备份重要的配置文件

## 故障排查

### 配置文件不存在

```python
from ani2openlist import load_config_or_default

# 使用此函数可以在配置文件不存在时返回默认配置，而不抛出异常
config = load_config_or_default("config.yaml")
```

### 配置文件格式错误

确保 YAML 文件格式正确，注意缩进（使用空格，不是 Tab）：

```yaml
# 正确
openlist:
  url: "http://localhost:5244"

# 错误（缩进不对）
openlist:
url: "http://localhost:5244"
```

### 配置值类型错误

确保配置值的类型正确：

```yaml
# 正确
ani:
  rss_update: true
  year: 2024
  month: 10

# 错误
ani:
  rss_update: "true"  # 应该是布尔值，不是字符串
  year: "2024"        # 应该是整数，不是字符串
```

## 参考

- [YAML 语法教程](https://yaml.org/spec/1.2.2/)
- [PyYAML 文档](https://pyyaml.org/wiki/PyYAMLDocumentation)
