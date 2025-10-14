# 🔐 安全说明

## 重要提示

本项目涉及敏感信息的处理，使用前请仔细阅读以下安全建议。

## ⚠️ 配置文件安全

### 不要提交敏感信息到 Git

以下文件包含敏感信息，**绝不应该**提交到 Git 仓库：

- `config.yaml` - 包含 Openlist 密码/Token
- `webui/schedule.yaml` - 可能包含敏感配置
- `logs/*.log` - 可能包含运行日志

这些文件已在 `.gitignore` 中配置，请不要强制提交。

### 首次使用

1. 复制配置模板：
   ```bash
   cp config.yaml.example config.yaml
   cp webui/schedule.yaml.example webui/schedule.yaml
   ```

2. 编辑 `config.yaml`，填写你的实际配置：
   - Openlist 服务器地址
   - 用户名/密码 或 Token
   - 目标目录

3. **检查配置文件权限**（Linux/Mac）：
   ```bash
   chmod 600 config.yaml
   ```

## 🔑 认证方式

### Token 认证（推荐）

Token 认证比用户名密码更安全：

```yaml
openlist:
  url: "https://your-openlist-server.com"
  token: "your_openlist_token_here"
  username: ""  # 留空
  password: ""  # 留空
```

### 用户名密码认证

如果必须使用密码：

```yaml
openlist:
  url: "https://your-openlist-server.com"
  username: "your_username"
  password: "your_password"
  token: ""  # 留空
```

## 🌐 Web UI 安全

### 开发环境

Web UI 默认运行在开发模式，仅适合本地使用：

```bash
python webui_start.py
# 访问: http://localhost:5000
```

### 生产环境

**⚠️ 重要**: 不要将 Web UI 直接暴露到公网！

如需远程访问，请使用以下方案之一：

#### 方案 1: SSH 隧道（推荐）

```bash
# 在远程服务器上运行
python webui_start.py

# 在本地电脑上建立隧道
ssh -L 5000:localhost:5000 user@remote-server
# 然后访问 http://localhost:5000
```

#### 方案 2: VPN

使用 WireGuard、OpenVPN 等 VPN 方案，仅在内网访问。

#### 方案 3: 反向代理 + 认证

如必须公网访问，使用 Nginx 反向代理并配置：

1. **HTTPS** (使用 Let's Encrypt)
2. **HTTP Basic Auth** 或其他认证方式
3. **IP 白名单**
4. **速率限制**

Nginx 配置示例：

```nginx
server {
    listen 443 ssl http2;
    server_name ani2openlist.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Basic Auth
    auth_basic "Ani2Openlist Admin";
    auth_basic_user_file /path/to/.htpasswd;
    
    # IP 限制（可选）
    allow 192.168.1.0/24;
    deny all;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔒 环境变量（可选）

为了更好的安全性，可以使用环境变量存储敏感信息：

```bash
# Linux/Mac
export ALIST_URL="https://your-openlist-server.com"
export ALIST_TOKEN="your_token_here"

# Windows PowerShell
$env:ALIST_URL="https://your-openlist-server.com"
$env:ALIST_TOKEN="your_token_here"
```

然后修改代码读取环境变量（需要自行实现）。

## 📝 日志安全

日志文件可能包含敏感信息：

1. 定期清理日志
2. 不要分享日志文件
3. 如需提交 issue，清理日志中的敏感信息

## 🐛 报告安全问题

如发现安全漏洞，请**不要**公开提交 issue。

请发送邮件到项目维护者（见 README.md），我们会尽快处理。

## ✅ 安全检查清单

部署前请确认：

- [ ] `config.yaml` 不在 Git 版本控制中
- [ ] 密码强度足够（如使用密码认证）
- [ ] Web UI 不暴露在公网（或已配置安全措施）
- [ ] 定期更新依赖包（`pip install -U -r requirements.txt`）
- [ ] 日志文件权限正确
- [ ] 使用 HTTPS（如需远程访问）

## 📚 延伸阅读

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security](https://flask.palletsprojects.com/en/latest/security/)
- [Python Security Best Practices](https://snyk.io/blog/python-security-best-practices/)

---

**记住：安全是一个持续的过程，不是一次性的配置！**
