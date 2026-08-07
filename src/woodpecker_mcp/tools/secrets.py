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
        """List secrets for a repository.

        Secrets are encrypted environment variables available to pipeline steps.

        Args:
            repo_id: The internal Woodpecker repository ID.
            page: Page number (1-indexed).
            per_page: Items per page (default 50).

        Returns:
            Dict with 'items' list of secrets, each containing 'name' (values are not returned).

        Related tools:
            - create_repo_secret: Add a new secret.
            - delete_repo_secret: Remove a secret.
        """
        return await client().paginate(f"/repos/{repo_id}/secrets", page=page, per_page=per_page)

    @mcp.tool()
    async def create_repo_secret(
        repo_id: int,
        name: str,
        value: str,
    ) -> dict[str, Any]:
        """Create a new secret for a repository.

        Secrets are encrypted environment variables available to pipeline steps.
        The secret value is stored securely and not returned by list operations.

        Args:
            repo_id: The internal Woodpecker repository ID.
            name: Secret name, must be uppercase with underscores (e.g. 'MY_SECRET',
                  'DEPLOY_TOKEN'). Will be available as environment variable in pipelines.
            value: The secret value to encrypt and store.

        Returns:
            The created secret object with 'name' (value is not returned).

        Related tools:
            - list_repo_secrets: See all secrets for the repository.
            - delete_repo_secret: Remove a secret.
        """
        body: dict[str, Any] = {"name": name, "value": value}
        return await client().post_json(f"/repos/{repo_id}/secrets", json=body)

    @mcp.tool()
    async def delete_repo_secret(repo_id: int, secret_name: str) -> dict[str, Any]:
        """Delete a secret from a repository.

        Args:
            repo_id: The internal Woodpecker repository ID.
            secret_name: The name of the secret to delete (e.g. 'MY_SECRET').

        Returns:
            Dict with 'deleted': True on success.

        Related tools:
            - list_repo_secrets: See all secrets for the repository.
            - create_repo_secret: Add a new secret.
        """
        await client().delete(f"/repos/{repo_id}/secrets/{secret_name}")
        return {"deleted": True}
