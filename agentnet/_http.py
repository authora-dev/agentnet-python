"""HTTP client for AgentNet API -- sync and async variants."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from .errors import (
    AgentNetError,
    AuthenticationError,
    AuthorizationError,
    InsufficientFundsError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
)


class SyncHttpClient:
    """Synchronous HTTP client using urllib (zero dependencies)."""

    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def get(self, path: str, query: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, query=query)

    def post(self, path: str, body: Any = None, query: dict[str, Any] | None = None) -> Any:
        return self._request("POST", path, body=body, query=query)

    def put(self, path: str, body: Any = None) -> Any:
        return self._request("PUT", path, body=body)

    def delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    def _request(self, method: str, path: str, body: Any = None, query: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        if query:
            params = {k: str(v) for k, v in query.items() if v is not None}
            if params:
                url = f"{url}?{urlencode(params)}"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = None
        if body is not None and method != "GET":
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")

        req = Request(url, data=data, headers=headers, method=method)

        try:
            with urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                result = json.loads(raw) if raw else {}
                return self._unwrap(result)
        except HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            try:
                err_body = json.loads(body_text)
            except (json.JSONDecodeError, ValueError):
                err_body = {"message": body_text}
            self._throw_for_status(e.code, err_body, method, path)
        except URLError as e:
            if "timed out" in str(e.reason):
                raise TimeoutError(f"Request to {method} {path} timed out after {self.timeout}s")
            raise NetworkError(f"Request to {method} {path} failed: {e.reason}")

    def _unwrap(self, body: Any) -> Any:
        if isinstance(body, dict) and "data" in body:
            data = body["data"]
            if isinstance(data, list):
                pagination = body.get("pagination") or body.get("meta")
                if pagination:
                    return {"items": data, "total": pagination.get("total", len(data))}
                return {"items": data}
            return data
        return body

    def _throw_for_status(self, status: int, body: Any, method: str, path: str) -> None:
        parsed = self._parse_error(body)
        prefix = f"{method} {path}"

        if status == 401:
            raise AuthenticationError(parsed.get("message", f"{prefix}: Authentication failed"))
        elif status == 402:
            raise InsufficientFundsError(parsed.get("message", f"{prefix}: Insufficient funds"))
        elif status == 403:
            raise AuthorizationError(parsed.get("message", f"{prefix}: Forbidden"))
        elif status == 404:
            raise NotFoundError(parsed.get("message", f"{prefix}: Not found"))
        elif status == 429:
            raise RateLimitError(parsed.get("message", f"{prefix}: Rate limit exceeded"))
        else:
            raise AgentNetError(parsed.get("message", f"{prefix}: Status {status}"), status, parsed.get("code"))

    def _parse_error(self, body: Any) -> dict[str, Any]:
        if isinstance(body, dict):
            if "error" in body and isinstance(body["error"], dict):
                return body["error"]
            return body
        return {"message": str(body)}


class AsyncHttpClient:
    """Async HTTP client using aiohttp (optional dependency)."""

    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._session = None

    async def _get_session(self):
        if self._session is None or self._session.closed:
            try:
                import aiohttp
            except ImportError:
                raise ImportError("Install aiohttp for async support: pip install agentnet[async]")
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
            )
        return self._session

    async def get(self, path: str, query: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, query=query)

    async def post(self, path: str, body: Any = None) -> Any:
        return await self._request("POST", path, body=body)

    async def delete(self, path: str) -> Any:
        return await self._request("DELETE", path)

    async def _request(self, method: str, path: str, body: Any = None, query: dict[str, Any] | None = None) -> Any:
        session = await self._get_session()
        url = f"{self.base_url}{path}"
        kwargs: dict[str, Any] = {}
        if body is not None:
            kwargs["json"] = body
        if query:
            kwargs["params"] = {k: str(v) for k, v in query.items() if v is not None}

        async with session.request(method, url, **kwargs) as resp:
            if resp.content_type == "application/json":
                data = await resp.json()
            else:
                data = await resp.text()

            if resp.status >= 400:
                err = data if isinstance(data, dict) else {"message": str(data)}
                SyncHttpClient._throw_for_status(None, resp.status, err, method, path)  # type: ignore

            return SyncHttpClient._unwrap(None, data)  # type: ignore

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
