import pytest
import respx

from tests.conftest import BASE_URL, call

API_PREFIX = "/api"


@pytest.mark.asyncio
async def test_open_pipeline_url(mcp, bound_client):
    fake_pipeline = {
        "number": 422,
        "status": "success",
        "branch": "main",
        "event": "pull_request",
        "author": "59-29",
        "commit": "7a0d315ea70b3945ba6ecbd6d6e1b29a367f704b",
        "message": "UAE Pass",
        "title": "UAE Pass",
        "workflows": [
            {"name": "django_test", "state": "success", "started": 100, "finished": 366},
            {"name": "ruff", "state": "success", "started": 100, "finished": 138},
        ],
    }
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/11/pipelines/422").respond(
            200, json=fake_pipeline
        )
        raw = await call(
            mcp,
            "open_woodpecker_url",
            url=f"{BASE_URL}/repos/11/pipeline/422",
        )
        result = raw["result"] if isinstance(raw, dict) else raw
        assert route.called
        assert "Pipeline #422" in result
        assert "success" in result
        assert "django_test" in result
        assert "266s" in result


@pytest.mark.asyncio
async def test_open_repo_url(mcp, bound_client):
    fake_repo = {
        "full_name": "KalvadTech/GSR-Backend",
        "forge_url": "https://github.com/KalvadTech/GSR-Backend",
        "default_branch": "main",
        "visibility": "private",
        "active": True,
        "timeout": 60,
    }
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/11").respond(
            200,
            json=fake_repo,
        )
        raw = await call(
            mcp,
            "open_woodpecker_url",
            url=f"{BASE_URL}/repos/11",
        )
        result = raw["result"] if isinstance(raw, dict) else raw
        assert route.called
        assert "KalvadTech/GSR-Backend" in result
        assert "private" in result


@pytest.mark.asyncio
async def test_open_url_wrong_instance(mcp, bound_client):
    raw = await call(
        mcp,
        "open_woodpecker_url",
        url="https://other.ci.example.com/repos/11/pipeline/422",
    )
    result = raw["result"] if isinstance(raw, dict) else raw
    assert "does not belong to the configured" in result


@pytest.mark.asyncio
async def test_open_url_unsupported_path(mcp, bound_client):
    raw = await call(
        mcp,
        "open_woodpecker_url",
        url=f"{BASE_URL}/users/5",
    )
    result = raw["result"] if isinstance(raw, dict) else raw
    assert "Unsupported Woodpecker URL" in result
