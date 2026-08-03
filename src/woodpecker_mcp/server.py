from __future__ import annotations

import os

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from .middleware import WoodpeckerAuthMiddleware, load_base_url
from .tools import register_all


def build_mcp(base_url: str) -> MCPServer:
    mcp = MCPServer("woodpecker")
    register_all(mcp)
    return mcp


def _load_transport_security() -> TransportSecuritySettings | None:
    raw = os.environ.get("MCP_ALLOWED_HOSTS", "").strip()
    if not raw:
        return None
    if raw == "*":
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)
    hosts: list[str] = []
    for entry in raw.split(","):
        host = entry.strip()
        if not host:
            continue
        hosts.append(host)
        if ":" not in host:
            hosts.append(f"{host}:*")
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
    )


async def _up(request: Request) -> PlainTextResponse:
    del request
    return PlainTextResponse("ok")


def build_app(transport: httpx.AsyncBaseTransport | None = None) -> Starlette:
    base_url = load_base_url()
    mcp = build_mcp(base_url)
    app: Starlette = mcp.streamable_http_app(
        stateless_http=True,
        json_response=True,
        transport_security=_load_transport_security(),
    )
    app.routes.append(Route("/up", _up, methods=["GET"]))
    app.add_middleware(
        WoodpeckerAuthMiddleware,
        base_url=base_url,
        transport=transport,
    )
    return app
