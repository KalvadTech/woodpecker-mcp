from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from ._common import client


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    async def list_organizations(
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """List all registered organizations. Requires admin rights."""
        params: dict[str, Any] = {"page": page, "perPage": per_page}
        return await client().paginate("/orgs", params=params, page=page, per_page=per_page)

    @mcp.tool()
    async def get_organization(org_id: int) -> dict[str, Any]:
        """Get an organization by its id."""
        return await client().get_json(f"/orgs/{org_id}")

    @mcp.tool()
    async def get_org_permissions(org_id: int) -> dict[str, Any]:
        """Get the permissions of the currently authenticated user for the given organization."""
        return await client().get_json(f"/orgs/{org_id}/permissions")
