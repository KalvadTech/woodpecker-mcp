import base64

import pytest
import respx

from tests.conftest import BASE_URL, call

API_PREFIX = "/api"


def _encode(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def _fake_pipeline(
    number: int = 42,
    status: str = "failure",
    workflows: list | None = None,
) -> dict:
    return {
        "id": 100,
        "number": number,
        "status": status,
        "event": "push",
        "branch": "main",
        "message": "fix: broken build",
        "author": "dev",
        "commit": "abc123",
        "created": 1000000,
        "started": 1000010,
        "finished": 1000120,
        "changed_files": ["src/main.py"],
        "workflows": workflows
        or [
            {
                "name": "build",
                "state": "failure",
                "error": "exit code 1",
                "started": 1000010,
                "finished": 1000090,
                "children": [
                    {
                        "id": 10,
                        "pid": 1,
                        "name": "clone",
                        "state": "success",
                        "exit_code": 0,
                        "started": 1000010,
                        "finished": 1000020,
                        "type": "clone",
                    },
                    {
                        "id": 11,
                        "pid": 2,
                        "name": "test",
                        "state": "failure",
                        "exit_code": 1,
                        "started": 1000020,
                        "finished": 1000080,
                        "type": "plugin",
                    },
                ],
            },
        ],
    }


def _fake_config(name: str = ".woodpecker.yml") -> list[dict]:
    data = "pipeline:\n  test:\n    image: python:3.12\n    commands:\n      - pytest"
    return [{"name": name, "data": _encode(data)}]


def _fake_logs(lines: list[str]) -> list[dict]:
    return [
        {"line": i, "data": _encode(line), "time": 1000 + i * 100} for i, line in enumerate(lines)
    ]


@pytest.mark.asyncio
async def test_explain_with_pipeline_number(mcp, bound_client):
    pipeline = _fake_pipeline()
    logs = _fake_logs(["Cloning...", "Error: test failed with exit code 1"])
    config = _fake_config()

    async with respx.mock:
        pipeline_route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42").respond(
            200, json=pipeline
        )
        config_route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42/config").respond(
            200, json=config
        )
        logs_route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/logs/42/11").respond(200, json=logs)

        result = await call(mcp, "explain_pipeline_failure", repo_id=1, pipeline_number=42)

        assert pipeline_route.called
        assert config_route.called
        assert logs_route.called
        assert result["pipeline"]["number"] == 42
        assert result["pipeline"]["status"] == "failure"
        assert result["pipeline"]["duration_seconds"] == 110
        assert len(result["workflows"]) == 1
        assert result["workflows"][0]["name"] == "build"
        assert result["workflows"][0]["error"] == "exit code 1"

        steps = result["workflows"][0]["steps"]
        assert len(steps) == 2
        assert steps[0]["name"] == "clone"
        assert steps[0]["state"] == "success"
        assert "logs" not in steps[0]
        assert steps[1]["name"] == "test"
        assert steps[1]["state"] == "failure"
        assert steps[1]["exit_code"] == 1
        assert steps[1]["logs"]["total_lines"] == 2
        assert "Error: test failed" in steps[1]["logs"]["text"]
        assert steps[1]["logs"]["truncated"] is False

        assert len(result["config"]) == 1
        assert "python:3.12" in result["config"][0]["data"]


@pytest.mark.asyncio
async def test_explain_without_pipeline_number_finds_latest_failure(mcp, bound_client):
    pipeline = _fake_pipeline()
    logs = _fake_logs(["Error: something broke"])
    config = _fake_config()

    list_response = [
        {"id": 1, "number": 1, "status": "success"},
        {"id": 42, "number": 42, "status": "failure"},
    ]

    async with respx.mock:
        list_route = respx.get(
            f"{BASE_URL}{API_PREFIX}/repos/1/pipelines",
            params={"page": 1, "perPage": 50},
        ).respond(200, json=list_response)
        pipeline_route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42").respond(
            200, json=pipeline
        )
        respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42/config").respond(200, json=config)
        respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/logs/42/11").respond(200, json=logs)

        result = await call(mcp, "explain_pipeline_failure", repo_id=1)

        assert list_route.called
        assert pipeline_route.called
        assert result["pipeline"]["number"] == 42


@pytest.mark.asyncio
async def test_explain_no_failure_found(mcp, bound_client):
    list_response = [
        {"id": 1, "number": 1, "status": "success"},
        {"id": 2, "number": 2, "status": "success"},
    ]

    async with respx.mock:
        route = respx.get(
            f"{BASE_URL}{API_PREFIX}/repos/1/pipelines",
            params={"page": 1, "perPage": 50},
        ).respond(200, json=list_response)

        result = await call(mcp, "explain_pipeline_failure", repo_id=1)

        assert route.called
        assert result["message"] == "no failed pipelines found in this repository"


