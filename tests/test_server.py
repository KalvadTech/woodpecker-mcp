from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
import pytest
from mcp.server.transport_security import TransportSecuritySettings

from tests.conftest import API_TOKEN, BASE_URL
from woodpecker_mcp import __version__
from woodpecker_mcp.server import _load_transport_security, build_app

_INIT_REQUEST = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1"},
    },
}

_NO_SECURITY = TransportSecuritySettings(enable_dns_rebinding_protection=False)


@pytest.fixture
def app():
    return build_app(base_url=BASE_URL, transport_security=_NO_SECURITY)


@asynccontextmanager
async def _client(app, base_url: str = "http://testserver") -> AsyncGenerator[httpx.AsyncClient]:
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url=base_url,
        ) as http,
    ):
        yield http


def _auth_headers(token: str = API_TOKEN) -> dict[str, str]:
    return {
        "authorization": f"Bearer {token}",
        "accept": "application/json, text/event-stream",
    }


@pytest.mark.asyncio
async def test_up_is_public(app):
    async with _client(app) as client:
        response = await client.get("/up")
    assert response.status_code == 200
    assert response.text == "ok"


@pytest.mark.asyncio
async def test_mcp_post_requires_auth(app):
    async with _client(app) as client:
        response = await client.post("/mcp", json=_INIT_REQUEST)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == 'Bearer realm="woodpecker-mcp"'
    body = response.json()
    assert body["error"]["code"] == -32600
    assert "missing Authorization header" in body["error"]["message"]


@pytest.mark.asyncio
async def test_mcp_get_requires_auth(app):
    async with _client(app) as client:
        response = await client.get("/mcp")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_mcp_rejects_malformed_bearer(app):
    async with _client(app) as client:
        response = await client.post(
            "/mcp",
            json=_INIT_REQUEST,
            headers={"authorization": "Basic dXNlcjpwYXNz"},
        )
    assert response.status_code == 401
    assert "must use Bearer scheme" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_mcp_initialize_with_valid_token(app):
    async with _client(app) as client:
        response = await client.post("/mcp", json=_INIT_REQUEST, headers=_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["jsonrpc"] == "2.0"
    assert body["result"]["serverInfo"]["name"] == "woodpecker"
    assert body["result"]["serverInfo"]["version"] == __version__
    assert "untrusted input" in body["result"]["instructions"]


@pytest.mark.asyncio
async def test_host_allowlist_rejects_unknown_host():
    app = build_app(
        base_url=BASE_URL,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=["allowed.test", "allowed.test:*"],
        ),
    )
    async with _client(app, base_url="http://evil.test") as client:
        response = await client.post("/mcp", json=_INIT_REQUEST, headers=_auth_headers())
    assert response.status_code == 421


@pytest.mark.asyncio
async def test_host_allowlist_accepts_allowed_host():
    app = build_app(
        base_url=BASE_URL,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=["allowed.test", "allowed.test:*"],
        ),
    )
    async with _client(app, base_url="http://allowed.test") as client:
        response = await client.post("/mcp", json=_INIT_REQUEST, headers=_auth_headers())
    assert response.status_code == 200


class TestLoadTransportSecurity:
    def test_unset_returns_none(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("MCP_ALLOWED_HOSTS", raising=False)
        assert _load_transport_security() is None

    def test_wildcard_disables_protection(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("MCP_ALLOWED_HOSTS", "*")
        settings = _load_transport_security()
        assert settings is not None
        assert settings.enable_dns_rebinding_protection is False

    def test_host_list_adds_wildcard_port(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("MCP_ALLOWED_HOSTS", "ci.example.com, 127.0.0.1")
        settings = _load_transport_security()
        assert settings is not None
        assert settings.enable_dns_rebinding_protection is True
        assert settings.allowed_hosts == [
            "ci.example.com",
            "ci.example.com:*",
            "127.0.0.1",
            "127.0.0.1:*",
        ]
