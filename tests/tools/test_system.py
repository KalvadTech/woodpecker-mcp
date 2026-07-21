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
async def test_get_queue_info(mcp, bound_client):
    fake_queue = {"running": 2, "pending": 5, "stats": {}}
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/queue").respond(
            200,
            json=fake_queue,
        )
        result = await call(mcp, "get_queue_info")
        assert route.called
        assert result["running"] == 2
