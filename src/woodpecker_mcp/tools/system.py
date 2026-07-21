from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_health() -> dict[str, Any]:
        """Get health information of the Woodpecker server.
        Returns 204 if healthy, raises error if unhealthy."""
        try:
            await client().get_json("/healthz")
            return {"healthy": True}
        except Exception:
            return {"healthy": False}

    @mcp.tool()
    async def get_version() -> dict[str, Any]:
        """Get the Woodpecker server version and build information."""
        return await client().get_json("/version")

    @mcp.tool()
    async def get_queue_info() -> dict[str, Any]:
        """Get pipeline queue information."""
        return await client().get_json("/queue")
