import json
import unittest
from html import escape
from unittest.mock import AsyncMock, patch

import httpx

from ani2openlist import Ani2Openlist, Config
from ani2openlist.utils.flaresolverr import FlareSolverrDirectory, parse_directory


def response(data):
    return httpx.Response(200, json=data, request=httpx.Request("POST", "http://solver/v1"))


class TestDirectoryParsing(unittest.TestCase):
    def test_raw_and_browser_wrapped_json(self):
        data = {"files": [{"name": "A & B <episode>.mp4"}]}
        raw = json.dumps(data)
        self.assertEqual(parse_directory(raw), data)
        self.assertEqual(parse_directory('<html><body><pre style="x">' + escape(raw) + '</pre></body></html>'), data)

    def test_challenge_or_invalid_schema_is_not_empty_success(self):
        for body in ('<html>Just a moment...</html>', '{}', '{"files": {}}', '[]'):
            with self.subTest(body=body), self.assertRaises(ValueError):
                parse_directory(body)

    def test_endpoint_and_timeout_validation(self):
        for url in ('http://solver:8191', 'http://solver:8191/v1/'):
            self.assertEqual(FlareSolverrDirectory(url).endpoint, 'http://solver:8191/v1')
        for timeout in (0, True, '60000'):
            with self.assertRaises(ValueError):
                FlareSolverrDirectory('http://solver', timeout)


class TestFlareSolverrScan(unittest.IsolatedAsyncioTestCase):
    @patch('ani2openlist.ani2openlist.OpenlistClient')
    async def test_recursive_scan_reuses_session_and_resource_links(self, _client):
        folder = {"name": "Nested", "mimeType": "application/vnd.google-apps.folder"}
        video = {"name": "A & B.mp4", "mimeType": "video/mp4", "size": "123",
                 "createdTime": "2024-10-01T00:00:00.000Z"}
        def solved(files):
            return response({"status": "ok", "solution": {"status": 200,
                "response": '<html><pre>' + escape(json.dumps({"files": files})) + '</pre></html>'}})
        responses = [response({"status": "ok"}), response({"status": "ok"}),
                     solved([folder]), solved([video]), response({"status": "ok"})]
        config = Config({"ani": {"rss_update": False, "year": 2024, "month": 10,
            "src_domain": "source.example", "resource_domain": "resources.example",
            "flaresolverr_url": "http://solver:8191", "flaresolverr_timeout": 90000}})
        with patch('ani2openlist.utils.flaresolverr.RequestUtils.post', new=AsyncMock(side_effect=responses)) as post:
            ani = Ani2Openlist(config=config)
            tree = {}
            await ani.update_season_anime_dict(tree)
        calls = post.call_args_list
        commands = [c.kwargs['json'] for c in calls]
        self.assertEqual([c['cmd'] for c in commands],
                         ['sessions.create', 'request.get', 'request.post', 'request.post', 'sessions.destroy'])
        self.assertEqual(len({c['session'] for c in commands}), 1)
        self.assertEqual(commands[2]['url'], 'https://source.example/2024-10/')
        self.assertEqual(commands[3]['postData'], '')
        self.assertEqual(calls[2].kwargs['timeout'], 105)
        self.assertEqual(tree['2024-10']['Nested']['A & B.mp4'][2],
                         'https://resources.example/2024-10/Nested/A%20&%20B.mp4?d=true')

    async def test_session_destroyed_on_invalid_directory(self):
        responses = [response({"status": "ok"}),
                     response({"status": "ok", "solution": {"status": 200, "response": '<html>challenge</html>'}}),
                     response({"status": "ok"})]
        with patch('ani2openlist.utils.flaresolverr.RequestUtils.post', new=AsyncMock(side_effect=responses)) as post:
            with self.assertRaises(ValueError):
                async with FlareSolverrDirectory('http://solver') as solver:
                    await solver.directory('https://source.example/2024-10/')
        self.assertEqual(post.call_args.kwargs['json']['cmd'], 'sessions.destroy')

    async def test_solver_failure_is_explicit(self):
        with patch('ani2openlist.utils.flaresolverr.RequestUtils.post', new=AsyncMock(return_value=response({"status": "error"}))):
            with self.assertRaises(RuntimeError):
                await FlareSolverrDirectory('http://solver').warmup('https://source.example/')

    async def test_solver_http_timeout_has_safe_actionable_error(self):
        failed = httpx.Response(500, json={"status": "error",
            "message": "Error solving challenge. Timeout after 60 seconds. private-value"},
            request=httpx.Request("POST", "http://solver/v1"))
        with patch('ani2openlist.utils.flaresolverr.RequestUtils.post', new=AsyncMock(return_value=failed)):
            with self.assertRaisesRegex(RuntimeError, 'timed out after 60000 ms') as caught:
                await FlareSolverrDirectory('http://solver').warmup('https://source.example/')
        self.assertNotIn('private-value', str(caught.exception))

    @patch('ani2openlist.ani2openlist.OpenlistClient')
    async def test_disabled_keeps_direct_request(self, _client):
        with patch('ani2openlist.ani2openlist.RequestUtils.post', new=AsyncMock(return_value=response({"files": []}))) as post:
            await Ani2Openlist(rss_update=False, year=2024, month=10).update_season_anime_dict({})
        self.assertEqual(post.await_count, 1)
        self.assertNotIn('json', post.call_args.kwargs)
