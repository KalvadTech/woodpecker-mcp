import pytest
import respx

from tests.conftest import BASE_URL, call

API_PREFIX = "/api"


@pytest.mark.asyncio
async def test_list_pipelines(mcp, bound_client):
    fake_pipelines = [
        {"id": 1, "status": "success", "branch": "main"},
        {"id": 2, "status": "running", "branch": "develop"},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines").respond(
            200,
            json=fake_pipelines,
        )
        result = await call(mcp, "list_pipelines", repo_id=1)
        assert route.called
        assert result["items"] == fake_pipelines


@pytest.mark.asyncio
async def test_get_pipeline(mcp, bound_client):
    fake_pipeline = {"id": 1, "status": "success", "branch": "main"}
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42").respond(
            200, json=fake_pipeline
        )
        result = await call(mcp, "get_pipeline", repo_id=1, pipeline_id=42)
        assert route.called
        assert result == fake_pipeline


@pytest.mark.asyncio
async def test_trigger_pipeline(mcp, bound_client):
    async with respx.mock:
        route = respx.post(
            f"{BASE_URL}{API_PREFIX}/repos/1/pipelines",
            json={"branch": "main"},
        ).respond(200, json={"id": 3, "status": "pending"})
        result = await call(mcp, "trigger_pipeline", repo_id=1)
        assert route.called
        assert result["status"] == "pending"


@pytest.mark.asyncio
async def test_trigger_pipeline_with_variables(mcp, bound_client):
    async with respx.mock:
        route = respx.post(
            f"{BASE_URL}{API_PREFIX}/repos/1/pipelines",
            json={"branch": "feature", "variables": {"KEY": "value"}},
        ).respond(200, json={"id": 4, "status": "pending"})
        result = await call(
            mcp, "trigger_pipeline", repo_id=1, branch="feature", variables={"KEY": "value"}
        )
        assert route.called
        assert result["id"] == 4


@pytest.mark.asyncio
async def test_restart_pipeline(mcp, bound_client):
    async with respx.mock:
        route = respx.post(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42").respond(
            200, json={"id": 5, "status": "pending"}
        )
        result = await call(mcp, "restart_pipeline", repo_id=1, pipeline_id=42)
        assert route.called
        assert result["id"] == 5


@pytest.mark.asyncio
async def test_cancel_pipeline(mcp, bound_client):
    async with respx.mock:
        route = respx.post(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42/cancel").respond(
            200, json={"id": 42, "status": "cancelled"}
        )
        result = await call(mcp, "cancel_pipeline", repo_id=1, pipeline_id=42)
        assert route.called
        assert result["status"] == "cancelled"


@pytest.mark.asyncio
async def test_approve_pipeline(mcp, bound_client):
    async with respx.mock:
        route = respx.post(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42/approve").respond(
            200, json={"id": 42, "status": "running"}
        )
        result = await call(mcp, "approve_pipeline", repo_id=1, pipeline_id=42)
        assert route.called
        assert result["status"] == "running"


@pytest.mark.asyncio
async def test_get_pipeline_config(mcp, bound_client):
    fake_config = [
        {"name": ".woodpecker.yml", "data": "pipeline:\n  test:\n    image: alpine"},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42/config").respond(
            200, json=fake_config
        )
        result = await call(mcp, "get_pipeline_config", repo_id=1, pipeline_id=42)
        assert route.called
        assert result["configs"] == fake_config


@pytest.mark.asyncio
async def test_rerun_last_failed(mcp, bound_client):
    async with respx.mock:
        list_route = respx.get(
            f"{BASE_URL}{API_PREFIX}/repos/1/pipelines",
            params={"page": 1, "perPage": 50},
        ).respond(
            200,
            json=[
                {"id": 1, "status": "success"},
                {"id": 2, "status": "failure"},
            ],
        )
        restart_route = respx.post(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/2").respond(
            200, json={"id": 3, "status": "pending"}
        )
        result = await call(mcp, "rerun_last_failed", repo_id=1)
        assert list_route.called
        assert restart_route.called
        assert result["id"] == 3


@pytest.mark.asyncio
async def test_rerun_last_failed_none_found(mcp, bound_client):
    async with respx.mock:
        route = respx.get(
            f"{BASE_URL}{API_PREFIX}/repos/1/pipelines",
            params={"page": 1, "perPage": 50},
        ).respond(200, json=[{"id": 1, "status": "success"}])
        result = await call(mcp, "rerun_last_failed", repo_id=1)
        assert route.called
        assert result["message"] == "no failed pipelines found"
