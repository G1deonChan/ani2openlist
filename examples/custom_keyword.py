"""
使用自定义关键字示例
"""

import asyncio
from ani2openlist import Ani2Openlist


async def main():
    # 使用自定义关键字搜索
    ani = Ani2Openlist(
        url="http://localhost:5244",
        username="admin",
        password="password",
        target_dir="/Anime",
        rss_update=False,
        key_word="2024-7"  # 自定义关键字
    )
    
    print("使用关键字 '2024-7' 搜索动画...")
    await ani.run()
    print("完成！")


if __name__ == "__main__":
    asyncio.run(main())
