import math
from typing import Any, Literal, overload
from collections.abc import Coroutine
from urllib.parse import urlsplit, urlunsplit
from weakref import WeakSet

from httpx import (
    AsyncClient,
    Client,
    Request,
    Response,
    Timeout,
    TimeoutException,
    TransportError,
)

from ani2openlist.utils.url import URLUtils
from ani2openlist.utils.retry import Retry


DEFAULT_TIMEOUT = 30.0


def validate_timeout(value: Any) -> float:
    """Return a finite, positive timeout in seconds."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("http.timeout 必须是大于 0 的有限秒数")
    timeout = float(value)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("http.timeout 必须是大于 0 的有限秒数")
    return timeout


def _safe_request_url(url: str) -> str:
    """Keep enough context for diagnosis without logging credentials or queries."""
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    try:
        if parsed.port is not None:
            host = f"{host}:{parsed.port}"
    except ValueError:
        pass
    return urlunsplit((parsed.scheme, host, parsed.path, "", ""))


def _timeout_description(timeout: Any) -> str:
    if isinstance(timeout, Timeout):
        values = timeout.as_dict()
        return ", ".join(f"{name}={value:g} 秒" for name, value in values.items())
    if timeout is None:
        return "未设置时限"
    return f"{timeout:g} 秒"


def _timeout_error(error: TimeoutException, method: str, url: str, timeout: Any) -> TimeoutException:
    message = (
        f"HTTP 请求超时：{type(error).__name__}，{method.upper()} "
        f"{_safe_request_url(url)}，超时设置：{_timeout_description(timeout)}"
    )
    try:
        request = error.request
    except RuntimeError:
        request = Request(method, _safe_request_url(url))
    return type(error)(message, request=request)


class HTTPClient:
    """
    HTTP 客户端类
    """

    # 默认请求头
    HEADERS: dict[str, str] = {
        "User-Agent": "Ani2Openlist/1.2.0",
        "Accept": "application/json",
    }

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        """
        初始化 HTTP 客户端
        """

        self.timeout = validate_timeout(timeout)
        self.__new_async_client()
        self.__new_sync_client()

    def __new_sync_client(self):
        """
        创建新的同步 HTTP 客户端
        """
        self.__sync_client = Client(http2=True, follow_redirects=True, timeout=self.timeout)

    def __new_async_client(self):
        """
        创建新的异步 HTTP 客户端
        """
        self.__async_client = AsyncClient(http2=True, follow_redirects=True, timeout=self.timeout)

    def close_sync_client(self) -> None:
        """
        关闭同步 HTTP 客户端
        """
        if self.__sync_client:
            self.__sync_client.close()

    async def close_async_client(self) -> None:
        """
        关闭异步 HTTP 客户端
        """
        if self.__async_client:
            await self.__async_client.aclose()

    @Retry.sync_retry(TransportError, tries=3, delay=1, backoff=2)
    def _sync_request(self, method: str, url: str, **kwargs) -> Response:
        """
        发起同步 HTTP 请求

        重试耗尽后会抛出异常，不会返回 None
        """
        try:
            return self.__sync_client.request(method, url, **kwargs)
        except TimeoutException as e:
            self.close_sync_client()
            self.__new_sync_client()
            raise _timeout_error(e, method, url, kwargs.get("timeout", self.timeout)) from e

    @Retry.async_retry(TransportError, tries=3, delay=1, backoff=2)
    async def _async_request(self, method: str, url: str, **kwargs) -> Response:
        """
        发起异步 HTTP 请求

        重试耗尽后会抛出异常，不会返回 None
        """
        try:
            return await self.__async_client.request(method, url, **kwargs)
        except TimeoutException as e:
            await self.close_async_client()
            self.__new_async_client()
            raise _timeout_error(e, method, url, kwargs.get("timeout", self.timeout)) from e

    @overload
    def request(
        self, method: str, url: str, *, sync: Literal[True], **kwargs
    ) -> Response: ...

    @overload
    def request(
        self, method: str, url: str, *, sync: Literal[False] = False, **kwargs
    ) -> Coroutine[Any, Any, Response]: ...

    def request(
        self,
        method: str,
        url: str,
        *,
        sync: Literal[True, False] = False,
        **kwargs,
    ) -> Response | Coroutine[Any, Any, Response]:
        """
        发起 HTTP 请求

        :param method: HTTP 方法，如 get, post, put 等
        :param url: 请求的 URL
        :param sync: 是否使用同步请求方式，默认为 False
        :param kwargs: 其他请求参数，如 headers, cookies 等
        :return: HTTP 响应对象
        """
        headers = kwargs.get("headers", self.HEADERS)
        kwargs["headers"] = headers
        if sync:
            return self._sync_request(method, url, **kwargs)
        else:
            return self._async_request(method, url, **kwargs)

    @overload
    def get(self, url: str, *, sync: Literal[True], **kwargs) -> Response: ...

    @overload
    def get(
        self, url: str, *, sync: Literal[False], **kwargs
    ) -> Coroutine[Any, Any, Response]: ...

    def get(
        self,
        url: str,
        *,
        sync: Literal[True, False] = False,
        params: dict = {},
        **kwargs,
    ) -> Response | Coroutine[Any, Any, Response]:
        """
        发送 GET 请求

        :param url: 请求的 URL
        :param sync: 是否使用同步请求方式，默认为 False
        :param params: 请求的查询参数
        :param kwargs: 其他请求参数，如 headers, cookies 等
        :return: HTTP 响应对象
        """
        return self.request("get", url, sync=sync, params=params, **kwargs)

    @overload
    def post(self, url: str, *, sync: Literal[True], **kwargs) -> Response: ...

    @overload
    def post(
        self, url: str, *, sync: Literal[False], **kwargs
    ) -> Coroutine[Any, Any, Response]: ...

    def post(
        self,
        url: str,
        *,
        sync: Literal[True, False] = False,
        data: Any = None,
        json: dict = {},
        **kwargs,
    ) -> Response | Coroutine[Any, Any, Response]:
        """
        发送 POST 请求

        :param url: 请求的 URL
        :param sync: 是否使用同步请求方式，默认为 False
        :param data: 请求的数据
        :param json: 请求的 JSON 数据
        :param kwargs: 其他请求参数，如 headers, cookies 等
        :return: HTTP 响应对象
        """
        return self.request("post", url, sync=sync, data=data, json=json, **kwargs)


class RequestUtils:
    """
    HTTP 请求工具类
    支持同步和异步请求
    """

    __clients: dict[str, HTTPClient] = {}
    __client_list: WeakSet[HTTPClient] = WeakSet()

    @classmethod
    def get_client(cls, url: str = "", timeout: float | None = None) -> HTTPClient:
        """
        获取 HTTP 客户端

        :param url: 请求的 URL
        :return: HTTP 客户端
        """

        if url:
            _, domain, port = URLUtils.get_resolve_url(url)
            key = f"{domain}:{port}"
            if key not in cls.__clients:
                cls.__clients[key] = HTTPClient(
                    DEFAULT_TIMEOUT if timeout is None else timeout
                )
            elif timeout is not None:
                # Refresh only when a caller explicitly supplies a timeout.
                cls.__clients[key].timeout = validate_timeout(timeout)
            return cls.__clients[key]

        client = HTTPClient(DEFAULT_TIMEOUT if timeout is None else timeout)
        cls.__client_list.add(client)
        return client

    @overload
    @classmethod
    def request(
        cls, method: str, url: str, sync: Literal[True], **kwargs
    ) -> Response: ...

    @overload
    @classmethod
    def request(
        cls, method: str, url: str, sync: Literal[False] = False, **kwargs
    ) -> Coroutine[Any, Any, Response]: ...

    @classmethod
    def request(
        cls, method: str, url: str, sync: Literal[True, False] = False, **kwargs
    ) -> Response | Coroutine[Any, Any, Response]:
        """
        发起 HTTP 请求
        """
        client = cls.get_client(url, timeout=kwargs.get("timeout"))
        return client.request(method, url, sync=sync, **kwargs)

    @overload
    @classmethod
    def get(cls, url: str, *, sync: Literal[True], **kwargs) -> Response: ...

    @overload
    @classmethod
    def get(
        cls, url: str, *, sync: Literal[False] = False, **kwargs
    ) -> Coroutine[Any, Any, Response]: ...

    @classmethod
    def get(
        cls,
        url: str,
        *,
        sync: Literal[True, False] = False,
        params: dict = {},
        **kwargs,
    ) -> Response | Coroutine[Any, Any, Response]:
        """
        发送 GET 请求

        :param url: 请求的 URL
        :param params: 请求的查询参数
        :param kwargs: 其他请求参数，如 headers, cookies 等
        :return: HTTP 响应对象
        """
        return cls.request("get", url, sync=sync, params=params, **kwargs)

    @overload
    @classmethod
    def post(cls, url: str, *, sync: Literal[True], **kwargs) -> Response: ...

    @overload
    @classmethod
    def post(
        cls,
        url: str,
        *,
        sync: Literal[False] = False,
        data: Any = None,
        json: dict = {},
        **kwargs,
    ) -> Coroutine[Any, Any, Response]: ...

    @classmethod
    def post(
        cls,
        url: str,
        *,
        sync: Literal[True, False] = False,
        data: Any = None,
        json: dict = {},
        **kwargs,
    ) -> Response | Coroutine[Any, Any, Response]:
        """
        发送 POST 请求

        :param url: 请求的 URL
        :param data: 请求的数据
        :param json: 请求的 JSON 数据
        :param kwargs: 其他请求参数，如 headers, cookies 等
        :return: HTTP 响应对象
        """
        return cls.request("post", url, sync=sync, data=data, json=json, **kwargs)
    
    @classmethod
    async def close_all_async_clients(cls) -> None:
        """
        关闭所有 HTTP 客户端并清除缓存
        用于清理资源，防止事件循环关闭时出现警告
        下次调用 get_client() 时会自动创建新的客户端
        """
        # 同步客户端没有绑定事件循环，也在这里一起关闭。
        for client in cls.__clients.values():
            try:
                client.close_sync_client()
                await client.close_async_client()
            except Exception:
                pass
        
        # 清除缓存，下次会创建新的客户端
        cls.__clients.clear()
        
        # 关闭弱引用集合中的客户端
        for client in list(cls.__client_list):
            try:
                client.close_sync_client()
                await client.close_async_client()
            except Exception:
                pass
