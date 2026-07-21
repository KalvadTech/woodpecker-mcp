from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_forges(
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """List all configured forges."""
        params: dict[str, Any] = {"page": page, "perPage": per_page}
        return await client().paginate("/forges", params=params, page=page, per_page=per_page)
