from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from ._common import client


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    async def list_cron_jobs(
        repo_id: int,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """List cron jobs for a repository.

        Args:
            repo_id: The internal Woodpecker repository ID.
            page: Page number (1-indexed).
            per_page: Items per page (default 50).

        Returns:
            Dict with 'items' list of cron jobs, each containing 'id', 'name',
            'schedule', 'branch', 'created', etc.

        Related tools:
            - create_cron_job: Add a new cron job.
            - delete_cron_job: Remove a cron job.
        """
        return await client().paginate(f"/repos/{repo_id}/cron", page=page, per_page=per_page)

    @mcp.tool()
    async def create_cron_job(
        repo_id: int,
        name: str,
        schedule: str,
        branch: str = "main",
    ) -> dict[str, Any]:
        """Create a new cron job for a repository.

        Cron jobs trigger pipelines on a schedule without requiring code changes.

        Args:
            repo_id: The internal Woodpecker repository ID.
            name: Name for the cron job (e.g. 'nightly-build').
            schedule: Cron expression (e.g. '0 0 * * *' for daily at midnight,
                      '*/15 * * * *' for every 15 minutes).
            branch: Git branch to build (e.g. 'main'). Defaults to 'main'.

        Returns:
            The created cron job object with 'id', 'name', 'schedule', 'branch', etc.

        Related tools:
            - list_cron_jobs: See all cron jobs for the repository.
            - trigger_cron_job: Run a cron job immediately.
        """
        body: dict[str, Any] = {
            "name": name,
            "schedule": schedule,
            "branch": branch,
        }
        return await client().post_json(f"/repos/{repo_id}/cron", json=body)

    @mcp.tool()
    async def delete_cron_job(repo_id: int, cron_id: int) -> dict[str, Any]:
        """Delete a cron job from a repository.

        Args:
            repo_id: The internal Woodpecker repository ID.
            cron_id: The cron job ID to delete.

        Returns:
            Dict with 'deleted': True on success.

        Related tools:
            - list_cron_jobs: Find cron job IDs.
        """
        await client().delete(f"/repos/{repo_id}/cron/{cron_id}")
        return {"deleted": True}

    @mcp.tool()
    async def trigger_cron_job(repo_id: int, cron_id: int) -> dict[str, Any]:
        """Trigger a cron job immediately.

        Runs the cron job now instead of waiting for the next scheduled time.

        Args:
            repo_id: The internal Woodpecker repository ID.
            cron_id: The cron job ID to trigger.

        Returns:
            The triggered pipeline object.

        Related tools:
            - list_cron_jobs: Find cron job IDs.
            - create_cron_job: Add a new cron job.
        """
        return await client().post_json(f"/repos/{repo_id}/cron/{cron_id}")
