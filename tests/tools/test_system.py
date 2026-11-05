import pytest
import respx

from tests.conftest import BASE_URL, call

API_PREFIX = "/api"


@pytest.mark.asyncio
async def test_get_version(mcp, bound_client):
    fake_version = {"version": "3.16.0", "source": "https://github.com/woodpecker-ci/woodpecker"}
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/version").respond(
            200,
            json=fake_version,
        )
        result = await call(mcp, "get_version")
        assert route.called
        assert result["version"] == "3.16.0"


@pytest.mark.asyncio
async def test_list_queued_pipelines(mcp, bound_client):
    fake_feed = [
        {
            "repo_id": 1,
            "full_name": "testuser/repo-one",
            "number": 791,
            "status": "pending",
            "branch": "main",
            "commit": "abc123",
            "author": "dev",
            "created": 1790000000,
        },
        {
            "repo_id": 2,
            "full_name": "testuser/repo-two",
            "number": 467,
            "status": "running",
            "branch": "staging",
            "commit": "def456",
            "author": "dev",
            "created": 1790000100,
        },
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/pipelines").respond(
            200,
            json=fake_feed,
        )
        result = await call(mcp, "list_queued_pipelines")
        assert route.called
        assert result["items"] == fake_feed


@pytest.mark.asyncio
async def test_get_signature_public_key(mcp, bound_client):
    fake_key = (
        "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A\n-----END PUBLIC KEY-----"
    )
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/signature/public-key").respond(
            200,
            text=fake_key,
        )
        result = await call(mcp, "get_signature_public_key")
        assert route.called
        assert result["public_key"] == fake_key


@pytest.mark.asyncio
async def test_get_queue_info(mcp, bound_client):
    fake_queue = {
        "pending": [],
        "waiting_on_deps": [],
        "running": [{"repo_id": 1, "number": 42}],
        "stats": {"worker_count": 1, "pending_count": 0, "running_count": 1},
        "paused": False,
    }
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/queue/info").respond(
            200,
            json=fake_queue,
        )
        result = await call(mcp, "get_queue_info")
        assert route.called
        assert result["stats"]["running_count"] == 1
        assert result["paused"] is False


@pytest.mark.asyncio
async def test_get_queue_info_empty(mcp, bound_client):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/queue/info").respond(200, content=b"")
        result = await call(mcp, "get_queue_info")
        assert route.called
        assert result == {}


@pytest.mark.asyncio
async def test_get_queue_info_forbidden(mcp, bound_client):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/queue/info").respond(403)
        with pytest.raises(Exception, match="forbidden"):
            await call(mcp, "get_queue_info")
        assert route.called
