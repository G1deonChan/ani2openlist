# Ani2Openlist 示例

本目录包含 Ani2Openlist 的各种使用示例。

## 示例列表

### 1. config_usage.py （推荐）
使用配置文件的示例，这是最推荐的使用方式。

```bash
python config_usage.py
```

### 2. basic_usage.py
基本使用示例，使用 RSS 追更最新番剧。

```bash
python basic_usage.py
```

### 3. token_auth.py
使用 Openlist 永久 Token 进行认证的示例。

```bash
python token_auth.py
```

### 4. season_anime.py
按年份和季度获取动画的示例。

```bash
python season_anime.py
```

### 5. custom_keyword.py
使用自定义关键字搜索动画的示例。

```bash
python custom_keyword.py
```

### 6. custom_domain.py
使用自定义反代域名的示例。

```bash
python custom_domain.py
```

### 7. with_logging.py
配置详细日志输出的示例。

```bash
python with_logging.py
```

## 运行前准备

### 方式一：使用配置文件（推荐）

1. 确保已安装 ani2openlist：
```bash
pip install ani2openlist
```

2. 复制并修改配置文件：
```bash
cp ../config.yaml.example ../config.yaml
```

3. 编辑 `config.yaml` 文件，填写你的配置信息

4. 运行示例：
```bash
python config_usage.py
```

### 方式二：直接修改代码

1. 确保已安装 ani2openlist：
```bash
pip install ani2openlist
```

2. 修改示例代码中的配置：
   - Openlist 服务器地址
   - 用户名和密码（或 Token）
   - 目标目录路径

3. 确保 Openlist 服务器正在运行且可访问

## 注意事项

- 推荐使用配置文件方式，便于管理和修改
- 使用 Token 认证更加安全和便捷
- RSS 追更模式会获取最新的动画资源
- 季度月份只能是 1, 4, 7, 10（对应春夏秋冬四季）
- 自定义域名反代可以加速访问或绕过限制
- 配置文件中的设置优先级低于代码中直接传入的参数
