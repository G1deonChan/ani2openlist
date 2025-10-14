"""
配置日志示例
"""

import asyncio
import logging
from ani2openlist import Ani2Openlist
from ani2openlist.core import setup_logger


async def main():
    # 配置日志 - 输出到控制台和文件
    setup_logger(
        level=logging.DEBUG,  # 日志级别
        log_file="ani2openlist.log"  # 日志文件路径
    )
    
    ani = Ani2Openlist(
        url="http://localhost:5244",
        username="admin",
        password="password",
        target_dir="/Anime",
        rss_update=True
    )
    
    print("开始运行（详细日志已启用）...")
    await ani.run()
    print("完成！查看 ani2openlist.log 文件获取详细日志")


if __name__ == "__main__":
    asyncio.run(main())
