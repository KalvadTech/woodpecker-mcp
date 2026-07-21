from __future__ import annotations

from contextvars import ContextVar, Token
from types import TracebackType
from typing import Any

import httpx

from . import __version__ as _version
from .errors import WoodpeckerError

_DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0)
_DEFAULT_PER_PAGE = 50
_MAX_PER_PAGE = 100


class WoodpeckerClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout: httpx.Timeout = _DEFAULT_TIMEOUT,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            follow_redirects=False,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "User-Agent": f"woodpecker-mcp/{_version}",
            },
            transport=transport,
        )

    @property
    def base_url(self) -> str:
        return self._base_url

    def _url(self, path: str) -> str:
        return f"/api{path}"

    async def __aenter__(self) -> WoodpeckerClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self._json("GET", path, params=params)

    async def post_json(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return await self._json("POST", path, json=json, params=params)

    async def delete(self, path: str, params: dict[str, Any] | None = None) -> None:
        resp = await self._client.delete(self._url(path), params=_clean_params(params))
        _raise_for_status(resp)

    async def paginate(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        page: int = 1,
        per_page: int = _DEFAULT_PER_PAGE,
    ) -> dict[str, Any]:
        merged = dict(params or {})
        merged["page"] = page
        merged["perPage"] = min(per_page, _MAX_PER_PAGE)
        data = await self.get_json(path, params=merged)
        if isinstance(data, list):
            return {
                "items": data,
                "page": page,
                "per_page": merged["perPage"],
            }
        return {
            "items": data,
            "page": page,
            "per_page": merged["perPage"],
        }

    async def _json(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        resp = await self._client.request(
            method,
            self._url(path),
            json=json,
            params=_clean_params(params),
        )
        _raise_for_status(resp)
        if not resp.content:
            return None
        return resp.json()


def _clean_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    if not params:
        return None
    return {k: v for k, v in params.items() if v is not None}


def _raise_for_status(resp: httpx.Response) -> None:
    if resp.is_success:
        return
    status = resp.status_code
    body: Any = None
    errors: list[str] = []
    message = resp.reason_phrase or "request failed"
    try:
        body = resp.json()
    except ValueError:
        body = resp.text or None
    if isinstance(body, dict):
        raw = body.get("errors")
        if isinstance(raw, list):
            errors = [str(e) for e in raw]
            if errors and not message:
                message = errors[0]
        raw_msg = body.get("message")
        if raw_msg:
            message = str(raw_msg)
    if status == 401:
        message = "invalid Woodpecker API token or unauthorized"
    elif status == 403:
        message = errors[0] if errors else "forbidden"
    elif status == 404:
        message = "not found"
    raise WoodpeckerError(status, message, errors=errors, body=body)


_current_client: ContextVar[WoodpeckerClient | None] = ContextVar("woodpecker_client", default=None)


def set_current_client(client: WoodpeckerClient | None) -> Token[WoodpeckerClient | None]:
    return _current_client.set(client)


def reset_current_client(token: Token[WoodpeckerClient | None]) -> None:
    _current_client.reset(token)


def get_woodpecker_client() -> WoodpeckerClient:
    client = _current_client.get()
    if client is None:
        raise RuntimeError(
            "no WoodpeckerClient bound to this request; Authorization header must be set"
        )
    return client
