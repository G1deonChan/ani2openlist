# 项目结构# ani2openlist 项目结构说明



```## 📁 项目结构

ani2openlist/

├── ani2openlist/              # 主包目录```

│   ├── __init__.py        # 包初始化ani2openlist/

│   ├── ani2openlist.py       # 核心功能├── app/                          # 应用核心代码

│   ├── openlist/             # Openlist 客户端│   ├── __init__.py              # 包初始化，版本信息

│   │   ├── client.py      # API 客户端│   ├── core/                    # 核心模块

│   │   ├── path.py        # 路径处理│   │   ├── __init__.py

│   │   └── storage.py     # 存储管理│   │   ├── config.py           # 配置管理

│   ├── core/              # 核心模块│   │   └── logger.py           # 日志管理

│   │   ├── config.py      # 配置管理│   ├── modules/                 # 功能模块

│   │   └── logger.py      # 日志管理│   │   ├── __init__.py

│   └── utils/             # 工具模块│   │   ├── ani2openlist/          # 主要功能模块

│       ├── openlist.py       # Openlist 工具│   │   │   ├── __init__.py

│       ├── http.py        # HTTP 请求│   │   │   └── ani2openlist.py   # 核心业务逻辑

│       ├── url.py         # URL 处理│   │   └── openlist/              # Openlist 客户端

│       └── ...            # 其他工具│   │       ├── __init__.py

├── docs/                  # 文档│   │       └── v3/             # Openlist v3 API

│   ├── CONFIG.md         # 配置说明│   │           ├── __init__.py

│   ├── MIGRATION.md      # 迁移指南│   │           ├── client.py   # API 客户端

│   ├── USAGE.md          # 使用文档│   │           ├── path.py     # 路径操作

│   ├── API.md            # API 文档│   │           └── storage.py  # 存储操作

│   └── FAQ.md            # 常见问题│   └── utils/                   # 工具类

├── examples/             # 示例代码│       ├── __init__.py

│   ├── config_usage.py   # 配置文件使用│       ├── openlist.py            # Openlist 工具

│   ├── basic_usage.py    # 基本使用│       ├── http.py             # HTTP 客户端

│   └── ...               # 其他示例│       ├── url.py              # URL 工具

├── tests/                # 测试│       ├── retry.py            # 重试装饰器

│   └── test_ani2openlist.py│       ├── singleton.py        # 单例模式

├── cli.py                # 命令行工具│       └── multiton.py         # 多例模式

├── run.py                # 快速运行脚本├── config/                      # 配置文件

├── quickstart.py         # 快速开始│   └── config.yaml.example     # 配置示例

├── test_setup.py         # 配置测试├── docs/                        # 文档

├── config.yaml.example   # 配置模板│   ├── API.md                  # API 文档

├── requirements.txt      # 依赖│   ├── USAGE.md                # 使用指南

├── setup.py              # 安装配置│   └── FAQ.md                  # 常见问题

├── README.md             # 项目说明├── tests/                       # 测试文件

└── CHANGELOG.md          # 更新日志│   ├── __init__.py

```│   └── test_ani2openlist.py       # 单元测试

├── logs/                        # 日志目录（运行时创建）

## 核心文件├── .github/                     # GitHub 配置

│   └── workflows/

- **ani2openlist/ani2openlist.py**: 主要业务逻辑│       └── python-tests.yml    # CI/CD 工作流

- **cli.py**: 命令行入口├── __init__.py                  # 包入口

- **run.py**: 简单启动脚本├── cli.py                       # 命令行接口

- **config.yaml**: 配置文件（需自行创建）├── example.py                   # 使用示例

- **requirements.txt**: Python 依赖├── quickstart.py                # 快速开始

├── setup.py                     # 安装脚本

## 文档├── pyproject.toml              # 项目配置

├── requirements.txt             # 依赖列表

- **README.md**: 项目介绍和快速开始├── README.md                    # 项目说明

- **docs/CONFIG.md**: 配置文件详细说明├── LICENSE                      # 许可证

- **docs/USAGE.md**: 使用指南├── CHANGELOG.md                 # 更新日志

- **docs/MIGRATION.md**: 迁移指南├── CONTRIBUTING.md              # 贡献指南

- **CHANGELOG.md**: 版本更新记录├── MANIFEST.in                  # 打包配置

├── Dockerfile                   # Docker 配置

## 使用文件├── .dockerignore               # Docker 忽略

└── .gitignore                  # Git 忽略

- **test_setup.py**: 测试配置是否正确```

