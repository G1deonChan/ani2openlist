# 使用指南

## 快速开始

### 1. 安装

```bash
pip install ani2openlist
```

或从源码安装：

```bash
git clone https://github.com/yourusername/ani2openlist.git
cd ani2openlist
pip install -e .
```

### 2. 配置

复制配置示例文件：

```bash
cp config/config.yaml.example config/config.yaml
```

编辑 `config/config.yaml`，填入你的配置：

```yaml
ani:
  base_url: https://api.bgm.tv
  enable: true
  rate_limit: 1.0

openlist:
  base_url: http://localhost:5244
  token: "your_openlist_token_here"
  root_path: /anime
```

### 3. 基本使用

```python
from app.modules.ani2openlist import Ani2Openlist
from app.core.config import load_config

# 加载配置
config = load_config('config/config.yaml')

# 创建实例
ani2openlist = Ani2Openlist(config)

# 搜索动漫
results = ani2openlist.search("葬送的芙莉莲")
for anime in results:
    print(f"{anime['id']}: {anime['name']}")

# 获取详细信息
info = ani2openlist.get_anime_info(results[0]['id'])
print(f"简介: {info['summary']}")

# 整理文件
result = ani2openlist.organize("/anime/unsorted")
print(f"整理完成: 成功 {result['success']} 个，失败 {result['failed']} 个")
```

## 高级用法

### 批量整理

```python
# 整理多个目录
paths = [
    "/anime/season1",
    "/anime/season2",
    "/anime/movies"
]

for path in paths:
    print(f"整理 {path}...")
    result = ani2openlist.organize(path)
    print(f"结果: {result}")
```

### 自定义文件匹配规则

```python
from app.modules.ani2openlist import Ani2Openlist

config['ani']['filename_patterns'] = [
    r'\[(?P<group>.*?)\].*?(?P<episode>\d+).*?\.(?P<ext>mkv|mp4)',
    r'S(?P<season>\d+)E(?P<episode>\d+)',
]

ani2openlist = Ani2Openlist(config)
```

### 使用过滤器

```python
# 只处理特定格式的文件
def video_filter(file_info):
    return file_info['name'].endswith(('.mkv', '.mp4', '.avi'))

result = ani2openlist.organize(
    "/anime/unsorted",
    file_filter=video_filter
)
```

### 同步到 Openlist

```python
# 从 Bangumi 获取信息并同步到 Openlist
anime_id = 12345  # Bangumi 动漫 ID
openlist_path = "/anime/葬送的芙莉莲"

# 同步元数据
success = ani2openlist.sync(anime_id, openlist_path)
if success:
    print("同步成功！")
```

## 命令行使用

### 搜索动漫

```bash
python -m app.modules.ani2openlist search "葬送的芙莉莲"
```

### 整理文件

```bash
python -m app.modules.ani2openlist organize "/anime/unsorted"
```

### 同步信息

```bash
python -m app.modules.ani2openlist sync 12345 "/anime/葬送的芙莉莲"
```

## 常见场景

### 场景 1: 新番整理

```python
# 每周自动整理新番目录
import schedule
import time

def organize_new_anime():
    result = ani2openlist.organize("/anime/new")
    print(f"整理完成: {result}")

# 每天凌晨3点执行
schedule.every().day.at("03:00").do(organize_new_anime)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 场景 2: 批量重命名

```python
# 根据 Bangumi 信息批量重命名文件
files = ani2openlist.openlist_client.list_files("/anime/unsorted")

for file in files:
    # 识别文件名中的关键信息
    anime_name = extract_anime_name(file['name'])
    
    # 搜索 Bangumi
    results = ani2openlist.search(anime_name)
    if results:
        anime = results[0]
        # 根据标准格式重命名
        new_name = f"{anime['name']}/{file['name']}"
        ani2openlist.openlist_client.rename(file['path'], new_name)
```

### 场景 3: 自动创建目录结构

```python
# 为每个动漫创建标准目录结构
anime_list = [12345, 23456, 34567]  # Bangumi ID 列表

for anime_id in anime_list:
    info = ani2openlist.get_anime_info(anime_id)
    
    # 创建目录
    base_path = f"/anime/{info['name']}"
    ani2openlist.openlist_client.create_folder(base_path)
    ani2openlist.openlist_client.create_folder(f"{base_path}/Season 1")
    ani2openlist.openlist_client.create_folder(f"{base_path}/Special")
    
    # 同步元数据
    ani2openlist.sync(anime_id, base_path)
```

## Docker 使用

### 构建镜像

```bash
docker build -t ani2openlist .
```

### 运行容器

```bash
docker run -d \
  --name ani2openlist \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  ani2openlist
```

### Docker Compose

```yaml
version: '3'
services:
  ani2openlist:
    build: .
    container_name: ani2openlist
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    restart: unless-stopped
```

## 故障排查

### 问题 1: 无法连接到 Openlist

**解决方案:**
- 检查 Openlist 服务是否运行
- 确认 `base_url` 配置正确
- 验证 token 是否有效

```python
# 测试连接
try:
    files = ani2openlist.openlist_client.list_files("/")
    print("连接成功！")
except Exception as e:
    print(f"连接失败: {e}")
```

### 问题 2: Bangumi API 请求失败

**解决方案:**
- 检查网络连接
- 增加 `rate_limit` 值，减慢请求速度
- 确认 API 地址正确

```python
# 测试 API
try:
    results = ani2openlist.search("test")
    print("API 正常")
except Exception as e:
    print(f"API 错误: {e}")
```

### 问题 3: 文件识别不准确

**解决方案:**
- 调整文件名匹配规则
- 使用自定义过滤器
- 手动指定动漫信息

```python
# 手动指定
ani2openlist.organize(
    "/anime/unsorted",
    anime_id=12345,  # 指定 Bangumi ID
    force=True       # 强制处理
)
```

## 性能优化

### 1. 启用缓存

```python
config['ani']['cache_enabled'] = True
config['ani']['cache_ttl'] = 3600  # 缓存 1 小时
```

### 2. 并发处理

```python
from concurrent.futures import ThreadPoolExecutor

def process_path(path):
    return ani2openlist.organize(path)

paths = ["/anime/path1", "/anime/path2", "/anime/path3"]

with ThreadPoolExecutor(max_workers=3) as executor:
    results = executor.map(process_path, paths)
```

### 3. 批量操作

```python
# 批量移动文件
files_to_move = [
    ("/src/file1.mkv", "/dst/file1.mkv"),
    ("/src/file2.mkv", "/dst/file2.mkv"),
]

for src, dst in files_to_move:
    ani2openlist.openlist_client.move(src, dst)
```

## 最佳实践

1. **定期备份**: 整理前备份重要文件
2. **测试运行**: 先在小范围测试，确认无误后再大规模使用
3. **日志监控**: 定期检查日志，发现潜在问题
4. **版本控制**: 配置文件使用版本控制管理
5. **错误处理**: 始终处理可能的异常情况

## 更多示例

查看 `example.py` 文件获取更多使用示例。
