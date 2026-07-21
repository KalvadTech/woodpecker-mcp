from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlsplit

import httpx

from .client import (
    WoodpeckerClient,
    reset_current_client,
    set_current_client,
)
from .errors import AuthHeaderError

_HEADER_AUTH = b"authorization"
_TOKEN_PREFIX = "Bearer "
_HEALTH_PATHS = {"/up"}


class WoodpeckerAuthMiddleware:
    def __init__(
        self,
        app: Any,
        *,
        base_url: str,
        api_prefix: str = "/api",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._app = app
        self._base_url = base_url
        self._api_prefix = api_prefix
        self._transport = transport

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self._app(scope, receive, send)
            return
        if scope.get("path") in _HEALTH_PATHS or scope.get("method") == "GET":
            await self._app(scope, receive, send)
            return

        token_raw: str | None = None
        for name, value in scope.get("headers", []):
            if name == _HEADER_AUTH:
                token_raw = value.decode("latin-1")
                break

        try:
            token = _extract_token(token_raw)
        except AuthHeaderError as exc:
            await _send_jsonrpc_error(send, exc)
            return

        client = WoodpeckerClient(
            self._base_url,
            token,
            api_prefix=self._api_prefix,
            transport=self._transport,
        )
        ctx_token = set_current_client(client)
        try:
            await self._app(scope, receive, send)
        finally:
            reset_current_client(ctx_token)
            await client.aclose()


def load_base_url() -> str:
    raw = os.environ.get("WOODPECKER_SERVER", "").strip()
    if not raw:
        raise RuntimeError("WOODPECKER_SERVER env var is required")
    parsed = urlsplit(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise RuntimeError(f"WOODPECKER_SERVER must be an absolute http(s) URL, got: {raw!r}")
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"


def load_api_prefix() -> str:
    raw = os.environ.get("WOODPECKER_API_PREFIX", "").strip()
    if not raw:
        return "/api"
    if not raw.startswith("/"):
        return f"/{raw}"
    return raw.rstrip("/")


def _extract_token(raw: str | None) -> str:
    if not raw:
        raise AuthHeaderError("missing Authorization header")
    if not raw.startswith(_TOKEN_PREFIX):
        raise AuthHeaderError(
            'Authorization header must use Bearer scheme, e.g. "Authorization: Bearer <token>"'
        )
    token = raw[len(_TOKEN_PREFIX) :].strip()
    if not token:
        raise AuthHeaderError("Authorization header Bearer token is empty")
    if any(c.isspace() for c in token):
        raise AuthHeaderError("Authorization header token must not contain whitespace")
    return token


async def _send_jsonrpc_error(send: Any, exc: AuthHeaderError) -> None:
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": exc.message},
            "id": None,
        }
    ).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": exc.status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body, "more_body": False})
