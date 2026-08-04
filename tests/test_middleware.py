from __future__ import annotations

import json
from typing import Any

import pytest

from woodpecker_mcp.client import get_woodpecker_client
from woodpecker_mcp.errors import AuthHeaderError
from woodpecker_mcp.middleware import (
    WoodpeckerAuthMiddleware,
    _extract_token,
    _send_jsonrpc_error,
    load_base_url,
)


class TestExtractToken:
    def test_valid_bearer_token(self):
        assert _extract_token("Bearer my-secret-token") == "my-secret-token"

    def test_none_input(self):
        with pytest.raises(AuthHeaderError, match="missing Authorization header"):
            _extract_token(None)

    def test_empty_string(self):
        with pytest.raises(AuthHeaderError, match="missing Authorization header"):
            _extract_token("")

    def test_wrong_scheme(self):
        with pytest.raises(AuthHeaderError, match="must use Bearer scheme"):
            _extract_token("Basic dXNlcjpwYXNz")

    def test_bearer_no_token(self):
        with pytest.raises(AuthHeaderError, match="Bearer token is empty"):
            _extract_token("Bearer ")

    def test_bearer_only_whitespace(self):
        with pytest.raises(AuthHeaderError, match="Bearer token is empty"):
            _extract_token("Bearer   ")

    def test_token_with_internal_whitespace(self):
        with pytest.raises(AuthHeaderError, match="must not contain whitespace"):
            _extract_token("Bearer my secret token")

    def test_token_with_leading_trailing_whitespace(self):
        assert _extract_token("Bearer   my-token   ") == "my-token"

    def test_error_status_code(self):
        with pytest.raises(AuthHeaderError) as exc_info:
            _extract_token(None)
        assert exc_info.value.status == 400


