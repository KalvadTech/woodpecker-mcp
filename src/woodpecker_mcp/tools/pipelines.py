from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_pipelines(
        repo_id: int,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """List pipelines of a repository."""
        params: dict[str, Any] = {"page": page, "perPage": per_page}
        return await client().paginate(
            f"/repos/{repo_id}/pipelines", params=params, page=page, per_page=per_page
        )

    @mcp.tool()
    async def get_pipeline(repo_id: int, pipeline_id: int) -> dict[str, Any]:
        """Get a single pipeline by repo and pipeline id."""
        return await client().get_json(f"/repos/{repo_id}/pipelines/{pipeline_id}")

    @mcp.tool()
    async def trigger_pipeline(
        repo_id: int,
        branch: str = "main",
        variables: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Trigger a manual pipeline for a repository."""
        body: dict[str, Any] = {"branch": branch}
        if variables:
            body["variables"] = variables
        return await client().post_json(f"/repos/{repo_id}/pipelines", json=body)

    @mcp.tool()
    async def restart_pipeline(repo_id: int, pipeline_id: int) -> dict[str, Any]:
        """Restart a pipeline."""
        return await client().post_json(f"/repos/{repo_id}/pipelines/{pipeline_id}")

    @mcp.tool()
    async def cancel_pipeline(repo_id: int, pipeline_id: int) -> dict[str, Any]:
        """Cancel a running pipeline."""
        return await client().post_json(f"/repos/{repo_id}/pipelines/{pipeline_id}/cancel")

    @mcp.tool()
    async def approve_pipeline(repo_id: int, pipeline_id: int) -> dict[str, Any]:
        """Approve and start a pending pipeline."""
        return await client().post_json(f"/repos/{repo_id}/pipelines/{pipeline_id}/approve")

    @mcp.tool()
    async def get_pipeline_config(repo_id: int, pipeline_id: int) -> dict[str, Any]:
        """Get configuration files for a pipeline."""
        data = await client().get_json(f"/repos/{repo_id}/pipelines/{pipeline_id}/config")
        return {"configs": data if isinstance(data, list) else []}
