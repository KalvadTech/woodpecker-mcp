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
        """List all registered agents.

        Agents are worker nodes that execute pipeline steps.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page (default 50).

        Returns:
            Dict with 'items' list of agents, each containing 'id', 'name',
            'status' (idle, busy, offline), 'platform', 'backend', etc.
            Also includes 'has_more' boolean indicating if more pages are available.

        Related tools:
            - get_agent: Get details of a specific agent.
            - list_agent_tasks: See tasks assigned to an agent.
        """
        return await client().paginate("/agents", page=page, per_page=per_page)

    @mcp.tool()
    async def get_agent(agent_id: int) -> dict[str, Any]:
        """Get a single agent by its id.

        Args:
            agent_id: The agent ID.

        Returns:
            Agent object with 'id', 'name', 'status' (idle, busy, offline),
            'platform', 'backend', 'capacity', 'created', etc.

        Related tools:
            - list_agents: See all registered agents.
            - list_agent_tasks: See tasks assigned to this agent.
        """
        return await client().get_json(f"/agents/{agent_id}")

    @mcp.tool()
    async def list_agent_tasks(agent_id: int) -> dict[str, Any]:
        """List tasks assigned to an agent.

        Shows the pipeline steps currently being executed or queued for this agent.

        Args:
            agent_id: The agent ID.

        Returns:
            Dict with 'tasks' list, each containing task metadata.

        Related tools:
            - list_agents: Find agent IDs.
            - get_agent: Get agent details.
        """
        data = await client().get_json(f"/agents/{agent_id}/tasks")
        return {"tasks": data if isinstance(data, list) else []}
