# Ani2Openlist

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

将 ANI Open 项目的视频通过地址树的方式挂载到 Openlist 服务器上。

## 功能特性

- 🎬 支持从 ANI Open 获取动画资源
- 📡 支持 RSS 订阅追更最新番剧
- 📅 支持按年份和季度筛选动画
- 🔍 支持自定义关键字搜索
- 🌐 支持自定义域名反代
- 📂 自动创建和更新 Openlist UrlTree 存储

## 安装

### 使用 pip 安装

```bash
pip install ani2openlist
```

### 从源码安装

```bash
git clone https://github.com/yourusername/ani2openlist.git
cd ani2openlist
pip install -e .
```

## 快速开始

### 使用配置文件（推荐）

1. 复制配置文件模板：

```bash
cp config.yaml.example config.yaml
```

2. 编辑 `config.yaml` 配置文件：

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
```

3. 运行程序：

```bash
# 使用默认配置文件 config.yaml
python cli.py

# 或指定配置文件
python cli.py -c /path/to/config.yaml
```

4. 或在 Python 代码中使用：

```python
import asyncio
from ani2openlist import Ani2Openlist, load_config

async def main():
    # 从配置文件加载
    config = load_config("config.yaml")
    
    # 创建实例
    ani = Ani2Openlist(config=config)
    
    # 运行更新
    await ani.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### 使用代码配置

#### 基本用法

```python
import asyncio
from ani2openlist import Ani2Openlist

async def main():
    # 创建 Ani2Openlist 实例
    ani = Ani2Openlist(
        url="http://localhost:5244",  # Openlist 服务器地址
        username="admin",              # Openlist 用户名
        password="password",           # Openlist 密码
        target_dir="/Anime",           # 挂载目录
        rss_update=True                # 使用 RSS 追更
    )
    
    # 运行更新
    await ani.run()

if __name__ == "__main__":
    asyncio.run(main())
```

#### 使用 Token 认证

```python
ani = Ani2Openlist(
    url="http://localhost:5244",
    token="your-openlist-token",
    target_dir="/Anime",
    rss_update=True
)
```

#### 按季度获取动画

```python
ani = Ani2Openlist(
    url="http://localhost:5244",
    username="admin",
    password="password",
    target_dir="/Anime",
    rss_update=False,
    year=2024,
    month=10  # 2024年10月（秋季）
)
```

#### 使用自定义关键字

```python
ani = Ani2Openlist(
    url="http://localhost:5244",
    username="admin",
    password="password",
    target_dir="/Anime",
    rss_update=False,
    key_word="2024-10"  # 自定义关键字
)
```

#### 自定义域名反代

```python
ani = Ani2Openlist(
    url="http://localhost:5244",
    username="admin",
    password="password",
    target_dir="/Anime",
    rss_update=True,
    src_domain="your-aniopen-proxy.com",  # ANI Open 反代域名
    rss_domain="your-rss-proxy.com"       # RSS 反代域名
)
```

## 配置说明

### 配置文件结构

配置文件使用 YAML 格式，包含以下几个部分：

#### Openlist 配置

```yaml
openlist:
  url: "http://localhost:5244"     # Openlist 服务器地址
  username: "admin"                # 用户名（与 token 二选一）
  password: "password"             # 密码（与 token 二选一）
  token: "your-token"              # Token 认证（优先使用）
  target_dir: "/Anime"             # 挂载目录
```

#### ANI Open 配置

```yaml
ani:
  rss_update: true                          # 使用 RSS 追更
  year: 2024                                # 动画年份（rss_update=false 时）
  month: 10                                 # 动画季度（rss_update=false 时）
  key_word: "2024-10"                       # 自定义关键字
  src_domain: "aniopen.an-i.workers.dev"   # ANI Open 源域名
  rss_domain: "api.ani.rip"                # RSS 域名
```

#### 日志配置

```yaml
logging:
  level: "INFO"                    # 日志级别: DEBUG/INFO/WARNING/ERROR
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/ani2openlist.log"       # 日志文件（可选）
  max_bytes: 10485760              # 日志文件最大大小（可选）
  backup_count: 5                  # 保留的日志文件数量（可选）
```

### 命令行参数

命令行参数会覆盖配置文件中的设置：

```bash
# 指定配置文件
python cli.py -c config.yaml

# 覆盖配置文件中的参数
python cli.py --url http://localhost:5244 --username admin --password pass

# 使用 RSS 追更
python cli.py --rss

# 指定年份和季度
python cli.py --year 2024 --month 10

# 使用自定义关键字
python cli.py --keyword "2024-10"
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| url | str | "http://localhost:5244" | Openlist 服务器地址 |
| username | str | "" | Openlist 用户名 |
| password | str | "" | Openlist 密码 |
| token | str | "" | Openlist 永久令牌（与用户名密码二选一） |
| target_dir | str | "/Anime" | 挂载到 Openlist 的目录 |
| rss_update | bool | True | 是否使用 RSS 追更最新番剧 |
| year | int \| None | None | 动画年份 |
| month | int \| None | None | 动画季度（1, 4, 7, 10） |
| src_domain | str | "aniopen.an-i.workers.dev" | ANI Open 项目地址 |
| rss_domain | str | "api.ani.rip" | RSS 订阅地址 |
| key_word | str \| None | None | 自定义关键字 |
| config | Config \| None | None | Config 对象（优先使用） |

## 项目结构

```
ani2openlist/
├── ani2openlist/           # 主包
│   ├── __init__.py
│   ├── ani2openlist.py    # 核心功能
│   ├── openlist/          # Openlist 客户端
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── path.py
│   │   └── storage.py
│   ├── core/           # 核心模块
│   │   ├── __init__.py
│   │   ├── config.py   # 配置管理
│   │   └── logger.py   # 日志管理
│   └── utils/          # 工具类
│       ├── __init__.py
│       ├── openlist.py
│       ├── http.py
│       ├── multiton.py
│       ├── retry.py
│       ├── singleton.py
│       └── url.py
├── examples/           # 示例代码
│   ├── config_usage.py # 配置文件使用示例
│   └── ...
├── config.yaml.example # 配置文件模板
├── config.yaml        # 配置文件
├── requirements.txt   # 依赖
├── setup.py          # 安装配置
├── cli.py            # 命令行入口
└── README.md         # 说明文档
```

## 依赖项

- Python 3.10+
- feedparser >= 6.0.11
- httpx[http2] >= 0.27.2
- pydantic >= 2.9.2
- PyYAML >= 6.0

## 许可证

本项目基于 MIT 许可证开源。详见 [LICENSE](LICENSE) 文件。

## 致谢

- [ANI Open](https://github.com/open-ani/ani-open) - 动画资源提供
- [Openlist](https://github.com/openlist-org/openlist) - 文件列表程序

## 相关项目

本项目提取自 [AutoFilm](https://github.com/AkimioJR/AutoFilm)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 作者

AkimioJR

## 更新日志

### v1.0.0 (2025-10-14)
- 首次发布
- 从 AutoFilm 项目独立出来
- 支持 RSS 追更和按季度获取动画
- 支持自定义关键字和域名反代
