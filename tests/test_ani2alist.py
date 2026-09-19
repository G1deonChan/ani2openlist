"""Ani2Openlist 的基础行为测试。"""
import unittest
from unittest.mock import patch

from ani2openlist import Ani2Openlist, Config


class TestAni2Openlist(unittest.TestCase):
    """Ani2Openlist 初始化和配置测试。"""

    @staticmethod
    def make_config() -> Config:
        return Config(
            {
                "openlist": {
                    "url": "http://localhost:5244",
                    "token": "test_token",
                    "target_dir": "/anime/",
                },
                "ani": {"rss_update": True},
            }
        )

    @patch("ani2openlist.ani2openlist.OpenlistClient")
    def test_init_uses_config_and_normalizes_target_dir(self, mock_openlist_client):
        """配置对象应覆盖默认值，目标目录只保留一个前导斜杠。"""
        ani2openlist = Ani2Openlist(config=self.make_config())

        mock_openlist_client.assert_called_once_with(
            "http://localhost:5244", "", "", "test_token"
        )
        self.assertEqual(ani2openlist._Ani2Openlist__target_dir, "/anime")

    @patch("ani2openlist.ani2openlist.OpenlistClient")
    def test_explicit_arguments_work_without_config(self, mock_openlist_client):
        """不使用配置对象时应保留显式构造参数。"""
        Ani2Openlist(
            url="https://openlist.example",
            username="user",
            password="password",
            target_dir="/media/anime",
            rss_update=False,
            year=2024,
            month=10,
        )

        mock_openlist_client.assert_called_once_with(
            "https://openlist.example", "user", "password", ""
        )


class TestConfig(unittest.TestCase):
    """点号路径配置读取测试。"""

    def test_nested_value_and_default(self):
        config = Config({"openlist": {"url": "http://localhost"}})

        self.assertEqual(config.get("openlist.url"), "http://localhost")
        self.assertEqual(config.get("openlist.token", "fallback"), "fallback")
        self.assertEqual(config.get("missing.value", "fallback"), "fallback")


if __name__ == '__main__':
    unittest.main()
