import asyncio
import json
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from ani2openlist import Ani2Openlist, Config
from ani2openlist.openlist.client import OpenlistClient, StorageUpdateUnconfirmedError
from ani2openlist.openlist.storage import OpenlistStorage
from ani2openlist.utils.http import HTTPClient, RequestUtils
from ani2openlist.utils.multiton import Multiton


class TestStorageWrite(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        Multiton.clear_instances()
        self.calls = []
        self.timeout_values = []
        self.persisted = None
        self.fail_write = False
        self.gateway = False
        self.mismatch = False
        self.fail_read = False
        self.storage = OpenlistStorage(
            id=7, driver="UrlTree", mount_path="/Anime",
            addition=json.dumps(
                {
                    "url_structure": "Show:\n  clip:12:1:https://media.example/a",
                    "head_size": True,
                }
            ),
        )
        self.http = HTTPClient()
        await self.http.close_async_client()
        self.http._HTTPClient__async_client = httpx.AsyncClient(
            transport=httpx.MockTransport(self.handle), trust_env=False,
        )
        with patch.object(OpenlistClient, "sync_api_me"), patch.object(
            RequestUtils, "get_client", return_value=self.http
        ):
            self.client = OpenlistClient("https://openlist.example", token="test-token")

    async def asyncTearDown(self):
        self.http.close_sync_client()
        await self.http.close_async_client()
        Multiton.clear_instances()

    def handle(self, request):
        self.calls.append((request.method, request.url.path))
        self.timeout_values.append(request.extensions["timeout"])
        if request.method == "POST":
            self.persisted = json.loads(request.content)
            if self.gateway:
                return httpx.Response(504)
            if self.fail_write:
                raise httpx.ReadTimeout("", request=request)
            return httpx.Response(200, json={"code": 200})
        if self.fail_read:
            raise httpx.ConnectError("private-error", request=request)
        actual = dict(self.persisted)
        # The upstream controls status/modified and serializes addition itself.
        actual.update(status="work", modified="2026-10-29T01:00:00Z")
        actual["addition"] = json.dumps(json.loads(actual["addition"]), indent=2)
        if self.mismatch:
            actual["addition"] = "{}"
        return httpx.Response(200, json={"code": 200, "data": actual})

    async def test_success_uses_dedicated_read_timeout_and_preserves_options(self):
        await self.client.async_api_admin_storage_update(self.storage)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(
            self.timeout_values[0],
            {"connect": 30, "read": 120, "write": 30, "pool": 30},
        )
        self.assertTrue(json.loads(self.persisted["addition"])["head_size"])

    async def test_saved_before_timeout_is_not_reposted_or_falsely_reported_ready(self):
        self.fail_write = True
        with self.assertRaisesRegex(StorageUpdateUnconfirmedError, "配置保存成功.*重载结果尚未确认") as caught:
            await self.client.async_api_admin_storage_update(self.storage)
        self.assertIsInstance(caught.exception.__cause__, httpx.ReadTimeout)
        self.assertEqual(
            self.calls,
            [
                ("POST", "/api/admin/storage/update"),
                ("GET", "/api/admin/storage/get"),
            ],
        )
        self.assertEqual(self.timeout_values[1]["read"], 30)

    async def test_unmatched_saved_data_and_failed_read_remain_unconfirmed(self):
        for mismatch, fail_read in ((True, False), (False, True)):
            with self.subTest(mismatch=mismatch):
                self.calls.clear()
                self.fail_write, self.mismatch, self.fail_read = True, mismatch, fail_read
                with self.assertRaisesRegex(StorageUpdateUnconfirmedError, "无法确认") as caught:
                    await self.client.async_api_admin_storage_update(self.storage)
                self.assertEqual(len(self.calls), 2)
                self.assertNotIn("private-error", str(caught.exception))

    async def test_gateway_timeout_also_reconciles_once(self):
        self.gateway = True
        with self.assertRaises(StorageUpdateUnconfirmedError):
            await self.client.async_api_admin_storage_update(self.storage)
        self.assertEqual(len(self.calls), 2)

    async def test_rejects_missing_storage_id_before_request(self):
        self.storage.id = 0
        with self.assertRaises(ValueError):
            await self.client.async_api_admin_storage_update(self.storage)
        self.assertEqual(self.calls, [])

    async def test_per_request_override_does_not_change_cached_default(self):
        with patch.object(RequestUtils, "get_client", return_value=self.http):
            for timeout in (httpx.Timeout(None, read=5), 2, None):
                response = await RequestUtils.post(
                    "https://solver.example/v1", json={}, timeout=timeout
                )
                self.assertEqual(response.status_code, 200)
            await RequestUtils.post("https://solver.example/v1", json={})
        self.assertEqual(self.timeout_values[-1]["read"], 30)
        self.assertIsNone(self.timeout_values[-2]["read"])


class TestSlowStorageServer(unittest.IsolatedAsyncioTestCase):
    async def test_slow_write_outlives_general_timeout_without_duplicate_post(self):
        received = []
        handlers = set()

        async def serve(reader, writer):
            task = asyncio.current_task()
            handlers.add(task)
            try:
                header = await reader.readuntil(b"\r\n\r\n")
                length = next(
                    int(line.split(b":", 1)[1])
                    for line in header.split(b"\r\n")
                    if line.lower().startswith(b"content-length:")
                )
                received.append(json.loads(await reader.readexactly(length)))
                await asyncio.sleep(0.2)
                body = b'{"code":200}'
                writer.write(
                    b"HTTP/1.1 200 OK\r\nContent-Length: "
                    + str(len(body)).encode()
                    + b"\r\nConnection: close\r\n\r\n"
                    + body
                )
                await writer.drain()
            finally:
                writer.close()
                await writer.wait_closed()
                handlers.discard(task)

        server = await asyncio.start_server(serve, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        Multiton.clear_instances()
        with patch.object(OpenlistClient, "sync_api_me"):
            client = OpenlistClient(
                f"http://127.0.0.1:{port}",
                token="test",
                http_timeout=0.05,
                storage_update_timeout=1,
            )
        http = client._OpenlistClient__client
        await http.close_async_client()
        http._HTTPClient__async_client = httpx.AsyncClient(trust_env=False)
        try:
            async with server:
                await client.async_api_admin_storage_update(OpenlistStorage(id=9, driver="UrlTree"))
                self.assertEqual(len(received), 1)
        finally:
            server.close()
            await server.wait_closed()
            if handlers:
                await asyncio.gather(*handlers)
            await RequestUtils.close_all_async_clients()
            Multiton.clear_instances()


class TestSyncAndConfiguration(unittest.IsolatedAsyncioTestCase):
    async def test_no_change_skips_write_and_changed_tree_retains_storage_options(self):
        with patch("ani2openlist.ani2openlist.OpenlistClient"):
            ani = Ani2Openlist()
        storage = OpenlistStorage(
            id=4,
            driver="UrlTree",
            addition=(
                '{"url_structure":"Show:\\n  a:1:1:https://media.example/a",'
                ' "head_size":true}'
            ),
        )
        ani.client.get_storage_by_mount_path = AsyncMock(return_value=storage)
        ani.client.async_api_admin_storage_update = AsyncMock()
        with patch.object(ani, "update_rss_anime_dict", new=AsyncMock()):
            await ani.run()
        ani.client.async_api_admin_storage_update.assert_not_awaited()

        async def add_item(tree):
            tree["new"] = ["2", "1", "https://media.example/new"]

        with patch.object(ani, "update_rss_anime_dict", new=add_item):
            await ani.run()
        ani.client.async_api_admin_storage_update.assert_awaited_once()
        self.assertTrue(storage.addition2dict["head_size"])
        self.assertIn("a:1:1:https://media.example/a", storage.addition2dict["url_structure"])

    def test_config_precedence_validation_and_webui_roundtrip(self):
        from webui.app import app
        with patch("ani2openlist.ani2openlist.OpenlistClient") as create:
            ani = Ani2Openlist(
                config=Config({"openlist": {"update_timeout": 180}}),
                storage_update_timeout=5,
            )
            self.assertEqual(create.call_args.kwargs["storage_update_timeout"], 180)
            create.reset_mock()
            for value in (None, True, 0, -1, "120", float("inf"), float("nan"), 10**400):
                with self.subTest(value_type=type(value).__name__):
                    with self.assertRaisesRegex(ValueError, "openlist.update_timeout"):
                        Ani2Openlist(config=Config({"openlist": {"update_timeout": value}}))
                    with patch("webui.app.open") as opened:
                        response = app.test_client().post(
                            "/api/config",
                            json={"openlist": {"update_timeout": value}},
                        )
                    self.assertEqual(response.status_code, 400)
                    opened.assert_not_called()
            create.assert_not_called()
        with patch("webui.app.open"), patch("webui.app.yaml.dump") as dump:
            response = app.test_client().post(
                "/api/config", json={"openlist": {"update_timeout": 180}}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(dump.call_args.args[0]["openlist"]["update_timeout"], 180)

    def test_config_page_exposes_update_timeout(self):
        from webui.app import app

        response = app.test_client().get("/config")
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="openlist_update_timeout"', html)
        self.assertIn("update_timeout: updateTimeout", html)
