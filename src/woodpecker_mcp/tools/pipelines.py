from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from ._common import client


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    async def list_pipelines(
        repo_id: int,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """List pipelines of a repository."""
        return await client().paginate(f"/repos/{repo_id}/pipelines", page=page, per_page=per_page)

    @mcp.tool()
    async def get_pipeline(repo_id: int, pipeline_number: int) -> dict[str, Any]:
        """Get a single pipeline by repo and pipeline number."""
        return await client().get_json(f"/repos/{repo_id}/pipelines/{pipeline_number}")

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
    async def restart_pipeline(repo_id: int, pipeline_number: int) -> dict[str, Any]:
        """Restart a pipeline."""
        return await client().post_json(f"/repos/{repo_id}/pipelines/{pipeline_number}")

    @mcp.tool()
    async def cancel_pipeline(repo_id: int, pipeline_number: int) -> dict[str, Any]:
        """Cancel a running pipeline."""
        return await client().post_json(f"/repos/{repo_id}/pipelines/{pipeline_number}/cancel")

    @mcp.tool()
    async def approve_pipeline(repo_id: int, pipeline_number: int) -> dict[str, Any]:
        """Approve and start a pending pipeline."""
        return await client().post_json(f"/repos/{repo_id}/pipelines/{pipeline_number}/approve")

    @mcp.tool()
    async def get_pipeline_config(repo_id: int, pipeline_number: int) -> dict[str, Any]:
        """Get configuration files for a pipeline."""
        data = await client().get_json(f"/repos/{repo_id}/pipelines/{pipeline_number}/config")
        return {"configs": data if isinstance(data, list) else []}

    @mcp.tool()
    async def rerun_last_failed(repo_id: int) -> dict[str, Any]:
        """Find the last failed pipeline for a repository and restart it."""
        data = await client().paginate(f"/repos/{repo_id}/pipelines", page=1, per_page=50)
        for pipeline in data.get("items", []):
            if pipeline.get("status") in ("failure", "error"):
                return await client().post_json(f"/repos/{repo_id}/pipelines/{pipeline['number']}")
        return {"message": "no failed pipelines found"}
