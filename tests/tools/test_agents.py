import pytest
import respx

from tests.conftest import BASE_URL, call

API_PREFIX = "/api"


@pytest.mark.asyncio
async def test_list_agents(mcp, bound_client):
    fake_agents = [
        {"id": 1, "name": "agent-1", "platform": "linux/amd64", "backend": "docker"},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/agents").respond(
            200,
            json=fake_agents,
        )
        result = await call(mcp, "list_agents")
        assert route.called
        assert result["items"] == fake_agents


@pytest.mark.asyncio
async def test_get_agent(mcp, bound_client):
    fake_agent = {"id": 1, "name": "agent-1", "platform": "linux/amd64"}
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/agents/1").respond(
            200,
            json=fake_agent,
        )
        result = await call(mcp, "get_agent", agent_id=1)
        assert route.called
        assert result == fake_agent


@pytest.mark.asyncio
async def test_list_agent_tasks(mcp, bound_client):
    fake_tasks = [
        {"id": "task-1", "name": "build", "pipeline_id": 42, "repo_id": 1},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/agents/1/tasks").respond(
            200,
            json=fake_tasks,
        )
        result = await call(mcp, "list_agent_tasks", agent_id=1)
        assert route.called
        assert result["tasks"] == fake_tasks
