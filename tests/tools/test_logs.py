import pytest
import respx

from tests.conftest import BASE_URL, call

API_PREFIX = "/api"


@pytest.mark.asyncio
async def test_get_step_logs(mcp, bound_client):
    fake_logs = [
        {"line": 1, "data": "Cloning repository...", "time": 1000},
        {"line": 2, "data": "Step completed", "time": 2000},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/logs/42/3").respond(200, json=fake_logs)
        result = await call(mcp, "get_step_logs", repo_id=1, pipeline_id=42, step_id=3)
        assert route.called
        assert result["logs"] == fake_logs


@pytest.mark.asyncio
async def test_list_pipeline_steps(mcp, bound_client):
    fake_pipeline = {
        "id": 42,
        "workflows": [
            {
                "name": "build",
                "children": [
                    {
                        "pid": 1,
                        "name": "Build binary",
                        "state": "success",
                        "started": 1000,
                        "finished": 2000,
                        "exit_code": 0,
                    },
                    {
                        "pid": 2,
                        "name": "Run tests",
                        "state": "success",
                        "started": 2000,
                        "finished": 3000,
                        "exit_code": 0,
                    },
                ],
            },
        ],
    }
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42").respond(
            200, json=fake_pipeline
        )
        result = await call(mcp, "list_pipeline_steps", repo_id=1, pipeline_id=42)
        assert route.called
        assert len(result["steps"]) == 2
        assert result["steps"][0]["workflow"] == "build"
        assert result["steps"][0]["name"] == "Build binary"
        assert result["steps"][1]["name"] == "Run tests"


@pytest.mark.asyncio
async def test_summarize_logs(mcp, bound_client):
    fake_logs = [
        {"line": 1, "data": "Cloning repository...", "time": 1000},
        {"line": 2, "data": "Error: build failed", "time": 2000},
        {"line": 3, "data": "Warning: deprecated API", "time": 3000},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/logs/42/3").respond(200, json=fake_logs)
        result = await call(mcp, "summarize_logs", repo_id=1, pipeline_id=42, step_id=3)
        assert route.called
        assert result["total_lines"] == 3
        assert result["error_lines"] == 1
        assert result["warning_lines"] == 1
        assert "Error: build failed" in result["text"]
