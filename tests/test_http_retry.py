"""HTTP 层重试行为测试。

覆盖回归问题：重试次数耗尽后，旧实现会返回 ``None``，调用方随即抛出
``'NoneType' object has no attribute 'status_code'``，掩盖了真实的网络错误。
"""
import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from ani2openlist.utils.http import HTTPClient, RequestUtils
from ani2openlist.utils.retry import Retry


class TestRetryDecorator(unittest.TestCase):
    """重试装饰器在耗尽重试后必须抛出异常，而不是返回 None。"""

    def setUp(self):
        # 避免测试真正等待退避时间
        self._sleep_patches = [
            patch("ani2openlist.utils.retry.sleep"),
            patch("ani2openlist.utils.retry.async_sleep", new=AsyncMock()),
        ]
        for patcher in self._sleep_patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_sync_retry_reraises_instead_of_returning_none(self):
        calls = []

        @Retry.sync_retry(ValueError, tries=3, delay=0, backoff=1)
        def always_fails():
            calls.append(1)
            raise ValueError("boom")

        with self.assertRaises(ValueError):
            always_fails()

        self.assertEqual(len(calls), 3, "应按 tries 次数重试")

    def test_async_retry_reraises_instead_of_returning_none(self):
        calls = []

        @Retry.async_retry(ValueError, tries=2, delay=0, backoff=1)
        async def always_fails():
            calls.append(1)
            raise ValueError("boom")

        with self.assertRaises(ValueError):
            asyncio.run(always_fails())

        self.assertEqual(len(calls), 2)

    def test_sync_retry_returns_result_when_attempt_succeeds(self):
        attempts = {"n": 0}

        @Retry.sync_retry(ValueError, tries=3, delay=0, backoff=1)
        def flaky():
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise ValueError("temporary")
            return "ok"

        self.assertEqual(flaky(), "ok")
        self.assertEqual(attempts["n"], 3)

    def test_async_retry_returns_result_when_attempt_succeeds(self):
        attempts = {"n": 0}

        @Retry.async_retry(ValueError, tries=3, delay=0, backoff=1)
        async def flaky():
            attempts["n"] += 1
            if attempts["n"] < 2:
                raise ValueError("temporary")
            return "ok"

        self.assertEqual(asyncio.run(flaky()), "ok")

    def test_retry_rejects_non_positive_tries(self):
        with self.assertRaises(ValueError):
            Retry.sync_retry(ValueError, tries=0)

        with self.assertRaises(ValueError):
            Retry.async_retry(ValueError, tries=0)


class TestHTTPClientNeverReturnsNone(unittest.TestCase):
    """真实网络错误应向上抛出，且绝不能返回 None。"""

    def setUp(self):
        self._sleep_patches = [
            patch("ani2openlist.utils.retry.sleep"),
            patch("ani2openlist.utils.retry.async_sleep", new=AsyncMock()),
        ]
        for patcher in self._sleep_patches:
            patcher.start()
            self.addCleanup(patcher.stop)

        self.client = HTTPClient()
        self.addCleanup(self.client.close_sync_client)

        async def _close():
            await self.client.close_async_client()

        self.addCleanup(lambda: asyncio.run(_close()))

    def test_async_request_raises_transport_error_not_attribute_error(self):
        with patch.object(
            httpx.AsyncClient, "request", new=AsyncMock(side_effect=httpx.ConnectError("boom"))
        ):
            with self.assertRaises(httpx.ConnectError):
                asyncio.run(self.client._async_request("get", "https://example.invalid"))

    def test_async_request_raises_on_timeout_instead_of_returning_none(self):
        with patch.object(
            httpx.AsyncClient, "request", new=AsyncMock(side_effect=httpx.ReadTimeout("slow"))
        ):
            with self.assertRaises(httpx.TimeoutException):
                asyncio.run(self.client._async_request("get", "https://example.invalid"))

    def test_sync_request_raises_transport_error_not_attribute_error(self):
        with patch.object(
            httpx.Client, "request", side_effect=httpx.ConnectError("boom")
        ):
            with self.assertRaises(httpx.ConnectError):
                self.client._sync_request("get", "https://example.invalid")

    def test_async_request_returns_usable_response_on_success(self):
        response = httpx.Response(200, text="ok", request=httpx.Request("GET", "https://example.com"))

        with patch.object(httpx.AsyncClient, "request", new=AsyncMock(return_value=response)):
            resp = asyncio.run(self.client._async_request("get", "https://example.com"))

        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 200)

    def test_request_utils_get_wraps_client_without_returning_none(self):
        response = httpx.Response(200, text="ok", request=httpx.Request("GET", "https://example.com"))
        client = RequestUtils.get_client()

        with patch.object(httpx.AsyncClient, "request", new=AsyncMock(return_value=response)):
            resp = asyncio.run(RequestUtils.get("https://example.com"))

        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 200)

        asyncio.run(RequestUtils.close_all_async_clients())
        client.close_sync_client()


if __name__ == "__main__":
    unittest.main()
