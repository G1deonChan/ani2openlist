#!/usr/bin/env python3
"""
快速运行脚本
使用配置文件运行 ani2openlist
"""
import asyncio
from ani2openlist import Ani2Openlist, load_config


async def main():
    """主函数"""
    print("正在启动 ani2openlist...")
    print("-" * 50)
    
    try:
        # 加载配置
        config = load_config("config.yaml")
        print(f"✓ 配置加载成功")
        print(f"  Openlist: {config.get('openlist.url')}")
        print(f"  目标: {config.get('openlist.target_dir')}")
        print(f"  模式: {'RSS 追更' if config.get('ani.rss_update') else '手动指定'}")
        print("-" * 50)
        
        # 创建实例
        ani = Ani2Openlist(config=config)
        
        # 运行
        print("\n开始更新...\n")
        await ani.run()
        
        print("\n" + "-" * 50)
        print("✓ 更新完成！")
        print("-" * 50)
        
    except FileNotFoundError:
        print("✗ 错误: 找不到配置文件 config.yaml")
        print("\n请先运行: python test_setup.py")
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
