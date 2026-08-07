from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from ._common import client


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    async def list_forges(
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """List all configured forges.

        Forges are source code management integrations (GitHub, GitLab, Gitea, etc.)
        that Woodpecker uses to fetch repositories and report pipeline status.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page (default 50).

        Returns:
            Dict with 'items' list of forges, each containing 'id', 'type', 'url', etc.
            Also includes 'has_more' boolean indicating if more pages are available.
        """
        return await client().paginate("/forges", page=page, per_page=per_page)
