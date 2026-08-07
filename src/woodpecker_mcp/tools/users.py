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
        """List all registered users. Requires admin rights.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page (default 50).

        Returns:
            Dict with 'items' list of users, each containing 'id', 'login', 'email', 'admin', etc.

        Related tools:
            - get_current_user: Get the currently authenticated user.
        """
        return await client().paginate("/users", page=page, per_page=per_page)

    @mcp.tool()
    async def get_current_user() -> dict[str, Any]:
        """Get the currently authenticated user.

        Returns:
            User object with 'id', 'login', 'email', 'admin', 'avatar_url', etc.

        Related tools:
            - get_user_feed: Get the pipeline feed for this user.
        """
        return await client().get_json("/user")

    @mcp.tool()
    async def get_user_feed(
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """Get the pipeline feed for the currently authenticated user.

        Returns recent pipelines from repositories the user has access to.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page (default 50).

        Returns:
            Dict with 'items' list of pipelines, each containing 'repo_id', 'number',
            'status', 'event', 'branch', 'commit', 'author', etc.

        Related tools:
            - get_current_user: Get user details.
            - list_pipelines: List pipelines for a specific repository.
        """
        return await client().paginate("/user/feed", page=page, per_page=per_page)
