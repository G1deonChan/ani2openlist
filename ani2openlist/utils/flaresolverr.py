"""Read ANI directories inside a FlareSolverr browser session."""

import json
from html.parser import HTMLParser
from uuid import uuid4

from httpx import URL

from ani2openlist.core.logger import logger
from ani2openlist.utils.http import RequestUtils


class _PreText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_pre = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "pre":
            self.in_pre = True

    def handle_endtag(self, tag):
        if tag == "pre":
            self.in_pre = False

    def handle_data(self, data):
        if self.in_pre:
            self.parts.append(data)


def parse_directory(body: str) -> dict:
    try:
        data = json.loads(body)
    except (ValueError, TypeError):
        parser = _PreText()
        parser.feed(body)
        try:
            data = json.loads("".join(parser.parts))
        except ValueError:
            raise ValueError("ANI did not return directory JSON; challenge or unsupported POST") from None
    if not isinstance(data, dict) or not isinstance(data.get("files"), list):
        raise ValueError("ANI directory response must contain a files list")
    return data


class FlareSolverrDirectory:
    def __init__(self, endpoint: str, timeout_ms: int = 60000):
        endpoint = endpoint.strip().rstrip("/")
        url = URL(endpoint)
        if url.scheme not in ("http", "https") or not url.host or url.query or url.fragment:
            raise ValueError("FlareSolverr URL must be an HTTP(S) base URL or /v1 endpoint")
        if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int) or timeout_ms < 1000:
            raise ValueError("FlareSolverr timeout must be an integer >= 1000 milliseconds")
        self.endpoint = endpoint if url.path.endswith("/v1") else endpoint + "/v1"
        self.timeout_ms = timeout_ms
        self.session = "ani2openlist-" + uuid4().hex

    async def _command(self, cmd: str, **kwargs) -> dict:
        response = await RequestUtils.post(
            self.endpoint,
            json={"cmd": cmd, "session": self.session, "maxTimeout": self.timeout_ms, **kwargs},
            timeout=self.timeout_ms / 1000 + 15,
        )
        if response.is_error:
            try:
                error = response.json()
                message = str(error.get("message", "")).lower() if isinstance(error, dict) else ""
            except ValueError:
                message = ""
            if "timeout" in message:
                raise RuntimeError(
                    f"FlareSolverr {cmd} timed out after {self.timeout_ms} ms; "
                    "source access or challenge resolution did not complete"
                )
            if "captcha" in message:
                raise RuntimeError(f"FlareSolverr {cmd} could not resolve the CAPTCHA")
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict) or result.get("status") != "ok":
            # Solver messages can contain upstream content or cookies.
            raise RuntimeError(f"FlareSolverr {cmd} failed; inspect the service logs")
        return result

    async def __aenter__(self):
        try:
            await self._command("sessions.create")
        except BaseException:
            await self.__aexit__(None, None, None)
            raise
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        try:
            await self._command("sessions.destroy")
        except Exception:
            logger.warning("Could not close FlareSolverr session; check the service")

    async def warmup(self, url: str):
        await self._command("request.get", url=url)

    async def directory(self, url: str) -> dict:
        result = await self._command("request.post", url=url, postData="")
        solution = result.get("solution")
        if not isinstance(solution, dict) or solution.get("status") != 200:
            raise RuntimeError("FlareSolverr upstream directory request failed")
        body = solution.get("response")
        if not isinstance(body, str):
            raise ValueError("FlareSolverr response body is missing")
        # Selenium may report 200 even for an error page; validate the body too.
        return parse_directory(body)
