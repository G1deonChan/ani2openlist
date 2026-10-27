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


class TestHTTPTimeout(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = HTTPClient()
        for patcher in (
            patch("ani2openlist.utils.retry.sleep"),
            patch("ani2openlist.utils.retry.async_sleep", new=AsyncMock()),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    async def asyncTearDown(self):
        self.client.close_sync_client()
        await self.client.close_async_client()

    def assert_timeout_context(self, error, expected_type):
        self.assertIsInstance(error, expected_type)
        self.assertIsInstance(error.__cause__, expected_type)
        message = str(error)
        self.assertIn(expected_type.__name__, message)
        self.assertIn("GET https://example.invalid/ani-download.xml", message)
        self.assertIn("超时设置：30 秒", message)
        self.assertNotIn("private-token", message)
        self.assertNotIn("user:private-password", message)
        self.assertEqual(
            error.request.url,
            "https://example.invalid/ani-download.xml",
        )

    async def test_async_empty_timeout_keeps_type_and_safe_context(self):
        for exception_type in (
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.PoolTimeout,
        ):
            with self.subTest(exception_type=exception_type):
                with patch.object(
                    httpx.AsyncClient,
                    "request",
                    new=AsyncMock(side_effect=exception_type("")),
                ):
                    with self.assertRaises(exception_type) as caught:
                        await self.client.get(
                            "https://user:private-password@example.invalid/ani-download.xml"
                            "?private-token=secret"
                        )
                self.assert_timeout_context(caught.exception, exception_type)

    def test_sync_empty_timeout_keeps_type_and_safe_context(self):
        with patch.object(httpx.Client, "request", side_effect=httpx.ReadTimeout("")):
            with self.assertRaises(httpx.ReadTimeout) as caught:
                self.client.get(
                    "https://user:private-password@example.invalid/ani-download.xml"
                    "?private-token=secret",
                    sync=True,
                )
        self.assert_timeout_context(caught.exception, httpx.ReadTimeout)

    async def test_existing_request_object_is_preserved(self):
        request = httpx.Request(
            "GET", "https://example.invalid/feed?private-token=secret"
        )
        with patch.object(
            httpx.AsyncClient,
            "request",
            new=AsyncMock(side_effect=httpx.ReadTimeout("", request=request)),
        ):
            with self.assertRaises(httpx.ReadTimeout) as caught:
                await self.client.get("https://example.invalid/feed?private-token=secret")
        self.assertIs(caught.exception.request, request)
        self.assertNotIn("private-token", str(caught.exception))

    async def test_default_custom_and_per_request_timeout(self):
        response = httpx.Response(200, request=httpx.Request("GET", "https://example.com"))
        default_client = HTTPClient()
        self.addAsyncCleanup(default_client.close_async_client)
        self.addCleanup(default_client.close_sync_client)
        self.assertEqual(default_client.timeout, 30.0)
        with patch.object(httpx.AsyncClient, "request", new=AsyncMock(return_value=response)):
            await default_client.get("https://example.com")
            self.assertNotIn("timeout", httpx.AsyncClient.request.await_args.kwargs)

            await self.client.get("https://example.com", timeout=0.5)
            self.assertEqual(httpx.AsyncClient.request.await_args.kwargs["timeout"], 0.5)

    def test_timeout_validation(self):
        for value in (True, False, 0, -1, float("inf"), float("nan"), "30", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                HTTPClient(value)

    async def test_retry_logs_attempt_numbers_and_preserves_backoff(self):
        sleeps = []

        async def capture_sleep(delay):
            sleeps.append(delay)

        with (
            patch("ani2openlist.utils.retry.async_sleep", new=capture_sleep),
            patch.object(
                httpx.AsyncClient,
                "request",
                new=AsyncMock(side_effect=httpx.ReadTimeout("")),
            ),
            self.assertLogs("ani2openlist", level="WARNING") as logs,
        ):
            with self.assertRaises(httpx.ReadTimeout):
                await self.client.get("https://example.invalid")
        self.assertEqual(sleeps, [2, 4])
        self.assertIn("第 1/3 次请求失败", logs.output[0])
        self.assertIn("第 2/3 次请求失败", logs.output[1])
        self.assertIn("第 3/3 次请求失败", logs.output[-1])


if __name__ == "__main__":
    unittest.main()
