from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from ._common import client


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    async def search_repositories(
        query: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """Search repositories visible to the current user."""
        params: dict[str, Any] | None = {"query": query} if query else None
        return await client().paginate("/repos", params=params, page=page, per_page=per_page)

    @mcp.tool()
    async def get_repository(repo_id: int) -> dict[str, Any]:
        """Get a single repository by its id."""
        return await client().get_json(f"/repos/{repo_id}")

    @mcp.tool()
    async def list_branches(repo_id: int) -> dict[str, Any]:
        """List branches of a repository."""
        data = await client().get_json(f"/repos/{repo_id}/branches")
        return {"branches": data if isinstance(data, list) else []}

    @mcp.tool()
    async def list_pull_requests(repo_id: int) -> dict[str, Any]:
        """List active pull requests of a repository."""
        data = await client().get_json(f"/repos/{repo_id}/pull_requests")
        return {"pull_requests": data if isinstance(data, list) else []}

    @mcp.tool()
    async def repair_repository(repo_id: int) -> dict[str, Any]:
        """Repair a repository by re-syncing its webhook and configuration."""
        return await client().post_json(f"/repos/{repo_id}/repair")
