"""
部署前隐私检查脚本
检查项目中是否包含敏感信息
"""
import os
import re
import sys
from pathlib import Path

# 敏感信息模式（排除示例和文档中的占位符）
SENSITIVE_PATTERNS = [
    # 真实密码（排除示例）
    (r'password\s*[:=]\s*["\'](?!your_password|password|admin|my_password|your-password)[^"\']{6,}["\']', '真实密码'),
    # 真实 Token（排除示例）
    (r'token\s*[:=]\s*["\'](?!your_token|your-openlist-permanent-token-here|your_openlist_token_here|"")[a-zA-Z0-9_-]{32,}["\']', '真实 Token'),
    # 真实内网 IP（排除示例 IP）
    (r'\b(?:(?:10|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)\.(?:\d{1,3}\.){2})(?!1\.100|0\.1)\d{1,3}\b', '内网 IP 地址'),
]

# 需要检查的文件
CHECK_FILES = [
    'config.yaml',
    'webui/schedule.yaml',
    'README.md',
    'docs/*.md',
    '*.py',
]

# 应该被忽略的文件
SHOULD_BE_IGNORED = [
    'config.yaml',
    'webui/schedule.yaml',
    'logs/',
]

def check_gitignore():
    """检查 .gitignore 是否包含敏感文件"""
    print("🔍 检查 .gitignore...")
    
    gitignore_path = Path('.gitignore')
    if not gitignore_path.exists():
        print("  ❌ .gitignore 文件不存在！")
        return False
    
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        gitignore_content = f.read()
    
    missing = []
    for item in SHOULD_BE_IGNORED:
        if item not in gitignore_content:
            missing.append(item)
    
    if missing:
        print(f"  ⚠️  以下文件/目录应该添加到 .gitignore:")
        for item in missing:
            print(f"     - {item}")
        return False
    
    print("  ✅ .gitignore 配置正确")
    return True


def check_file_content(file_path):
    """检查文件内容是否包含敏感信息"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return []
    
    findings = []
    for pattern, description in SENSITIVE_PATTERNS:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            findings.append({
                'file': str(file_path),
                'line': line_num,
                'type': description,
                'text': match.group(0)[:50]  # 只显示前50个字符
            })
    
    return findings


def check_sensitive_info():
    """检查敏感信息"""
    print("\n🔍 检查敏感信息...")
    
    all_findings = []
    
    # 检查所有 Python 文件
    for py_file in Path('.').rglob('*.py'):
        if '__pycache__' in str(py_file) or 'venv' in str(py_file):
            continue
        findings = check_file_content(py_file)
        all_findings.extend(findings)
    
    # 检查 Markdown 文件
    for md_file in Path('.').rglob('*.md'):
        if 'venv' in str(md_file):
            continue
        findings = check_file_content(md_file)
        all_findings.extend(findings)
    
    if all_findings:
        print(f"  ⚠️  发现 {len(all_findings)} 处潜在敏感信息:")
        for finding in all_findings:
            print(f"\n     文件: {finding['file']}")
            print(f"     行号: {finding['line']}")
            print(f"     类型: {finding['type']}")
            print(f"     内容: {finding['text']}...")
        return False
    
    print("  ✅ 未发现明显的敏感信息")
    return True


def check_config_files():
    """检查配置文件是否存在且不在 Git 中"""
    print("\n🔍 检查配置文件...")
    
    config_path = Path('config.yaml')
    example_path = Path('config.yaml.example')
    
    if not example_path.exists():
        print("  ❌ config.yaml.example 不存在！")
        return False
    
    if config_path.exists():
        print("  ⚠️  config.yaml 存在，请确保它在 .gitignore 中")
        # 检查是否在 git 中
        if os.system('git ls-files --error-unmatch config.yaml > nul 2>&1') == 0:
            print("  ❌ config.yaml 已被 Git 跟踪！请立即移除:")
            print("     git rm --cached config.yaml")
            return False
    
    print("  ✅ 配置文件检查通过")
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("🔒 Ani2Openlist 部署前隐私检查")
    print("=" * 60)
    
    checks = [
        check_gitignore(),
        check_config_files(),
        check_sensitive_info(),
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ 所有检查通过！可以安全地推送到 GitHub")
        print("=" * 60)
        return 0
    else:
        print("❌ 发现问题，请先修复后再推送")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
