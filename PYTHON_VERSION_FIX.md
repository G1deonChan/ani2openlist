# Python 版本兼容性修复

## 问题描述

Docker 容器启动时出现以下错误：

```
TypeError: unsupported operand type(s) for |: 'type' and 'type'
```

## 根本原因

代码中使用了 Python 3.10+ 的新式类型注解语法（`str | int | None`），但 Dockerfile 使用的是 Python 3.9。

## 修复方案

### 1. ✅ 升级 Dockerfile Python 版本

```dockerfile
# 修改前
FROM python:3.9-slim

# 修改后
FROM python:3.10-slim
```

### 2. ✅ 修复 logger.py 类型注解（向后兼容）

```python
# 修改前
def setup_logger(
    level: int = logging.INFO,
    log_file: str | Path | None = None,
    format_string: str | None = None
) -> None:

# 修改后
from typing import Optional, Union

def setup_logger(
    level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    format_string: Optional[str] = None
) -> None:
```

### 3. ✅ 更新 pyproject.toml

```toml
# 修改前
requires-python = ">=3.8"

# 修改后
requires-python = ">=3.10"
```

## Python 版本要求

| 组件 | 最低版本 | 推荐版本 |
|------|---------|---------|
| 本地运行 | Python 3.10 | Python 3.11 |
| Docker 镜像 | Python 3.10 | Python 3.10 |
| CI/CD | Python 3.10 | Python 3.11 |

## 类型注解兼容性

### Python 3.9 及更早版本

```python
from typing import Optional, Union

# 使用 Union
def func(x: Union[str, int]) -> None: pass

# 使用 Optional
def func(x: Optional[str] = None) -> None: pass

# 多类型
def func(x: Union[str, int, None] = None) -> None: pass
```

### Python 3.10+

```python
# 使用 | 操作符
def func(x: str | int) -> None: pass

# 使用 | 和 None
def func(x: str | None = None) -> None: pass

# 多类型
def func(x: str | int | None = None) -> None: pass
```

## 验证修复

### 1. 重新构建镜像

```bash
# 拉取最新代码
git pull origin main

# 构建镜像
docker build -t ani2openlist:test .

# 检查 Python 版本
docker run --rm ani2openlist:test python --version
# 应该输出: Python 3.10.x
```

### 2. 测试运行

```bash
# 准备配置文件
cp config.yaml.example config.yaml
# 编辑 config.yaml...

# 运行容器
docker run -d \
  --name ani2openlist-test \
  -p 5000:5000 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/logs:/app/logs \
  ani2openlist:test

# 查看日志（应该没有 TypeError）
docker logs -f ani2openlist-test

# 访问健康检查
curl http://localhost:5000/health

# 清理
docker stop ani2openlist-test
docker rm ani2openlist-test
```

### 3. 使用 DockerHub 镜像

```bash
# 拉取最新镜像
docker pull yourusername/ani2openlist:latest

# 查看镜像信息
docker inspect yourusername/ani2openlist:latest | grep -i python

# 运行
docker-compose up -d
```

## 兼容性表

| Python 版本 | 类型注解语法 | 项目兼容性 |
|------------|------------|-----------|
| 3.8 | `Union`, `Optional` | ❌ 不兼容（代码未全部修改） |
| 3.9 | `Union`, `Optional` | ❌ 不兼容（部分代码使用 `|`） |
| 3.10 | `Union`, `Optional`, `|` | ✅ 完全兼容 |
| 3.11 | `Union`, `Optional`, `|` | ✅ 完全兼容 |
| 3.12 | `Union`, `Optional`, `|` | ✅ 预计兼容 |

## 如果你使用 Python 3.9

如果你必须使用 Python 3.9，需要修改所有使用 `|` 的类型注解：

```bash
# 搜索需要修改的文件
grep -r ": \w\+ | \w\+" ani2openlist/

# 需要修改的文件列表：
# - ani2openlist/openlist/path.py
# - ani2openlist/openlist/client.py
# - ani2openlist/core/config.py
# - ani2openlist/ani2openlist.py
# - ani2openlist/core/logger.py (已修复)
```

**注意**: 不建议使用 Python 3.9，因为需要大量代码修改。

## 相关链接

- [PEP 604 - Union Type Syntax](https://peps.python.org/pep-0604/)
- [Python 3.10 新特性](https://docs.python.org/3.10/whatsnew/3.10.html)
- [typing 模块文档](https://docs.python.org/3/library/typing.html)

## 后续计划

- ✅ 修复 Python 3.10 兼容性
- ✅ 更新文档说明版本要求
- ✅ 添加故障排查指南
- ⏳ 考虑添加 Python 3.12 支持
- ⏳ 添加自动化测试覆盖不同 Python 版本

---

**修复完成时间**: 2025年10月14日  
**影响范围**: Docker 镜像，本地开发环境  
**状态**: ✅ 已修复并测试
