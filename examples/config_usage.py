#!/usr/bin/env python3
"""
使用配置文件的示例
"""
import asyncio
from ani2openlist import Ani2Openlist, load_config


async def main():
    """主函数"""
    # 从配置文件加载配置
    config = load_config("config.yaml")
    
    # 使用配置创建实例
    ani = Ani2Openlist(config=config)
    
    # 运行更新
    await ani.run()


if __name__ == "__main__":
    asyncio.run(main())
