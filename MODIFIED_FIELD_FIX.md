# Alist/Openlist API Modified 字段错误修复

## 问题描述

Web UI 执行任务时出现以下错误：

```
任务执行失败: 更新存储器失败，详细信息：
model.Storage.Disabled: Modified: unmarshalerDecoder: 
parsing time "" as "2006-01-02T15:04:05Z07:00": cannot parse "" as "2006"
```

## 根本原因

1. **API 返回空字符串**: Alist/Openlist API 在某些情况下会返回空的 `modified` 字段（`"modified": ""`）

2. **类型解析错误**: 当更新存储器时，代码将这个空字符串原样发送回 API，导致服务端尝试将空字符串解析为时间格式时失败

3. **字段定义问题**: `modified` 字段定义为 `str = ""`，没有处理空值的情况

## 修复方案

### 1. ✅ 修改字段类型为可选

```python
# 修改前
modified: str = ""  # 修改时间

# 修改后
modified: Optional[str] = None  # 修改时间（可为空）
```

### 2. ✅ 添加字段验证器

```python
@field_validator("modified", mode="before")
@classmethod
def validate_modified(cls, v):
    """验证 modified 字段，将空字符串转换为 None"""
    if v == "" or v is None:
        return None
    return v
```

### 3. ✅ 更新 API 调用时排除空值

```python
# 更新存储器时，只在 modified 不为空时才包含它
if storage.modified:
    json["modified"] = storage.modified
```

## 已修改的文件

```
✅ ani2openlist/openlist/storage.py
   - 修改 modified 字段类型为 Optional[str]
   - 添加字段验证器处理空字符串

✅ ani2openlist/openlist/client.py
   - 更新存储器时，只在 modified 不为空时才发送该字段
```

## 技术细节

### Alist/Openlist 存储器结构

```json
{
  "id": 1,
  "mount_path": "/path",
  "driver": "UrlTree",
  "modified": "",  // 这个字段可能为空字符串
  "disabled": false,
  ...
}
```

### Go 时间格式

Alist/Openlist 使用 Go 语言，时间格式为：`2006-01-02T15:04:05Z07:00`

当字段为空字符串时，Go 的时间解析会失败：
```go
time.Parse("2006-01-02T15:04:05Z07:00", "")  // 错误！
```

### Pydantic 字段验证

使用 `field_validator` 在数据进入模型之前进行预处理：

```python
@field_validator("modified", mode="before")
@classmethod
def validate_modified(cls, v):
    """
    mode="before": 在 Pydantic 验证之前执行
    将空字符串转换为 None，避免类型错误
    """
    if v == "" or v is None:
        return None
    return v
```

## 测试验证

### 1. 本地测试

```python
from ani2openlist.openlist.storage import OpenlistStorage

# 测试空字符串
storage1 = OpenlistStorage(modified="")
assert storage1.modified is None

# 测试 None
storage2 = OpenlistStorage(modified=None)
assert storage2.modified is None

# 测试有效值
storage3 = OpenlistStorage(modified="2024-10-14T12:00:00Z")
assert storage3.modified == "2024-10-14T12:00:00Z"

print("✅ 所有测试通过")
```

### 2. Web UI 测试

```bash
# 启动 Web UI
python webui_start.py

# 访问 http://localhost:5000
# 点击"立即执行"按钮
# 检查日志是否有 modified 字段错误
```

### 3. Docker 测试

```bash
# 构建并运行
docker-compose up -d

# 查看日志
docker-compose logs -f

# 应该没有 "parsing time" 错误
```

## 相关问题

### 为什么会有空的 modified 字段？

1. **新创建的存储器**: 刚创建的存储器可能还没有修改时间
2. **API 版本差异**: 不同版本的 Alist 可能处理方式不同
3. **数据库迁移**: 从旧版本升级时可能没有这个字段

### 其他可能的空字段

类似的问题可能出现在其他时间字段上：
- `created` - 创建时间
- `updated` - 更新时间

如果遇到类似错误，采用相同的修复方案。

## 向后兼容性

### ✅ 兼容性良好

- 对于有值的 `modified` 字段，行为不变
- 对于空字符串，自动转换为 `None`
- API 调用时自动过滤 `None` 值
- 不影响现有功能

### 升级指南

无需任何配置更改，直接升级即可：

```bash
# 拉取最新代码
git pull origin main

# 重启服务
docker-compose restart

# 或重新构建
docker-compose up -d --build
```

## 预防措施

### 1. API 响应验证

在接收 API 响应时，添加数据验证：

```python
# 在 client.py 中
response_data = resp.json()
# Pydantic 会自动验证和转换数据
storage = OpenlistStorage(**response_data)
```

### 2. 发送请求时过滤空值

```python
# 构建请求 JSON 时
json = {k: v for k, v in data.items() if v is not None}
```

### 3. 日志记录

```python
if not storage.modified:
    logger.debug(f"存储器 {storage.id} 的 modified 字段为空，将被忽略")
```

## 相关链接

- [Pydantic Field Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [Alist API Documentation](https://alist.nn.ci/guide/api/)
- [Go Time Format](https://golang.org/pkg/time/#Time.Parse)

---

**修复完成时间**: 2025年10月14日  
**影响范围**: 存储器更新操作  
**状态**: ✅ 已修复并测试
