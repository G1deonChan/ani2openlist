"""
ani2openlist 模块测试
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from app.modules.ani2openlist import Ani2Openlist


class TestAni2Openlist(unittest.TestCase):
    """Ani2Openlist 测试类"""

    def setUp(self):
        """测试前准备"""
        self.config = {
            'ani': {
                'base_url': 'https://api.bgm.tv',
                'enable': True
            },
            'openlist': {
                'base_url': 'http://localhost:5244',
                'token': 'test_token',
                'root_path': '/anime'
            }
        }

    @patch('app.modules.ani2openlist.ani2openlist.OpenlistClient')
    def test_init(self, mock_openlist_client):
        """测试初始化"""
        ani2openlist = Ani2Openlist(self.config)
        self.assertIsNotNone(ani2openlist)
        mock_openlist_client.assert_called_once()

    @patch('app.modules.ani2openlist.ani2openlist.OpenlistClient')
    @patch('app.modules.ani2openlist.ani2openlist.HttpClient')
    def test_search_anime(self, mock_http_client, mock_openlist_client):
        """测试搜索动漫"""
        # Mock HTTP 响应
        mock_response = {
            'list': [
                {
                    'id': 12345,
                    'name': '测试动漫',
                    'name_cn': '测试动漫中文名',
                    'type': 2
                }
            ]
        }
        
        mock_http_instance = Mock()
        mock_http_instance.get.return_value = mock_response
        mock_http_client.return_value = mock_http_instance

        ani2openlist = Ani2Openlist(self.config)
        results = ani2openlist.search('测试动漫')
        
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)

    @patch('app.modules.ani2openlist.ani2openlist.OpenlistClient')
    def test_organize_files(self, mock_openlist_client):
        """测试文件整理"""
        mock_openlist_instance = Mock()
        mock_openlist_client.return_value = mock_openlist_instance

        ani2openlist = Ani2Openlist(self.config)
        
        # Mock list_files 返回值
        mock_openlist_instance.list_files.return_value = [
            {'name': 'test.mkv', 'is_dir': False}
        ]

        # 测试整理功能
        result = ani2openlist.organize('/test/path')
        self.assertIsNotNone(result)


class TestAni2OpenlistIntegration(unittest.TestCase):
    """集成测试"""

    def setUp(self):
        """测试前准备"""
        self.config = {
            'ani': {
                'base_url': 'https://api.bgm.tv',
                'enable': True
            },
            'openlist': {
                'base_url': 'http://localhost:5244',
                'token': 'test_token',
                'root_path': '/anime'
            }
        }

    @patch('app.modules.ani2openlist.ani2openlist.OpenlistClient')
    @patch('app.modules.ani2openlist.ani2openlist.HttpClient')
    def test_full_workflow(self, mock_http_client, mock_openlist_client):
        """测试完整工作流程"""
        # Mock 所有必要的响应
        mock_http_instance = Mock()
        mock_http_client.return_value = mock_http_instance
        
        mock_openlist_instance = Mock()
        mock_openlist_client.return_value = mock_openlist_instance

        ani2openlist = Ani2Openlist(self.config)
        
        # 这里可以测试完整的工作流程
        self.assertIsNotNone(ani2openlist)


if __name__ == '__main__':
    unittest.main()