- **run.py**: 快速运行程序

- **quickstart.py**: 快速开始示例## 📋 文件说明


### 核心模块

- **app/core/config.py**: 配置文件加载和管理
- **app/core/logger.py**: 日志系统配置
- **app/modules/ani2openlist/ani2openlist.py**: 主要业务逻辑，包含搜索、整理、同步等功能
- **app/modules/openlist/v3/client.py**: Openlist v3 API 客户端

### 工具类

- **app/utils/http.py**: HTTP 请求封装，支持重试
- **app/utils/openlist.py**: Openlist 相关工具函数
- **app/utils/url.py**: URL 处理工具
- **app/utils/retry.py**: 重试装饰器
- **app/utils/singleton.py**: 单例模式实现
- **app/utils/multiton.py**: 多例模式实现

### 入口文件

- **cli.py**: 命令行工具入口
- **example.py**: 使用示例代码
- **quickstart.py**: 快速开始脚本

### 配置文件

- **config/config.yaml.example**: 配置文件模板
- **setup.py**: Python 包安装配置
- **pyproject.toml**: 现代 Python 项目配置
- **requirements.txt**: 依赖包列表

### 文档

- **README.md**: 项目介绍和快速开始
- **docs/API.md**: 详细的 API 文档
- **docs/USAGE.md**: 使用指南和示例
- **docs/FAQ.md**: 常见问题解答

### 其他

- **LICENSE**: MIT 许可证
- **CHANGELOG.md**: 版本更新记录
- **CONTRIBUTING.md**: 贡献指南
- **Dockerfile**: Docker 容器配置
- **.github/workflows/**: GitHub Actions CI/CD 配置

## 🚀 快速开始

### 1. 安装

```bash
cd ani2openlist
pip install -e .
```

### 2. 配置

```bash
cp config/config.yaml.example config/config.yaml
# 编辑 config/config.yaml，填入你的配置
```

### 3. 测试

```bash
python quickstart.py
```

### 4. 使用

```bash
# 命令行
python cli.py search "葬送的芙莉莲"

# Python 代码
python example.py
```

## 📦 依赖关系

```
ani2openlist
├── requests (HTTP 请求)
├── pyyaml (配置文件解析)
└── loguru (日志记录)
```

## 🔧 开发依赖

```
pytest (测试框架)
pytest-cov (测试覆盖率)
black (代码格式化)
flake8 (代码检查)
mypy (类型检查)
```

## 📝 主要功能

1. **搜索动漫**: 从 Bangumi 搜索动漫信息
2. **获取详情**: 获取动漫的详细信息
3. **整理文件**: 自动整理 Openlist 中的动漫文件
4. **同步信息**: 同步 Bangumi 信息到 Openlist
5. **重命名**: 根据规则重命名文件
6. **目录管理**: 创建和管理动漫目录结构

## 🔌 扩展性

项目设计考虑了扩展性：

- **模块化**: 各功能模块独立，易于扩展
- **配置化**: 大部分行为可通过配置文件控制
- **插件化**: 可以轻松添加新的数据源或存储后端
- **工具类**: 提供了丰富的工具类供复用

## 📚 学习路径

1. 阅读 README.md 了解项目概况
2. 查看 example.py 学习基本使用
3. 运行 quickstart.py 测试环境
4. 阅读 docs/USAGE.md 了解高级用法
5. 查看 docs/API.md 了解详细 API
6. 阅读源码了解实现细节

## 🤝 贡献

欢迎贡献！请查看 CONTRIBUTING.md 了解详情。

## 📄 许可证

MIT License - 详见 LICENSE 文件
