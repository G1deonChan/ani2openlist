"""
使用 Token 认证示例
"""

import asyncio
from ani2openlist import Ani2Openlist


async def main():
    # 使用 Openlist 永久 Token 而不是用户名密码
    ani = Ani2Openlist(
        url="http://localhost:5244",
        token="your-openlist-permanent-token-here",  # 从 Openlist 设置中获取
        target_dir="/Anime",
        rss_update=True
    )
    
    print("使用 Token 认证...")
    await ani.run()
    print("完成！")


if __name__ == "__main__":
    asyncio.run(main())
