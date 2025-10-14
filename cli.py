"""
命令行入口
"""
import sys
import asyncio
import argparse
from ani2openlist import Ani2Openlist, load_config, load_config_or_default


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='ani2openlist - 将 ANI Open 的视频挂载到 Openlist'
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='配置文件路径 (默认: config.yaml)'
    )
    
    parser.add_argument(
        '--url',
        help='Openlist 服务器地址 (覆盖配置文件)'
    )
    
    parser.add_argument(
        '--username',
        help='Openlist 用户名 (覆盖配置文件)'
    )
    
    parser.add_argument(
        '--password',
        help='Openlist 密码 (覆盖配置文件)'
    )
    
    parser.add_argument(
        '--token',
        help='Openlist Token (覆盖配置文件)'
    )
    
    parser.add_argument(
        '--target-dir',
        help='挂载目录 (覆盖配置文件)'
    )
    
    parser.add_argument(
        '--rss',
        action='store_true',
        help='使用 RSS 追更'
    )
    
    parser.add_argument(
        '--year',
        type=int,
        help='动画年份'
    )
    
    parser.add_argument(
        '--month',
        type=int,
        help='动画季度 (1/4/7/10)'
    )
    
    parser.add_argument(
        '--keyword',
        help='自定义关键字'
    )
    
    args = parser.parse_args()
    
    try:
        # 加载配置文件
        config = load_config_or_default(args.config)
        
        # 构建参数字典（命令行参数优先）
        kwargs = {}
        
        if args.url:
            kwargs['url'] = args.url
        if args.username:
            kwargs['username'] = args.username
        if args.password:
            kwargs['password'] = args.password
        if args.token:
            kwargs['token'] = args.token
        if args.target_dir:
            kwargs['target_dir'] = args.target_dir
        if args.rss:
            kwargs['rss_update'] = True
        if args.year:
            kwargs['year'] = args.year
        if args.month:
            kwargs['month'] = args.month
        if args.keyword:
            kwargs['key_word'] = args.keyword
        
        # 创建实例（命令行参数会覆盖配置文件）
        if kwargs:
            # 如果有命令行参数，先从配置获取默认值，再用命令行参数覆盖
            ani = Ani2Openlist(config=config, **kwargs)
        else:
            # 如果没有命令行参数，直接使用配置
            ani = Ani2Openlist(config=config)
        
        # 运行
        asyncio.run(ani.run())
        
        return 0
        
    except FileNotFoundError as e:
        print(f"错误: 配置文件不存在 - {e}")
        print(f"请创建配置文件或使用命令行参数")
        return 1
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
