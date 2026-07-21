import pytest
import respx

from tests.conftest import BASE_URL, call

API_PREFIX = "/api"


@pytest.mark.asyncio
async def test_list_forges(mcp, bound_client):
    fake_forges = [
        {"id": 1, "type": "github", "url": "https://github.com"},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/forges").respond(
            200,
            json=fake_forges,
        )
        result = await call(mcp, "list_forges")
        assert route.called
        assert result["items"] == fake_forges
