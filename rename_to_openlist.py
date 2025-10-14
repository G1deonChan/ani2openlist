"""
批量替换 openlist 为 openlist
保持配置结构和字段名不变
"""
import os
import re
from pathlib import Path

# 需要替换的文件类型
EXTENSIONS = ['.py', '.yaml', '.md', '.txt', '.html', '.css', '.sh', '.ps1']

# 需要跳过的目录
SKIP_DIRS = ['__pycache__', '.git', 'venv', 'env', '.venv', 'node_modules']

# 替换规则
REPLACEMENTS = [
    # 项目名称相关
    ('Ani2Openlist', 'Ani2Openlist'),
    ('ani2openlist', 'ani2openlist'),
    ('ANI2OPENLIST', 'ANI2OPENLIST'),
    
    # Openlist 服务名称（保留配置字段名为 openlist）
    ('Openlist 服务器', 'Openlist 服务器'),
    ('Openlist服务器', 'Openlist服务器'),
    ('Openlist 密码', 'Openlist 密码'),
    ('Openlist Token', 'Openlist Token'),
    ('Openlist 配置', 'Openlist 配置'),
    ('Openlist服务', 'Openlist服务'),
    
    # URL 相关
    ('openlist.', 'openlist.'),
    ('Openlist', 'Openlist'),
    
    # 特殊情况：GitHub 仓库名（但不替换 openlist-org）
]

# 不替换的模式
KEEP_PATTERNS = [
    r'openlist:',  # YAML 配置字段名
    r'openlist\.', # 配置对象属性
    r'config\.openlist', # 代码中的配置访问
    r'openlist_\w+', # HTML/JS 中的 ID 和变量名
    r'openlist-org', # Openlist 官方组织
]

def should_skip_line(line):
    """检查是否应该跳过这行"""
    for pattern in KEEP_PATTERNS:
        if re.search(pattern, line):
            return True
    return False

def replace_in_file(file_path):
    """替换文件中的内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 逐行处理
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            # 检查是否需要保留（配置字段名等）
            if should_skip_line(line):
                new_lines.append(line)
            else:
                # 执行替换
                new_line = line
                for old, new in REPLACEMENTS:
                    new_line = new_line.replace(old, new)
                new_lines.append(new_line)
        
        new_content = '\n'.join(new_lines)
        
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        return False
    except Exception as e:
        print(f"  ❌ 处理失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🔄 批量替换 Openlist → Openlist")
    print("=" * 60)
    print()
    
    modified_files = []
    skipped_files = []
    
    # 遍历所有文件
    for root, dirs, files in os.walk('.'):
        # 跳过特定目录
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for file in files:
            # 检查文件扩展名
            if not any(file.endswith(ext) for ext in EXTENSIONS):
                continue
            
            # 跳过示例配置文件（保留原样）
            if file.endswith('.example'):
                skipped_files.append(file)
                continue
            
            file_path = Path(root) / file
            rel_path = file_path.relative_to('.')
            
            print(f"处理: {rel_path}", end=' ... ')
            
            if replace_in_file(file_path):
                print("✅ 已修改")
                modified_files.append(str(rel_path))
            else:
                print("⏭️  无需修改")
    
    print()
    print("=" * 60)
    print(f"✅ 完成！共修改 {len(modified_files)} 个文件")
    print("=" * 60)
    
    if modified_files:
        print("\n修改的文件:")
        for f in modified_files[:20]:  # 只显示前20个
            print(f"  - {f}")
        if len(modified_files) > 20:
            print(f"  ... 还有 {len(modified_files) - 20} 个文件")
    
    if skipped_files:
        print(f"\n⏭️  跳过 {len(skipped_files)} 个示例文件（保持原样）")

if __name__ == '__main__':
    main()
