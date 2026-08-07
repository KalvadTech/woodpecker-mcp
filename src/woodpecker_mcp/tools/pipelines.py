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
        """List pipelines of a repository.

        Returns a paginated list of pipelines, ordered by creation date (newest first).

        Args:
            repo_id: The internal Woodpecker repository ID.
            page: Page number (1-indexed).
            per_page: Items per page (default 50).

        Returns:
            Dict with 'items' list of pipelines, each containing 'number', 'status',
            'event', 'branch', 'commit', 'author', 'created', etc.
            Pipeline statuses: pending, running, success, failure, error, killed, blocked.
            Also includes 'has_more' boolean indicating if more pages are available.

        Related tools:
            - get_pipeline: Get details of a specific pipeline.
            - trigger_pipeline: Create a new pipeline.
        """
        return await client().paginate(f"/repos/{repo_id}/pipelines", page=page, per_page=per_page)

    @mcp.tool()
    async def get_pipeline(repo_id: int, pipeline_number: int) -> dict[str, Any]:
        """Get a single pipeline by repo and pipeline number.

        Args:
            repo_id: The internal Woodpecker repository ID.
            pipeline_number: The pipeline number (e.g. 42).

        Returns:
            Pipeline object with 'number', 'status', 'event', 'branch', 'commit',
            'author', 'message', 'workflows', 'started', 'finished', etc.
            Status values: pending, running, success, failure, error, killed, blocked.

        Related tools:
            - list_pipelines: List all pipelines for a repository.
            - get_pipeline_config: Get the configuration files for this pipeline.
        """
        return await client().get_json(f"/repos/{repo_id}/pipelines/{pipeline_number}")

    @mcp.tool()
    async def trigger_pipeline(
        repo_id: int,
        branch: str = "main",
        variables: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Trigger a manual pipeline run for a repository.

        Creates a new pipeline on the specified branch. Useful for running
        CI on demand without pushing a commit.

        Args:
            repo_id: The internal Woodpecker repository ID.
            branch: Git branch to build (e.g. 'main', 'feature/x'). Defaults to 'main'.
            variables: Optional dict of pipeline variables to override
                       (e.g. {'DEPLOY_ENV': 'staging'}).

        Returns:
            The created pipeline object with 'number', 'status' (initially 'pending'),
            'branch', 'event', etc.

        Related tools:
            - get_pipeline: Check status of the triggered pipeline.
            - list_pipelines: See all recent pipelines.
        """
        body: dict[str, Any] = {"branch": branch}
        if variables:
            body["variables"] = variables
        return await client().post_json(f"/repos/{repo_id}/pipelines", json=body)

    @mcp.tool()
    async def restart_pipeline(repo_id: int, pipeline_number: int) -> dict[str, Any]:
        """Restart a pipeline.

        Re-runs a pipeline from the beginning. Useful for retrying failed pipelines
        or re-running successful ones with updated configuration.

        Args:
            repo_id: The internal Woodpecker repository ID.
            pipeline_number: The pipeline number to restart (e.g. 42).

        Returns:
            The restarted pipeline object with updated 'status' (initially 'pending').

        Related tools:
            - get_pipeline: Check the pipeline status before restarting.
            - rerun_last_failed: Automatically find and restart the last failed pipeline.
        """
        return await client().post_json(f"/repos/{repo_id}/pipelines/{pipeline_number}")

    @mcp.tool()
    async def cancel_pipeline(repo_id: int, pipeline_number: int) -> dict[str, Any]:
        """Cancel a running pipeline.

        Stops a pipeline that is currently running or pending. The pipeline status
        will be set to 'killed'.

        Args:
            repo_id: The internal Woodpecker repository ID.
            pipeline_number: The pipeline number to cancel (e.g. 42).

        Returns:
            The cancelled pipeline object with 'status' set to 'killed'.

        Related tools:
            - get_pipeline: Check if the pipeline is still running.
        """
        return await client().post_json(f"/repos/{repo_id}/pipelines/{pipeline_number}/cancel")

    @mcp.tool()
    async def approve_pipeline(repo_id: int, pipeline_number: int) -> dict[str, Any]:
        """Approve and start a pending pipeline.

        Use this when a pipeline is blocked and requires manual approval before
        it can run (e.g. for deployment pipelines).

        Args:
            repo_id: The internal Woodpecker repository ID.
            pipeline_number: The pipeline number to approve (e.g. 42).

        Returns:
            The approved pipeline object with 'status' changing from 'blocked' to 'pending'.

        Related tools:
            - get_pipeline: Check if the pipeline is blocked.
        """
        return await client().post_json(f"/repos/{repo_id}/pipelines/{pipeline_number}/approve")

    @mcp.tool()
    async def get_pipeline_config(repo_id: int, pipeline_number: int) -> dict[str, Any]:
        """Get configuration files for a pipeline.

        Returns the .woodpecker.yml or other pipeline configuration files used
        for this specific pipeline run.

        Args:
            repo_id: The internal Woodpecker repository ID.
            pipeline_number: The pipeline number (e.g. 42).

        Returns:
            Dict with 'configs' list of configuration files, each with 'name' and 'data'
            (base64-encoded YAML content).

        Related tools:
            - get_pipeline: Get pipeline metadata without config.
            - explain_pipeline_failure: Analyze failures including config inspection.
        """
        data = await client().get_json(f"/repos/{repo_id}/pipelines/{pipeline_number}/config")
        return {"configs": data if isinstance(data, list) else []}

    @mcp.tool()
    async def rerun_last_failed(repo_id: int) -> dict[str, Any]:
        """Find the last failed pipeline for a repository and restart it.

        Searches recent pipelines for the most recent one with status 'failure' or 'error',
        then restarts it. Useful for quickly retrying failed builds.

        Args:
            repo_id: The internal Woodpecker repository ID.

        Returns:
            The restarted pipeline object, or a message if no failed pipelines were found.

        Related tools:
            - restart_pipeline: Restart a specific pipeline by number.
            - explain_pipeline_failure: Understand why a pipeline failed before retrying.
        """
        data = await client().paginate(f"/repos/{repo_id}/pipelines", page=1, per_page=50)
        for pipeline in data.get("items", []):
            if pipeline.get("status") in ("failure", "error"):
                return await client().post_json(f"/repos/{repo_id}/pipelines/{pipeline['number']}")
        return {"message": "no failed pipelines found"}