@pytest.mark.asyncio
async def test_explain_pipeline_not_failure(mcp, bound_client):
    pipeline = _fake_pipeline(status="success")

    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42").respond(
            200, json=pipeline
        )

        result = await call(mcp, "explain_pipeline_failure", repo_id=1, pipeline_number=42)

        assert route.called
        assert result["message"] == "Pipeline #42 is success, not a failure."


@pytest.mark.asyncio
async def test_explain_multi_workflow(mcp, bound_client):
    pipeline = _fake_pipeline(
        workflows=[
            {
                "name": "lint",
                "state": "success",
                "started": 1000010,
                "finished": 1000030,
                "children": [
                    {
                        "id": 20,
                        "pid": 1,
                        "name": "ruff",
                        "state": "success",
                        "exit_code": 0,
                        "started": 1000010,
                        "finished": 1000025,
                        "type": "plugin",
                    },
                ],
            },
            {
                "name": "build",
                "state": "failure",
                "error": "exit code 1",
                "started": 1000030,
                "finished": 1000090,
                "children": [
                    {
                        "id": 21,
                        "pid": 2,
                        "name": "compile",
                        "state": "failure",
                        "exit_code": 1,
                        "started": 1000030,
                        "finished": 1000080,
                        "type": "plugin",
                    },
                ],
            },
        ]
    )
    logs = _fake_logs(["compilation error: syntax error on line 42"])
    config = _fake_config()

    async with respx.mock:
        pipeline_route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42").respond(
            200, json=pipeline
        )
        respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42/config").respond(200, json=config)
        logs_route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/logs/42/21").respond(200, json=logs)

        result = await call(mcp, "explain_pipeline_failure", repo_id=1, pipeline_number=42)

        assert pipeline_route.called
        assert logs_route.called

        assert len(result["workflows"]) == 2
        assert result["workflows"][0]["name"] == "lint"
        assert result["workflows"][0]["state"] == "success"
        assert result["workflows"][1]["name"] == "build"
        assert result["workflows"][1]["state"] == "failure"

        # only the failed step in the failed workflow should have logs
        lint_steps = result["workflows"][0]["steps"]
        assert "logs" not in lint_steps[0]

        build_steps = result["workflows"][1]["steps"]
        assert build_steps[0]["logs"]["total_lines"] == 1
        assert "compilation error" in build_steps[0]["logs"]["text"]


@pytest.mark.asyncio
async def test_explain_pipeline_not_found(mcp, bound_client):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/999").respond(404)

        result = await call(mcp, "explain_pipeline_failure", repo_id=1, pipeline_number=999)

        assert route.called
        assert result["message"] == "Pipeline #999 not found."


@pytest.mark.asyncio
async def test_explain_empty_logs(mcp, bound_client):
    pipeline = _fake_pipeline()
    config = _fake_config()

    async with respx.mock:
        pipeline_route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42").respond(
            200, json=pipeline
        )
        respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42/config").respond(200, json=config)
        logs_route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/logs/42/11").respond(200, json=[])

        result = await call(mcp, "explain_pipeline_failure", repo_id=1, pipeline_number=42)

        assert pipeline_route.called
        assert logs_route.called
        assert result["workflows"][0]["steps"][1]["logs"]["total_lines"] == 0
        assert result["workflows"][0]["steps"][1]["logs"]["text"] == ""
        assert result["workflows"][0]["steps"][1]["logs"]["truncated"] is False


@pytest.mark.asyncio
async def test_explain_log_truncation(mcp, bound_client):
    pipeline = _fake_pipeline()
    config = _fake_config()
    # Generate 250 log lines to exceed the 200 line limit
    log_lines = [f"Log line {i}: some output" for i in range(250)]
    logs = _fake_logs(log_lines)

    async with respx.mock:
        pipeline_route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42").respond(
            200, json=pipeline
        )
        respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42/config").respond(200, json=config)
        logs_route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/logs/42/11").respond(200, json=logs)

        result = await call(mcp, "explain_pipeline_failure", repo_id=1, pipeline_number=42)

        assert pipeline_route.called
        assert logs_route.called

        step_logs = result["workflows"][0]["steps"][1]["logs"]
        # Verify total_lines reflects original count
        assert step_logs["total_lines"] == 250
        # Verify truncation flag is set
        assert step_logs["truncated"] is True
        # Verify text contains only first 200 lines
        text_lines = step_logs["text"].split("\n")
        assert len(text_lines) == 200
        # Verify we have the first line but not lines beyond 200
        assert "Log line 0" in step_logs["text"]
        assert "Log line 199" in step_logs["text"]
        assert "Log line 200" not in step_logs["text"]
        assert "Log line 249" not in step_logs["text"]
