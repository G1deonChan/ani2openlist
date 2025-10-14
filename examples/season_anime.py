"""
按季度获取动画示例
"""

import asyncio
from ani2openlist import Ani2Openlist


async def main():
    # 获取 2024 年 10 月（秋季）的动画
    ani = Ani2Openlist(
        url="http://localhost:5244",
        username="admin",
        password="password",
        target_dir="/Anime",
        rss_update=False,  # 不使用 RSS
        year=2024,         # 年份
        month=10           # 月份（季度：1, 4, 7, 10）
    )
    
    print("获取 2024 年 10 月（秋季）的动画...")
    await ani.run()
    print("完成！")


if __name__ == "__main__":
    asyncio.run(main())
