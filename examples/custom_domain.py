"""
使用自定义域名反代示例
"""

import asyncio
from ani2openlist import Ani2Openlist


async def main():
    # 使用自己的反代域名
    ani = Ani2Openlist(
        url="http://localhost:5244",
        username="admin",
        password="password",
        target_dir="/Anime",
        rss_update=True,
        src_domain="your-aniopen-proxy.com",  # ANI Open 资源反代域名
        rss_domain="your-rss-proxy.com"       # RSS 订阅反代域名
    )
    
    print("使用自定义反代域名...")
    await ani.run()
    print("完成！")


if __name__ == "__main__":
    asyncio.run(main())
