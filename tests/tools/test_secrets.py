import pytest
import respx

from tests.conftest import BASE_URL, call

API_PREFIX = "/api"


@pytest.mark.asyncio
async def test_list_repo_secrets(mcp, bound_client):
    fake_secrets = [
        {"id": 1, "name": "DOCKER_TOKEN"},
        {"id": 2, "name": "API_KEY"},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/secrets").respond(
            200,
            json=fake_secrets,
        )
        result = await call(mcp, "list_repo_secrets", repo_id=1)
        assert route.called
        assert result["items"] == fake_secrets


@pytest.mark.asyncio
async def test_create_repo_secret(mcp, bound_client):
    async with respx.mock:
        route = respx.post(
            f"{BASE_URL}{API_PREFIX}/repos/1/secrets",
            json={"name": "MY_SECRET", "value": "supersecret"},
        ).respond(200, json={"name": "MY_SECRET"})
        result = await call(
            mcp, "create_repo_secret", repo_id=1, name="MY_SECRET", value="supersecret"
        )
        assert route.called
        assert result["name"] == "MY_SECRET"


@pytest.mark.asyncio
async def test_delete_repo_secret(mcp, bound_client):
    async with respx.mock:
        route = respx.delete(f"{BASE_URL}{API_PREFIX}/repos/1/secrets/MY_SECRET").respond(204)
        result = await call(mcp, "delete_repo_secret", repo_id=1, secret_name="MY_SECRET")
        assert route.called
        assert result["deleted"] is True
