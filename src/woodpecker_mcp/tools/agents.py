from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from ._common import client


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    async def list_agents(
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """List all registered agents."""
        return await client().paginate("/agents", page=page, per_page=per_page)

    @mcp.tool()
    async def get_agent(agent_id: int) -> dict[str, Any]:
        """Get a single agent by its id."""
        return await client().get_json(f"/agents/{agent_id}")

    @mcp.tool()
    async def list_agent_tasks(agent_id: int) -> dict[str, Any]:
        """List tasks assigned to an agent."""
        data = await client().get_json(f"/agents/{agent_id}/tasks")
        return {"tasks": data if isinstance(data, list) else []}
