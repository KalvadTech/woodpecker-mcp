from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from ._common import client


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    async def list_users(
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """List all registered users. Requires admin rights."""
        params: dict[str, Any] = {"page": page, "perPage": per_page}
        return await client().paginate("/users", params=params, page=page, per_page=per_page)

    @mcp.tool()
    async def get_current_user() -> dict[str, Any]:
        """Get the currently authenticated user."""
        return await client().get_json("/user")

    @mcp.tool()
    async def get_user_feed(
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """Get the pipeline feed for the currently authenticated user."""
        params: dict[str, Any] = {"page": page, "perPage": per_page}
        return await client().paginate("/user/feed", params=params, page=page, per_page=per_page)
