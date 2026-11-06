from __future__ import annotations

import base64

import pytest
import respx

from tests.conftest import BASE_URL, call

API_PREFIX = "/api"


@pytest.mark.asyncio
async def test_queue_info_contract(mcp, bound_client):
    async with respx.mock(assert_all_called=True) as mock:
        route = mock.get(f"{BASE_URL}{API_PREFIX}/queue/info").respond(200, json={"paused": False})
        result = await call(mcp, "get_queue_info")

    assert route.called
    assert result == {"paused": False}


@pytest.mark.asyncio
async def test_search_repositories_contract(mcp, bound_client):
    async with respx.mock(assert_all_called=True) as mock:
        route = mock.get(
            f"{BASE_URL}{API_PREFIX}/user/repos",
            params={"name": "repo"},
        ).respond(200, json=[{"id": 1, "name": "repo"}])
        result = await call(mcp, "search_repositories", query="repo")

    assert route.called
    assert result["items"] == [{"id": 1, "name": "repo"}]


@pytest.mark.asyncio
async def test_step_logs_use_step_database_id(mcp, bound_client):
    pipeline = {
        "workflows": [
            {
                "name": "build",
                "children": [
                    {
                        "id": 99,
                        "pid": 1,
                        "name": "test",
                        "state": "failure",
                        "exit_code": 1,
                    }
                ],
            }
        ]
    }
    logs = [{"line": 1, "data": base64.b64encode(b"boom").decode()}]

    async with respx.mock(assert_all_called=True) as mock:
        mock.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42").respond(200, json=pipeline)
        logs_route = mock.get(f"{BASE_URL}{API_PREFIX}/repos/1/logs/42/99").respond(200, json=logs)

        steps = await call(mcp, "list_pipeline_steps", repo_id=1, pipeline_number=42)
        step_id = steps["steps"][0]["id"]
        result = await call(
            mcp,
            "get_step_logs",
            repo_id=1,
            pipeline_number=42,
            step_id=step_id,
        )

    assert logs_route.called
    assert result["text"] == "boom"


@pytest.mark.asyncio
async def test_pagination_contract_caps_at_50(mcp, bound_client):
    pipelines = [{"id": i} for i in range(50)]

    async with respx.mock(assert_all_called=True) as mock:
        route = mock.get(
            f"{BASE_URL}{API_PREFIX}/repos/1/pipelines",
            params={"page": "1", "perPage": "50"},
        ).respond(200, json=pipelines)
        result = await call(mcp, "list_pipelines", repo_id=1, per_page=100)

    assert route.called
    assert result["per_page"] == 50
    assert result["has_more"] is True
