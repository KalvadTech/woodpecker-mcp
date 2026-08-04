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
        """List cron jobs for a repository."""
        return await client().paginate(f"/repos/{repo_id}/cron", page=page, per_page=per_page)

    @mcp.tool()
    async def create_cron_job(
        repo_id: int,
        name: str,
        schedule: str,
        branch: str = "main",
    ) -> dict[str, Any]:
        """Create a new cron job for a repository.

        schedule is a cron expression like '0 0 * * *'.
        """
        body: dict[str, Any] = {
            "name": name,
            "schedule": schedule,
            "branch": branch,
        }
        return await client().post_json(f"/repos/{repo_id}/cron", json=body)

    @mcp.tool()
    async def delete_cron_job(repo_id: int, cron_id: int) -> dict[str, Any]:
        """Delete a cron job from a repository."""
        await client().delete(f"/repos/{repo_id}/cron/{cron_id}")
        return {"deleted": True}

    @mcp.tool()
    async def trigger_cron_job(repo_id: int, cron_id: int) -> dict[str, Any]:
        """Trigger a cron job immediately."""
        return await client().post_json(f"/repos/{repo_id}/cron/{cron_id}")
