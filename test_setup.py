#!/usr/bin/env python3
"""
配置文件测试脚本
测试配置文件是否正确，并验证与 Openlist 的连接
"""
import asyncio
import sys
from ani2openlist import Ani2Openlist, load_config
from ani2openlist.core.logger import logger


async def test_config():
    """测试配置文件"""
    print("=" * 60)
    print("ani2openlist 配置测试")
    print("=" * 60)
    
    # 1. 加载配置文件
    print("\n[1/4] 加载配置文件...")
    try:
        config = load_config("config.yaml")
        print("✓ 配置文件加载成功")
        
        # 显示配置信息（隐藏敏感信息）
        print("\n配置信息：")
        print(f"  - Openlist URL: {config.get('openlist.url')}")
        print(f"  - 用户名: {config.get('openlist.username')}")
        print(f"  - 目标目录: {config.get('openlist.target_dir')}")
        print(f"  - RSS 追更: {config.get('ani.rss_update')}")
        print(f"  - 源域名: {config.get('ani.src_domain')}")
        print(f"  - RSS 域名: {config.get('ani.rss_domain')}")
        print(f"  - 日志级别: {config.get('logging.level')}")
    except FileNotFoundError as e:
        print(f"✗ 配置文件不存在: {e}")
        return False
    except Exception as e:
        print(f"✗ 配置文件加载失败: {e}")
        return False
    
    # 2. 创建 Ani2Openlist 实例
    print("\n[2/4] 创建 Ani2Openlist 实例...")
    try:
        ani = Ani2Openlist(config=config)
        print("✓ 实例创建成功")
    except Exception as e:
        print(f"✗ 实例创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 测试 Openlist 连接
    print("\n[3/4] 测试 Openlist 服务器连接...")
    try:
        # 尝试登录
        if config.get('openlist.token'):
            print("  使用 Token 认证...")
        else:
            print("  使用用户名密码认证...")
        
        # 测试获取存储列表（这会触发登录）
        storages = await ani.client.async_api_admin_storage_list()
        print(f"✓ 连接成功！找到 {len(storages)} 个存储")
        
        # 显示存储信息
        if storages:
            print("\n  存储列表：")
            for storage in storages[:5]:  # 只显示前5个
                print(f"    - {storage.mount_path} ({storage.driver})")
            if len(storages) > 5:
                print(f"    ... 还有 {len(storages) - 5} 个存储")
    except Exception as e:
        print(f"✗ Openlist 连接失败: {e}")
        print("\n  请检查：")
        print("    1. Openlist URL 是否正确")
        print("    2. 用户名和密码是否正确")
        print("    3. Openlist 服务是否正在运行")
        print("    4. 网络连接是否正常")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 测试目标目录
    print(f"\n[4/4] 检查目标目录 '{config.get('openlist.target_dir')}'...")
    try:
        target_dir = config.get('openlist.target_dir')
        storage = await ani.client.get_storage_by_mount_path(
            mount_path=target_dir,
            create=False
        )
        
        if storage:
            print(f"✓ 目标目录已存在")
            print(f"  - 挂载路径: {storage.mount_path}")
            print(f"  - 驱动类型: {storage.driver}")
            print(f"  - 状态: {'启用' if storage.disabled == False else '禁用'}")
        else:
            print(f"⚠ 目标目录不存在（运行时会自动创建）")
    except Exception as e:
        print(f"⚠ 无法检查目标目录: {e}")
    
    print("\n" + "=" * 60)
    print("✓ 所有测试通过！配置正确，可以正常使用。")
    print("=" * 60)
    
    print("\n下一步：")
    print("  1. 运行主程序: python cli.py")
    print("  2. 查看帮助: python cli.py --help")
    print("  3. 使用示例: python examples/config_usage.py")
    
    return True


async def main():
    """主函数"""
    try:
        success = await test_config()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
