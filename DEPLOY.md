# 🚀 GitHub 部署指南

## 📋 部署前检查清单

在推送到 GitHub 之前，请确认以下事项：

### ✅ 隐私保护

- [ ] 运行隐私检查脚本：`python check_privacy.py`
- [ ] 确认 `config.yaml` 不在 Git 跟踪中
- [ ] 确认 `webui/schedule.yaml` 不在 Git 跟踪中
- [ ] 检查所有代码中没有硬编码的密码、Token

### ✅ 文件准备

- [ ] 存在 `config.yaml.example` 模板文件
- [ ] 存在 `webui/schedule.yaml.example` 模板文件
- [ ] `.gitignore` 配置完整
- [ ] `README.md` 已更新
- [ ] `SECURITY.md` 安全说明已创建

---

## 🎯 首次部署步骤

### 1. 初始化 Git 仓库

```bash
# 初始化 Git
git init

# 添加所有文件（.gitignore 会自动排除敏感文件）
git add .

# 查看将要提交的文件
git status

# 确认 config.yaml 和 webui/schedule.yaml 不在列表中！
```

### 2. 创建首次提交

```bash
# 提交
git commit -m "Initial commit: Ani2Openlist with Web UI"
```

### 3. 连接到 GitHub

在 GitHub 上创建新仓库后：

```bash
# 添加远程仓库
git remote add origin https://github.com/你的用户名/ani2openlist.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

---

## 🔄 后续更新流程

### 每次推送前的检查

```bash
# 1. 运行隐私检查
python check_privacy.py

# 2. 查看修改
git status
git diff

# 3. 确认没有敏感信息后再提交
git add .
git commit -m "描述你的修改"
git push
```

---

## ⚠️ 紧急情况：误提交了敏感信息

如果不小心提交了密码或 Token：

### 方案 1: 修改最近一次提交（未 push）

```bash
# 从 Git 中移除敏感文件
git rm --cached config.yaml

# 修改提交
git commit --amend

# 如果已经 push，需要强制推送（危险！）
git push -f
```

### 方案 2: 已经 push 到 GitHub

1. **立即更改密码/Token**
2. 从 Git 历史中完全删除敏感信息：

```bash
# 使用 git filter-repo（推荐）
pip install git-filter-repo
git filter-repo --path config.yaml --invert-paths

# 强制推送
git push origin --force --all
```

3. **通知 GitHub**: 如果是私有仓库，可能需要联系 GitHub Support

### 方案 3: 重建仓库（最彻底）

如果历史记录已被污染：

```bash
# 1. 删除本地 .git
rm -rf .git

# 2. 清理敏感文件
rm config.yaml
cp config.yaml.example config.yaml

# 3. 重新初始化
git init
git add .
git commit -m "Clean initial commit"

# 4. 删除 GitHub 上的旧仓库，创建新仓库
# 5. 推送到新仓库
git remote add origin https://github.com/你的用户名/ani2openlist.git
git push -u origin main
```

---

## 📁 确保被忽略的文件

以下文件/目录应该在 `.gitignore` 中：

```gitignore
# 配置文件（包含敏感信息）
config.yaml
webui/schedule.yaml

# 日志文件
logs/
*.log

# Python
__pycache__/
*.pyc
*.pyo

# 虚拟环境
venv/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

---

## 🔍 验证部署

部署后，让其他人（或在另一台电脑）克隆仓库测试：

```bash
# 克隆仓库
git clone https://github.com/你的用户名/ani2openlist.git
cd ani2openlist

# 创建配置文件
cp config.yaml.example config.yaml
cp webui/schedule.yaml.example webui/schedule.yaml

# 编辑配置
nano config.yaml

# 安装依赖
pip install -r requirements.txt

# 运行测试
python test_setup.py

# 启动 Web UI
python webui_start.py
```

如果能正常运行，说明部署成功！

---

## 📊 GitHub 设置建议

### 1. 仓库设置

- **可见性**: 
  - 公开仓库：任何人可见
  - 私有仓库：仅你和协作者可见（推荐用于个人项目）

### 2. 分支保护

Settings → Branches → Add rule:

- Branch name pattern: `main`
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging

### 3. 安全警报

Settings → Security:

- ✅ Dependency graph
- ✅ Dependabot alerts
- ✅ Dependabot security updates

### 4. Secrets 管理

如果使用 GitHub Actions，在 Settings → Secrets 添加：

- `ALIST_URL`
- `ALIST_TOKEN`

**永远不要在代码中硬编码密钥！**

---

## 📝 README.md 建议

确保 README.md 包含：

1. **安全警告**：提醒用户不要提交 `config.yaml`
2. **配置说明**：详细的配置步骤
3. **示例截图**：Web UI 界面截图
4. **常见问题**：FAQ 部分
5. **贡献指南**：链接到 CONTRIBUTING.md
6. **许可证**：开源许可证声明

---

## 🎉 最后的话

**记住三个原则：**

1. 🔒 **永远不要提交敏感信息**
2. ✅ **推送前总是运行检查**
3. 🔄 **定期更新密码和 Token**

部署愉快！如有问题，请查看 [SECURITY.md](SECURITY.md) 或提交 issue。
