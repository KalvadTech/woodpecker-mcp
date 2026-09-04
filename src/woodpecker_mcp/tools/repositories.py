from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from ..errors import WoodpeckerError
from ._common import client


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    async def search_repositories(
        query: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """Search repositories visible to the current user.

        Returns a paginated list of repositories. Use this to find the
        internal Woodpecker repo_id needed by most other tools.

        Args:
            query: Optional filter string to match against repository names.
            page: Page number (1-indexed).
            per_page: Items per page (default 50).

        Returns:
            Dict with 'items' list of repos, each containing 'id', 'full_name',
            'active', 'default_branch', 'visibility', etc.
            Also includes 'has_more' boolean indicating if more pages are available.

        Related tools:
            - get_repository: Get full details of a single repo by ID.
        """
        params: dict[str, Any] | None = {"query": query} if query else None
        return await client().paginate("/repos", params=params, page=page, per_page=per_page)

    @mcp.tool()
    async def get_repository(repo_id: int) -> dict[str, Any]:
        """Get a single repository by its internal Woodpecker ID.

        Args:
            repo_id: The internal Woodpecker repository ID (not the forge/GitHub ID).
                     Use search_repositories to find it.

        Returns:
            Repository object with 'id', 'full_name', 'forge_url', 'active',
            'default_branch', 'visibility', 'timeout', etc.

        Related tools:
            - search_repositories: Find repositories by name.
            - list_branches: List branches for this repository.
        """
        try:
            return await client().get_json(f"/repos/{repo_id}")
        except WoodpeckerError as e:
            raise ToolError(e.message) from e

    @mcp.tool()
    async def list_branches(repo_id: int) -> dict[str, Any]:
        """List branches of a repository.

        Args:
            repo_id: The internal Woodpecker repository ID.

        Returns:
            Dict with 'branches' list of branch names (e.g. ['main', 'develop', 'feature/x']).

        Related tools:
            - get_repository: Get repository metadata.
            - trigger_pipeline: Trigger a pipeline on a specific branch.
        """
        data = await client().get_json(f"/repos/{repo_id}/branches")
        return {"branches": data if isinstance(data, list) else []}

    @mcp.tool()
    async def list_pull_requests(repo_id: int) -> dict[str, Any]:
        """List active pull requests of a repository.

        Args:
            repo_id: The internal Woodpecker repository ID.

        Returns:
            Dict with 'pull_requests' list, each containing PR metadata from the forge.

        Related tools:
            - get_repository: Get repository metadata.
        """
        data = await client().get_json(f"/repos/{repo_id}/pull_requests")
        return {"pull_requests": data if isinstance(data, list) else []}

    @mcp.tool()
    async def repair_repository(repo_id: int) -> dict[str, Any]:
        """Repair a repository by re-syncing its webhook and configuration.

        Use this when the repository's webhook is broken or configuration is out of sync
        with the forge (GitHub/GitLab).

        Args:
            repo_id: The internal Woodpecker repository ID.

        Returns:
            Confirmation of repair action.

        Related tools:
            - get_repository: Check repository status before/after repair.
        """
        return await client().post_json(f"/repos/{repo_id}/repair")

    @mcp.tool()
    async def activate_repository(forge_remote_id: str) -> dict[str, Any]:
        """Activate a repository for the currently authenticated user.

        Enables Woodpecker integration for a repository that exists at the forge
        but is not yet active in Woodpecker.

        Args:
            forge_remote_id: The repository's unique identifier at the forge
                             (e.g. the GitHub repo ID).

        Returns:
            The activated repository object with 'id', 'full_name', 'active',
            'default_branch', etc.

        Related tools:
            - search_repositories: Find repositories to activate.
            - deactivate_repository: Remove a repository from Woodpecker.
        """
        return await client().post_json("/repos", params={"forge_remote_id": forge_remote_id})

    @mcp.tool()
    async def deactivate_repository(repo_id: int) -> dict[str, Any]:
        """Deactivate a repository, removing it from Woodpecker.

        Deletes the repository and its configuration from the Woodpecker server.
        Use this when a repository should no longer be built.

        Args:
            repo_id: The internal Woodpecker repository ID.

        Returns:
            Dict with 'deleted': True on success.

        Related tools:
            - search_repositories: Find repository IDs.
            - activate_repository: Re-activate a repository later.
        """
        await client().delete(f"/repos/{repo_id}")
        return {"deleted": True}
