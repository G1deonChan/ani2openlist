"""
配置管理模块
"""
from typing import Any
from pathlib import Path
import yaml


class Config:
    """配置类"""

    def __init__(self, config_dict: dict[str, Any] | None = None):
        """
        初始化配置对象

        :param config_dict: 配置字典
        """
        self._config = config_dict or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        :param key: 配置键，支持点号分隔的多级键（如 "openlist.url"）
        :param default: 默认值
        :return: 配置值
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def get_all(self) -> dict[str, Any]:
        """
        获取所有配置

        :return: 配置字典
        """
        return self._config.copy()

    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return self.get(key)

    def __contains__(self, key: str) -> bool:
        """支持 in 操作符"""
        return self.get(key) is not None


def load_config(config_path: str | Path) -> Config:
    """
    从 YAML 文件加载配置

    :param config_path: 配置文件路径
    :return: Config 对象
    :raises FileNotFoundError: 配置文件不存在
    :raises yaml.YAMLError: 配置文件格式错误
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config_dict = yaml.safe_load(f)

    if config_dict is None:
        config_dict = {}

    return Config(config_dict)


def load_config_or_default(config_path: str | Path | None = None) -> Config:
    """
    加载配置文件，如果文件不存在则返回默认配置

    :param config_path: 配置文件路径
    :return: Config 对象
    """
    if config_path is None:
        return Config()

    try:
        return load_config(config_path)
    except FileNotFoundError:
        return Config()
