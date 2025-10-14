#!/usr/bin/env python3
"""
启动 Web UI
"""
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from webui.app import app, setup_scheduler, add_log

if __name__ == '__main__':
    print('=' * 60)
    print('🎬 Ani2Openlist Web UI')
    print('=' * 60)
    print()
    print('正在启动 Web 服务器...')
    print()
    print('访问地址：')
    print('  - 本地访问: http://localhost:5000')
    print('  - 局域网访问: http://您的IP:5000')
    print()
    print('按 Ctrl+C 停止服务')
    print('=' * 60)
    print()
    
    # 初始化定时任务
    setup_scheduler()
    add_log('Web UI 已启动', 'success')
    
    # 启动 Flask 应用
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print('\n\n正在关闭服务器...')
        add_log('Web UI 已关闭', 'info')
