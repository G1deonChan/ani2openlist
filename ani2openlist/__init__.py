"""
Ani2Openlist - 将 ANI Open 的视频通过文件树的方式挂载到 Openlist上
"""

from ani2openlist.ani2openlist import Ani2Openlist
from ani2openlist.core import Config, load_config, load_config_or_default

__version__ = "1.0.0"
__all__ = ["Ani2Openlist", "Config", "load_config", "load_config_or_default"]
