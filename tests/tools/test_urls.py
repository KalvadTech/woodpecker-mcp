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
        "author": "testuser",
        "commit": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
        "message": "Update landing page",
        "title": "Update landing page",
        "workflows": [
            {"name": "django_test", "state": "success", "started": 100, "finished": 366},
            {"name": "ruff", "state": "success", "started": 100, "finished": 138},
        ],
    }
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/422").respond(
            200, json=fake_pipeline
        )
        raw = await call(
            mcp,
            "open_woodpecker_url",
            url=f"{BASE_URL}/repos/1/pipeline/422",
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
        "full_name": "testuser/repo-one",
        "forge_url": "https://github.com/testuser/repo-one",
        "default_branch": "main",
        "visibility": "private",
        "active": True,
        "timeout": 60,
    }
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1").respond(
            200,
            json=fake_repo,
        )
        raw = await call(
            mcp,
            "open_woodpecker_url",
            url=f"{BASE_URL}/repos/1",
        )
        result = raw["result"] if isinstance(raw, dict) else raw
        assert route.called
        assert "testuser/repo-one" in result
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
