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
        """List all registered organizations. Requires admin rights.

        Organizations group repositories and users for access control.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page (default 50).

        Returns:
            Dict with 'items' list of organizations, each containing 'id', 'name', etc.

        Related tools:
            - get_organization: Get details of a specific organization.
            - get_org_permissions: Check your permissions for an organization.
        """
        return await client().paginate("/orgs", page=page, per_page=per_page)

    @mcp.tool()
    async def get_organization(org_id: int) -> dict[str, Any]:
        """Get an organization by its id.

        Args:
            org_id: The organization ID.

        Returns:
            Organization object with 'id', 'name', etc.

        Related tools:
            - list_organizations: See all organizations.
            - get_org_permissions: Check your permissions for this organization.
        """
        return await client().get_json(f"/orgs/{org_id}")

    @mcp.tool()
    async def get_org_permissions(org_id: int) -> dict[str, Any]:
        """Get the permissions of the currently authenticated user for the given organization.

        Args:
            org_id: The organization ID.

        Returns:
            Dict with permission flags (e.g. 'admin', 'write', 'read').

        Related tools:
            - get_organization: Get organization details.
        """
        return await client().get_json(f"/orgs/{org_id}/permissions")