class TestLoadBaseUrl:
    def test_missing_env_var(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("WOODPECKER_SERVER", raising=False)
        with pytest.raises(RuntimeError, match="WOODPECKER_SERVER env var is required"):
            load_base_url()

    def test_empty_env_var(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("WOODPECKER_SERVER", "")
        with pytest.raises(RuntimeError, match="WOODPECKER_SERVER env var is required"):
            load_base_url()

    def test_whitespace_only_env_var(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("WOODPECKER_SERVER", "   ")
        with pytest.raises(RuntimeError, match="WOODPECKER_SERVER env var is required"):
            load_base_url()

    def test_invalid_scheme(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("WOODPECKER_SERVER", "ftp://ci.example.com")
        with pytest.raises(RuntimeError, match="must be an absolute http"):
            load_base_url()

    def test_no_scheme(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("WOODPECKER_SERVER", "ci.example.com")
        with pytest.raises(RuntimeError, match="must be an absolute http"):
            load_base_url()

    def test_valid_https_url(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("WOODPECKER_SERVER", "https://ci.example.com")
        assert load_base_url() == "https://ci.example.com"

    def test_valid_http_url(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("WOODPECKER_SERVER", "http://localhost:8080")
        assert load_base_url() == "http://localhost:8080"

    def test_trailing_slash_stripped(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("WOODPECKER_SERVER", "https://ci.example.com/")
        assert load_base_url() == "https://ci.example.com"

    def test_path_preserved(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("WOODPECKER_SERVER", "https://ci.example.com/woodpecker")
        assert load_base_url() == "https://ci.example.com/woodpecker"

    def test_path_trailing_slash_stripped(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("WOODPECKER_SERVER", "https://ci.example.com/woodpecker/")
        assert load_base_url() == "https://ci.example.com/woodpecker"


class TestWoodpeckerAuthMiddleware:
    @staticmethod
    def _make_scope(
        *,
        method: str = "POST",
        path: str = "/mcp",
        headers: list[tuple[bytes, bytes]] | None = None,
        scope_type: str = "http",
    ) -> dict[str, Any]:
        return {
            "type": scope_type,
            "method": method,
            "path": path,
            "headers": headers or [],
        }

    @staticmethod
    async def _noop_app(scope: dict, receive: Any, send: Any) -> None:
        pass

    @pytest.mark.asyncio
    async def test_non_http_scope_passes_through(self):
        called = False

        async def app(scope: dict, receive: Any, send: Any) -> None:
            nonlocal called
            called = True

        middleware = WoodpeckerAuthMiddleware(app, base_url="https://ci.example.com")
        scope = self._make_scope(scope_type="lifespan")
        await middleware(scope, None, None)
        assert called

    @pytest.mark.asyncio
    async def test_get_request_passes_through(self):
        called = False

        async def app(scope: dict, receive: Any, send: Any) -> None:
            nonlocal called
            called = True

        middleware = WoodpeckerAuthMiddleware(app, base_url="https://ci.example.com")
        scope = self._make_scope(method="GET")
        await middleware(scope, None, None)
        assert called

    @pytest.mark.asyncio
    async def test_health_path_passes_through(self):
        called = False

        async def app(scope: dict, receive: Any, send: Any) -> None:
            nonlocal called
            called = True

        middleware = WoodpeckerAuthMiddleware(app, base_url="https://ci.example.com")
        scope = self._make_scope(method="POST", path="/up")
        await middleware(scope, None, None)
        assert called

    @pytest.mark.asyncio
    async def test_missing_auth_header_returns_error(self):
        messages: list[dict] = []

        async def send(msg: dict) -> None:
            messages.append(msg)

        middleware = WoodpeckerAuthMiddleware(self._noop_app, base_url="https://ci.example.com")
        scope = self._make_scope()
        await middleware(scope, None, send)

        assert len(messages) == 2
        assert messages[0]["type"] == "http.response.start"
        assert messages[0]["status"] == 400
        body = json.loads(messages[1]["body"])
        assert body["jsonrpc"] == "2.0"
        assert body["error"]["code"] == -32600
        assert "missing Authorization header" in body["error"]["message"]

    @pytest.mark.asyncio
    async def test_wrong_scheme_returns_error(self):
        messages: list[dict] = []

        async def send(msg: dict) -> None:
            messages.append(msg)

        middleware = WoodpeckerAuthMiddleware(self._noop_app, base_url="https://ci.example.com")
        scope = self._make_scope(headers=[(b"authorization", b"Basic dXNlcjpwYXNz")])
        await middleware(scope, None, send)

        assert messages[0]["status"] == 400
        body = json.loads(messages[1]["body"])
        assert "must use Bearer scheme" in body["error"]["message"]

    @pytest.mark.asyncio
    async def test_empty_token_returns_error(self):
        messages: list[dict] = []

        async def send(msg: dict) -> None:
            messages.append(msg)

        middleware = WoodpeckerAuthMiddleware(self._noop_app, base_url="https://ci.example.com")
        scope = self._make_scope(headers=[(b"authorization", b"Bearer ")])
        await middleware(scope, None, send)

        assert messages[0]["status"] == 400
        body = json.loads(messages[1]["body"])
        assert "Bearer token is empty" in body["error"]["message"]

    @pytest.mark.asyncio
    async def test_valid_token_creates_client_and_calls_app(self):
        called = False
        captured_client = None

        async def app(scope: dict, receive: Any, send: Any) -> None:
            nonlocal called, captured_client
            called = True
            captured_client = get_woodpecker_client()

        middleware = WoodpeckerAuthMiddleware(app, base_url="https://ci.example.com")
        scope = self._make_scope(headers=[(b"authorization", b"Bearer my-token-123")])
        await middleware(scope, None, None)

        assert called
        assert captured_client is not None
        assert captured_client.base_url == "https://ci.example.com"

    @pytest.mark.asyncio
    async def test_client_cleaned_up_after_request(self):
        async def app(scope: dict, receive: Any, send: Any) -> None:
            pass

        middleware = WoodpeckerAuthMiddleware(app, base_url="https://ci.example.com")
        scope = self._make_scope(headers=[(b"authorization", b"Bearer my-token")])
        await middleware(scope, None, None)

        with pytest.raises(RuntimeError, match="no WoodpeckerClient bound"):
            get_woodpecker_client()

    @pytest.mark.asyncio
    async def test_client_cleaned_up_on_app_exception(self):
        async def app(scope: dict, receive: Any, send: Any) -> None:
            raise ValueError("boom")

        middleware = WoodpeckerAuthMiddleware(app, base_url="https://ci.example.com")
        scope = self._make_scope(headers=[(b"authorization", b"Bearer my-token")])

        with pytest.raises(ValueError, match="boom"):
            await middleware(scope, None, None)

        with pytest.raises(RuntimeError, match="no WoodpeckerClient bound"):
            get_woodpecker_client()


class TestSendJsonrpcError:
    @pytest.mark.asyncio
    async def test_sends_correct_structure(self):
        messages: list[dict] = []

        async def send(msg: dict) -> None:
            messages.append(msg)

        exc = AuthHeaderError("test error", status=401)
        await _send_jsonrpc_error(send, exc)

        assert len(messages) == 2

        start = messages[0]
        assert start["type"] == "http.response.start"
        assert start["status"] == 401
        headers = dict(start["headers"])
        assert headers[b"content-type"] == b"application/json"

        body_msg = messages[1]
        assert body_msg["type"] == "http.response.body"
        assert body_msg["more_body"] is False

        body = json.loads(body_msg["body"])
        assert body == {
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": "test error"},
            "id": None,
        }

    @pytest.mark.asyncio
    async def test_content_length_matches_body(self):
        messages: list[dict] = []

        async def send(msg: dict) -> None:
            messages.append(msg)

        exc = AuthHeaderError("some message")
        await _send_jsonrpc_error(send, exc)

        headers = dict(messages[0]["headers"])
        expected_length = str(len(messages[1]["body"]))
        assert headers[b"content-length"] == expected_length.encode("ascii")
