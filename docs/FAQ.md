# FAQ - 常见问题

## 一般问题

### Q: ani2openlist 是什么?
A: ani2openlist 是一个用于从 Bangumi 同步动漫信息到 Openlist 的工具，可以自动整理和重命名动漫文件。

### Q: 需要什么前置条件?
A: 
- Python 3.8 或更高版本
- 一个运行中的 Openlist 实例
- Openlist API Token
- 可访问 Bangumi API

### Q: 支持哪些平台?
A: 支持 Windows、Linux 和 macOS。

## 安装问题

### Q: 如何安装 ani2openlist?
A: 使用 pip 安装:
```bash
pip install ani2openlist
```
或从源码安装:
```bash
git clone https://github.com/yourusername/ani2openlist.git
cd ani2openlist
pip install -e .
```

### Q: 安装时出现依赖错误怎么办?
A: 尝试升级 pip 并重新安装:
```bash
pip install --upgrade pip
pip install ani2openlist
```

## 配置问题

### Q: 如何获取 Openlist Token?
A: 
1. 登录 Openlist 管理界面
2. 进入"个人资料"页面
3. 复制 API Token

### Q: 配置文件在哪里?
A: 配置文件位于 `config/config.yaml`。首次使用请复制 `config/config.yaml.example` 并修改。

### Q: 如何配置多个 Openlist 实例?
A: 可以创建多个配置文件，使用时指定:
```python
config1 = load_config('config/openlist1.yaml')
config2 = load_config('config/openlist2.yaml')
```

## 使用问题

### Q: 搜索不到动漫怎么办?
A: 
1. 检查关键词是否正确
2. 尝试使用不同的关键词（日文名、英文名等）
3. 确认 Bangumi API 可访问

### Q: 文件整理失败?
A: 
1. 检查 Openlist Token 是否有效
2. 确认有相应路径的访问权限
3. 查看日志文件了解详细错误

### Q: 如何处理重名文件?
A: 在配置中设置处理策略:
```yaml
openlist:
  duplicate_strategy: skip  # skip, overwrite, rename
```

### Q: 支持哪些视频格式?
A: 默认支持 `.mkv`, `.mp4`, `.avi`, `.flv`, `.wmv` 等常见格式。可以在配置中自定义:
```yaml
ani:
  video_extensions:
    - .mkv
    - .mp4
    - .avi
```

## 性能问题

### Q: 处理速度慢怎么办?
A: 
1. 增加并发数（如果你的服务器支持）
2. 减小日志级别
3. 启用缓存
4. 使用更快的网络连接

### Q: 如何减少 API 请求?
A: 
1. 启用缓存
2. 增加 `rate_limit` 值
3. 批量处理而非逐个处理

## 错误处理

### Q: 出现 "Connection refused" 错误?
A: 
1. 检查 Openlist 服务是否运行
2. 确认 base_url 配置正确
3. 检查防火墙设置

### Q: 出现 "Unauthorized" 错误?
A: 
1. 检查 Token 是否正确
2. 确认 Token 是否过期
3. 重新生成 Token

### Q: 出现 "Rate limit exceeded" 错误?
A: 
1. 增加 `rate_limit` 配置值
2. 等待一段时间后重试
3. 减少并发请求数

### Q: 日志文件太大怎么办?
A: 在配置中设置日志轮转:
```yaml
log:
  rotation: "100 MB"
  retention: "30 days"
```

## 高级功能

### Q: 如何自定义文件名格式?
A: 在配置中设置:
```yaml
ani:
  filename_format: "{name} - S{season}E{episode}"
```

### Q: 如何过滤特定文件?
A: 使用文件过滤器:
```python
def my_filter(file_info):
    return file_info['size'] > 100 * 1024 * 1024  # 只处理大于100MB的文件

ani2openlist.organize(path, file_filter=my_filter)
```

### Q: 支持定时任务吗?
A: 可以配合 cron（Linux）或任务计划程序（Windows）使用:
```bash
# crontab -e
0 3 * * * /usr/bin/python /path/to/ani2openlist/cli.py organize /anime
```

### Q: 可以集成到其他程序吗?
A: 可以，ani2openlist 提供了完整的 Python API:
```python
from ani2openlist import Ani2Openlist

ani2openlist = Ani2Openlist(config)
# 在你的程序中使用
```

## 故障排查

### Q: 如何启用调试模式?
A: 在配置中设置:
```yaml
log:
  level: DEBUG
```

### Q: 如何查看详细日志?
A: 日志文件位于 `logs/ani2openlist.log`，可以使用:
```bash
tail -f logs/ani2openlist.log
```

### Q: 如何重置所有配置?
A: 删除 `config/config.yaml` 并重新复制示例文件:
```bash
rm config/config.yaml
cp config/config.yaml.example config/config.yaml
```

## 贡献和支持

### Q: 如何报告 Bug?
A: 在 GitHub 仓库创建 Issue，包含:
- 错误描述
- 复现步骤
- 环境信息
- 相关日志

### Q: 如何贡献代码?
A: 查看 CONTRIBUTING.md 了解详细信息。

### Q: 在哪里获取帮助?
A: 
- GitHub Issues
- 项目文档
- 社区讨论

### Q: 如何提交功能请求?
A: 在 GitHub 创建 Feature Request Issue，描述你的需求和用例。

## 许可证

### Q: ani2openlist 使用什么许可证?
A: MIT License，可以自由使用、修改和分发。

### Q: 可以商用吗?
A: 可以，MIT License 允许商业使用。
