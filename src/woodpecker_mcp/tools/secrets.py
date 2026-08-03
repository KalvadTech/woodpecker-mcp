from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from ._common import client


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    async def list_repo_secrets(
        repo_id: int,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """List secrets for a repository."""
        params: dict[str, Any] = {"page": page, "perPage": per_page}
        return await client().paginate(
            f"/repos/{repo_id}/secrets", params=params, page=page, per_page=per_page
        )

    @mcp.tool()
    async def create_repo_secret(
        repo_id: int,
        name: str,
        value: str,
    ) -> dict[str, Any]:
        """Create a new secret for a repository.

        The name must be uppercase and use underscores (e.g. MY_SECRET).
        """
        body: dict[str, Any] = {"name": name, "value": value}
        return await client().post_json(f"/repos/{repo_id}/secrets", json=body)

    @mcp.tool()
    async def delete_repo_secret(repo_id: int, secret_name: str) -> dict[str, Any]:
        """Delete a secret from a repository."""
        await client().delete(f"/repos/{repo_id}/secrets/{secret_name}")
        return {"deleted": True}
