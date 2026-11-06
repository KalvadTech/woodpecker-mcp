import base64

import pytest
import respx

from tests.conftest import BASE_URL, call

API_PREFIX = "/api"


@pytest.mark.asyncio
async def test_get_step_logs(mcp, bound_client):
    fake_logs = [
        {"line": 1, "data": base64.b64encode(b"Cloning repository...").decode(), "time": 1000},
        {"line": 2, "data": base64.b64encode(b"Step completed").decode(), "time": 2000},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/logs/42/3").respond(200, json=fake_logs)
        result = await call(mcp, "get_step_logs", repo_id=1, pipeline_number=42, step_id=3)
        assert route.called
        assert result["total_lines"] == 2
        assert result["returned_lines"] == 2
        assert result["truncated"] is False
        assert result["text"] == "Cloning repository...\nStep completed"
        assert "logs" not in result


@pytest.mark.asyncio
async def test_get_step_logs_strips_ansi(mcp, bound_client):
    fake_logs = [
        {"line": 1, "data": base64.b64encode(b"\x1b[31mError: build failed\x1b[0m").decode()},
    ]
    async with respx.mock:
        respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/logs/42/3").respond(200, json=fake_logs)
        result = await call(mcp, "get_step_logs", repo_id=1, pipeline_number=42, step_id=3)
        assert result["text"] == "Error: build failed"


@pytest.mark.asyncio
async def test_get_step_logs_truncates_to_tail(mcp, bound_client):
    fake_logs = [
        {"line": i, "data": base64.b64encode(f"line {i}".encode()).decode()} for i in range(10)
    ]
    async with respx.mock:
        respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/logs/42/3").respond(200, json=fake_logs)
        result = await call(
            mcp,
            "get_step_logs",
            repo_id=1,
            pipeline_number=42,
            step_id=3,
            max_lines=3,
        )
        assert result["total_lines"] == 10
        assert result["returned_lines"] == 3
        assert result["truncated"] is True
        assert result["text"] == "line 7\nline 8\nline 9"


@pytest.mark.asyncio
async def test_download_step_logs(mcp, bound_client):
    fake_text = "line1\nline2\nline3"
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/logs/42/7/download").respond(
            200, text=fake_text
        )
        result = await call(mcp, "download_step_logs", repo_id=1, pipeline_number=42, step_id=7)
        assert route.called
        assert result["text"] == fake_text
        assert result["total_lines"] == 3
        assert result["truncated"] is False


@pytest.mark.asyncio
async def test_list_pipeline_steps(mcp, bound_client):
    fake_pipeline = {
        "id": 42,
        "workflows": [
            {
                "id": 7,
                "pid": 1,
                "name": "build",
                "state": "success",
                "children": [
                    {
                        "id": 11,
                        "pid": 1,
                        "name": "Build binary",
                        "state": "success",
                        "started": 1000,
                        "finished": 2000,
                        "exit_code": 0,
                    },
                    {
                        "id": 12,
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
        result = await call(mcp, "list_pipeline_steps", repo_id=1, pipeline_number=42)
        assert route.called
        assert len(result["steps"]) == 2
        assert result["steps"][0]["workflow"] == "build"
        assert result["steps"][0]["id"] == 11
        assert result["steps"][0]["pid"] == 1
        assert result["steps"][0]["name"] == "Build binary"
        assert result["steps"][1]["id"] == 12
        assert result["steps"][1]["name"] == "Run tests"
        assert result["workflows"] == [{"id": 7, "pid": 1, "name": "build", "state": "success"}]
        assert "children" not in result["workflows"][0]


@pytest.mark.asyncio
async def test_summarize_logs(mcp, bound_client):
    fake_logs = [
        {"line": 1, "data": base64.b64encode(b"Cloning repository...").decode(), "time": 1000},
        {"line": 2, "data": base64.b64encode(b"Error: build failed").decode(), "time": 2000},
        {"line": 3, "data": base64.b64encode(b"Warning: deprecated API").decode(), "time": 3000},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/logs/42/3").respond(200, json=fake_logs)
        result = await call(mcp, "summarize_logs", repo_id=1, pipeline_number=42, step_id=3)
        assert route.called
        assert result["total_lines"] == 3
        assert result["returned_lines"] == 3
        assert result["error_lines"] == 1
        assert result["warning_lines"] == 1
        assert result["truncated"] is False
        assert "Error: build failed" in result["text"]
