"""
基本使用示例 - 使用 RSS 追更最新番剧
"""

import asyncio
from ani2openlist import Ani2Openlist


async def main():
    # 创建 Ani2Openlist 实例，使用 RSS 追更最新番剧
    ani = Ani2Openlist(
        url="http://localhost:5244",  # Openlist 服务器地址
        username="admin",              # Openlist 用户名
        password="password",           # Openlist 密码
        target_dir="/Anime",           # 挂载到 Openlist 的目录
        rss_update=True                # 使用 RSS 追更
    )
    
    print("开始从 ANI Open RSS 获取最新动画...")
    await ani.run()
    print("完成！")


if __name__ == "__main__":
    asyncio.run(main())
