#!/usr/bin/env python3
"""
快速开始脚本
"""
import asyncio
from ani2openlist import Ani2Openlist, load_config, load_config_or_default


async def main():
    """主函数"""
    print("=== ani2openlist 快速开始 ===\n")
    
    # 加载配置
    print("1. 加载配置...")
    try:
        config = load_config('config.yaml')
        print("   ✓ 配置加载成功")
    except FileNotFoundError:
        print("   ✗ 配置文件不存在，请复制 config.yaml.example 并修改为 config.yaml")
        print("   使用默认配置继续...")
        config = load_config_or_default()
    
    # 创建实例
    print("2. 创建 ani2openlist 实例...")
    try:
        ani = Ani2Openlist(config=config)
        print("   ✓ 实例创建成功")
    except Exception as e:
        print(f"   ✗ 实例创建失败: {e}")
        return
    
    # 运行更新
    print("\n3. 开始更新...")
    try:
        await ani.run()
        print("   ✓ 更新完成")
    except Exception as e:
        print(f"   ✗ 更新失败: {e}")
        import traceback
        traceback.print_exc()
        print(f"   ✗ 连接失败: {e}")
    
    print("\n=== 快速开始完成 ===")
    print("\n接下来你可以:")
    
    print("\n=== 下一步 ===")
    print("  1. 查看 examples/ 目录了解更多使用方法")
    print("  2. 查看 docs/USAGE.md 了解详细文档")
    print("  3. 运行 python cli.py --help 查看命令行选项")


if __name__ == '__main__':
    asyncio.run(main())
