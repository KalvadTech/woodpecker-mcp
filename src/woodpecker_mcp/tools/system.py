from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from ._common import READ_ONLY, client, safe, tool


def register(mcp: MCPServer) -> None:
    @tool(mcp, annotations=READ_ONLY)
    @safe
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

    @tool(mcp, annotations=READ_ONLY)
    @safe
    async def get_version() -> dict[str, Any]:
        """Get the Woodpecker server version and build information.

        Returns:
            Dict with 'version', 'commit', 'build_date', etc.

        Related tools:
            - get_health: Check server health status.
        """
        return await client().get_json("/version")

    @tool(mcp, annotations=READ_ONLY)
    @safe
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

    @tool(mcp, annotations=READ_ONLY)
    @safe
    async def get_signature_public_key() -> dict[str, Any]:
        """Get the server's signature public key.

        Returns the public key the Woodpecker server uses to sign pipeline
        configurations and secrets.

        Returns:
            Dict with 'public_key' containing the PEM-encoded public key.

        Related tools:
            - get_version: Get server version information.
        """
        text = await client().get_text("/signature/public-key")
        return {"public_key": text}

    @tool(mcp, annotations=READ_ONLY)
    @safe
    async def get_queue_info() -> dict[str, Any]:
        """Get pipeline queue information.

        Shows the current state of the pipeline queue, including pending,
        waiting, and running tasks. Requires admin rights.

        Returns:
            Dict with 'pending', 'waiting_on_deps', and 'running' task lists,
            plus 'stats' (worker/pending/waiting/running counts) and 'paused'.

        Related tools:
            - list_queued_pipelines: See specific pipelines in the queue.
        """
        data = await client().get_json("/queue/info")
        return data if data is not None else {}
