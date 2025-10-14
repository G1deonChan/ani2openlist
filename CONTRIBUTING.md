# 贡献指南

感谢你考虑为 ani2openlist 做出贡献！

## 如何贡献

### 报告 Bug

如果你发现了 bug，请创建一个 issue 并包含以下信息：

- 问题的简短描述
- 复现步骤
- 期望的行为
- 实际的行为
- 环境信息（操作系统、Python 版本等）

### 提交功能请求

如果你有新功能的想法，请创建一个 issue 并描述：

- 功能的用例
- 为什么这个功能有用
- 可能的实现方案

### 提交代码

1. Fork 这个仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 使用有意义的变量和函数名
- 添加适当的注释和文档字符串
- 确保所有测试通过
- 保持代码简洁和可读

### 测试

在提交 PR 之前，请确保：

```bash
# 运行测试
pytest tests/

# 检查代码风格
flake8 app/

# 格式化代码
black app/
```

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/ani2openlist.git
cd ani2openlist

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -e ".[dev]"
```

## 发布流程

1. 更新版本号（`setup.py` 和 `app/__init__.py`）
2. 更新 CHANGELOG.md
3. 创建 git tag
4. 推送到 GitHub
5. 创建 Release

## 行为准则

请注意，这个项目采用了贡献者公约。参与此项目即表示你同意遵守其条款。

## 问题？

如果你有任何问题，请随时创建 issue 或联系维护者。

感谢你的贡献！
