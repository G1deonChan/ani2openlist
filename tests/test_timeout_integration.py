import asyncio
import threading
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from ani2openlist import Ani2Openlist, Config
from ani2openlist.openlist.client import OpenlistClient
from ani2openlist.utils.http import RequestUtils
from webui.app import app, run_ani2openlist_async, task_status


class TestTimeoutIntegration(unittest.TestCase):
    def setUp(self):
        asyncio.run(RequestUtils.close_all_async_clients())

    def tearDown(self):
        asyncio.run(RequestUtils.close_all_async_clients())

    @patch("ani2openlist.ani2openlist.OpenlistClient")
    def test_config_is_validated_before_openlist_network_access(self, client):
        for value in (True, 0, -1, float("inf"), float("nan"), "30", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Ani2Openlist(config=Config({"http": {"timeout": value}}))
        client.assert_not_called()

    @patch("ani2openlist.ani2openlist.OpenlistClient")
    def test_config_and_explicit_timeouts_are_passed_to_rss_and_openlist(self, client):
        config = Config({"ani": {"rss_domain": "rss.example"}, "http": {"timeout": 45}})
        ani = Ani2Openlist(config=config)
        client.assert_called_once_with(
            "http://localhost:5244", "", "", "", http_timeout=45.0, storage_update_timeout=120.0
        )
        response = httpx.Response(200, text="<rss></rss>")
        with patch(
            "ani2openlist.ani2openlist.RequestUtils.get", new=AsyncMock(return_value=response)
        ) as get:
            asyncio.run(ani.update_rss_anime_dict({}))
        get.assert_awaited_once_with("https://rss.example/ani-download.xml", timeout=45.0)

    def test_openlist_reuses_configured_client_and_explicit_timeout(self):
        response = MagicMock(status_code=200)
        response.json.return_value = {"code": 200, "data": {"base_path": "/", "id": 1}}
        private_client = MagicMock(timeout=12)
        private_client.get.return_value = response
        private_client.post.return_value = response
        list_response = MagicMock(status_code=200)
        list_response.json.return_value = {
            "code": 200,
            "data": {"total": 0, "content": []},
        }
        private_client.request = AsyncMock(return_value=list_response)
        with patch(
            "ani2openlist.openlist.client.RequestUtils.get_client",
            return_value=private_client,
        ) as get_client:
            client = OpenlistClient("http://openlist.invalid", token="token", http_timeout=12)
            client.sync_api_me()
            asyncio.run(client.async_api_fs_list("/"))
        get_client.assert_called_once_with(timeout=12.0)
        self.assertEqual(private_client.get.call_count, 2)
        self.assertEqual(private_client.post.call_count, 0)
        private_client.request.assert_awaited_once()
        self.assertEqual(private_client.request.await_args.args[:2], ("post", "http://openlist.invalid/api/fs/list"))
        for call in (
            private_client.get.call_args_list[0],
            private_client.get.call_args_list[1],
            private_client.request.await_args,
        ):
            self.assertEqual(call.kwargs["timeout"], 12)

    def test_cached_client_updates_only_for_explicit_timeout(self):
        first = RequestUtils.get_client("https://rss.example", timeout=12)
        same = RequestUtils.get_client("https://rss.example")
        self.assertIs(same, first)
        self.assertEqual(same.timeout, 12)
        updated = RequestUtils.get_client("https://rss.example", timeout=45)
        self.assertIs(updated, first)
        self.assertEqual(updated.timeout, 45)

    def test_cleanup_closes_sync_and_async_clients(self):
        client = RequestUtils.get_client("https://rss.example")
        with (
            patch.object(client, "close_sync_client") as close_sync,
            patch.object(client, "close_async_client", new=AsyncMock()) as close_async,
        ):
            asyncio.run(RequestUtils.close_all_async_clients())
        close_sync.assert_called_once_with()
        close_async.assert_awaited_once_with()

    @patch("ani2openlist.ani2openlist.OpenlistClient")
    def test_rss_failure_does_not_update_storage(self, client):
        ani = Ani2Openlist(config=Config({"http": {"timeout": 1}}))
        storage = MagicMock(driver="UrlTree")
        storage.addition2dict = {"url_structure": ""}
        ani.client.get_storage_by_mount_path = AsyncMock(return_value=storage)
        ani.client.async_api_admin_storage_update = AsyncMock()
        with patch(
            "ani2openlist.ani2openlist.RequestUtils.get",
            new=AsyncMock(side_effect=httpx.ReadTimeout("")),
        ):
            with self.assertRaises(httpx.ReadTimeout):
                asyncio.run(ani.run())
        ani.client.async_api_admin_storage_update.assert_not_awaited()


class TestWebUITimeout(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_invalid_timeout_does_not_write_config(self):
        for value in (True, 0, -1, "invalid", None, 1e999):
            with self.subTest(value=value), patch("webui.app.open") as opened:
                response = self.client.post(
                    "/api/config", json={"openlist": {}, "http": {"timeout": value}}
                )
                self.assertEqual(response.status_code, 400)
                opened.assert_not_called()

    def test_valid_timeout_is_saved(self):
        output = None

        def dump(data, _file, **_kwargs):
            nonlocal output
            output = data

        with patch("webui.app.open"), patch("webui.app.yaml.dump", side_effect=dump):
            response = self.client.post(
                "/api/config", json={"openlist": {}, "http": {"timeout": 45}}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(output["http"]["timeout"], 45.0)

    @patch("webui.app.CONFIG_PATH")
    @patch("webui.app.RequestUtils.close_all_async_clients", new=AsyncMock())
    def test_failed_async_task_is_cleaned_up_and_reports_error(self, _config):
        with patch("webui.app.Ani2Openlist") as ani:
            ani.return_value.run = AsyncMock(side_effect=httpx.ReadTimeout("slow"))
            result = asyncio.run(run_ani2openlist_async())
        self.assertFalse(result["success"])
        self.assertIn("任务执行失败", result["message"])

    def test_task_thread_releases_running_state_after_failure(self):
        with patch("webui.app.asyncio.DefaultEventLoopPolicy") as policy:
            policy.return_value.new_event_loop.side_effect = RuntimeError("loop failed")
            task_status["running"] = False
            run_started = threading.Event()
            with patch("webui.app.threading.Thread") as thread:
                thread.return_value.start.side_effect = run_started.set
                from webui.app import run_ani2openlist

                run_ani2openlist()
                target = thread.call_args.kwargs["target"]
                target()
            self.assertTrue(run_started.is_set())
        self.assertFalse(task_status["running"])
        self.assertFalse(task_status["last_result"]["success"])


if __name__ == "__main__":
    unittest.main()
