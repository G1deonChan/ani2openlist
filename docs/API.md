# API 文档

## Ani2Openlist 类

主要的类，用于从 Bangumi 同步动漫信息到 Openlist。

### 初始化

```python
from app.modules.ani2openlist import Ani2Openlist

config = {
    'ani': {
        'base_url': 'https://api.bgm.tv',
        'enable': True,
        'rate_limit': 1.0  # 请求间隔（秒）
    },
    'openlist': {
        'base_url': 'http://localhost:5244',
        'token': 'your_openlist_token',
        'root_path': '/anime'
    }
}

ani2openlist = Ani2Openlist(config)
```

### 方法

#### `search(keyword: str) -> list`

搜索动漫信息。

**参数:**
- `keyword` (str): 搜索关键词

**返回:**
- list: 搜索结果列表

**示例:**
```python
results = ani2openlist.search("葬送的芙莉莲")
for anime in results:
    print(f"ID: {anime['id']}, Name: {anime['name']}")
```

#### `get_anime_info(anime_id: int) -> dict`

获取动漫详细信息。

**参数:**
- `anime_id` (int): 动漫 ID

**返回:**
- dict: 动漫详细信息

**示例:**
```python
info = ani2openlist.get_anime_info(12345)
print(f"标题: {info['name']}")
print(f"简介: {info['summary']}")
```

#### `organize(path: str) -> dict`

整理指定路径的动漫文件。

**参数:**
- `path` (str): Openlist 中的路径

**返回:**
- dict: 整理结果统计

**示例:**
```python
result = ani2openlist.organize("/anime/unsorted")
print(f"成功: {result['success']}, 失败: {result['failed']}")
```

#### `sync(anime_id: int, openlist_path: str) -> bool`

同步动漫信息到 Openlist。

**参数:**
- `anime_id` (int): Bangumi 动漫 ID
- `openlist_path` (str): Openlist 目标路径

**返回:**
- bool: 是否成功

**示例:**
```python
success = ani2openlist.sync(12345, "/anime/葬送的芙莉莲")
if success:
    print("同步成功！")
```

## OpenlistClient 类

Openlist API 客户端。

### 初始化

```python
from app.modules.openlist.v3 import OpenlistClient

client = OpenlistClient(
    base_url="http://localhost:5244",
    token="your_token"
)
```

### 方法

#### `list_files(path: str) -> list`

列出目录中的文件。

**参数:**
- `path` (str): 目录路径

**返回:**
- list: 文件列表

#### `move(src: str, dst: str) -> bool`

移动文件或目录。

**参数:**
- `src` (str): 源路径
- `dst` (str): 目标路径

**返回:**
- bool: 是否成功

#### `rename(path: str, new_name: str) -> bool`

重命名文件或目录。

**参数:**
- `path` (str): 文件路径
- `new_name` (str): 新名称

**返回:**
- bool: 是否成功

#### `create_folder(path: str) -> bool`

创建目录。

**参数:**
- `path` (str): 目录路径

**返回:**
- bool: 是否成功

## HttpClient 类

HTTP 请求客户端。

### 初始化

```python
from app.utils import HttpClient

client = HttpClient(
    timeout=30,
    max_retries=3,
    headers={'User-Agent': 'ani2openlist/1.0'}
)
```

### 方法

#### `get(url: str, **kwargs) -> dict`

发送 GET 请求。

#### `post(url: str, **kwargs) -> dict`

发送 POST 请求。

#### `put(url: str, **kwargs) -> dict`

发送 PUT 请求。

#### `delete(url: str, **kwargs) -> dict`

发送 DELETE 请求。

## 配置项

### ani 配置

```yaml
ani:
  base_url: https://api.bgm.tv  # Bangumi API 地址
  enable: true                   # 是否启用
  rate_limit: 1.0               # 请求间隔（秒）
  user_agent: "ani2openlist/1.0"   # User-Agent
```

### openlist 配置

```yaml
openlist:
  base_url: http://localhost:5244  # Openlist 地址
  token: your_token_here           # API Token
  root_path: /anime                # 根目录路径
  timeout: 30                      # 请求超时（秒）
```

### 日志配置

```yaml
log:
  level: INFO                    # 日志级别
  file: logs/ani2openlist.log      # 日志文件
  rotation: "100 MB"            # 日志轮转大小
  retention: "30 days"          # 日志保留时间
  format: "{time} | {level} | {message}"  # 日志格式
```

## 错误处理

所有方法都可能抛出以下异常：

- `requests.exceptions.RequestException`: 网络请求错误
- `ValueError`: 参数错误
- `KeyError`: 数据格式错误

建议使用 try-except 处理：

```python
try:
    result = ani2openlist.search("关键词")
except requests.exceptions.RequestException as e:
    print(f"网络错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

## 最佳实践

1. **使用配置文件**: 将配置保存在 `config/config.yaml` 中
2. **设置合理的速率限制**: 避免频繁请求导致被封禁
3. **启用日志**: 方便调试和问题追踪
4. **错误处理**: 始终处理可能的异常
5. **批量操作**: 对于大量文件，使用批量处理提高效率
