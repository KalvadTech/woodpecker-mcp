from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from ._common import client


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    async def get_health() -> dict[str, Any]:
        """Get health information of the Woodpecker server.

        Checks if the Woodpecker server is healthy and responsive.

        Returns:
            Dict with 'healthy' boolean (True if server is responsive, False otherwise).

        Related tools:
            - get_version: Get server version information.
        """
        try:
            await client().get_json("/healthz")
            return {"healthy": True}
        except Exception:
            return {"healthy": False}

    @mcp.tool()
    async def get_version() -> dict[str, Any]:
        """Get the Woodpecker server version and build information.

        Returns:
            Dict with 'version', 'commit', 'build_date', etc.

        Related tools:
            - get_health: Check server health status.
        """
        return await client().get_json("/version")

    @mcp.tool()
    async def list_queued_pipelines() -> dict[str, Any]:
        """List pipelines currently in the queue.

        Returns the feed of pipelines waiting to be executed or running
        across all repositories.

        Returns:
            Dict with 'items' list of queued pipeline entries, each containing
            'repo_id', 'full_name', 'number', 'status', 'event', 'branch',
            'commit', 'author', 'created', etc.

        Related tools:
            - get_queue_info: Get queue statistics (running/pending counts).
            - list_pipelines: List pipelines for a specific repository.
        """
        data = await client().get_json("/pipelines")
        return {"items": data if isinstance(data, list) else []}

    @mcp.tool()
    async def get_queue_info() -> dict[str, Any]:
        """Get pipeline queue information.

        Shows the current state of the pipeline queue, including running and pending jobs.

        Returns:
            Dict with 'running' (count of active pipelines), 'pending' (count waiting),
            and 'stats' (detailed queue statistics).

        Related tools:
            - list_pipelines: See specific pipelines in the queue.
        """
        try:
            data = await client().get_json("/queue")
            return data if data is not None else {"running": 0, "pending": 0, "stats": {}}
        except Exception:
            return {"running": 0, "pending": 0, "stats": {}}
