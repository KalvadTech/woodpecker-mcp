import pytest
import respx

from tests.conftest import BASE_URL, call

API_PREFIX = "/api"


@pytest.mark.asyncio
async def test_list_organizations(mcp, bound_client):
    fake_orgs = [
        {"id": 1, "name": "my-org", "forge_id": 1, "is_user": False},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/orgs").respond(
            200,
            json=fake_orgs,
        )
        result = await call(mcp, "list_organizations")
        assert route.called
        assert result["items"] == fake_orgs


@pytest.mark.asyncio
async def test_get_organization(mcp, bound_client):
    fake_org = {"id": 1, "name": "my-org", "forge_id": 1}
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/orgs/1").respond(
            200,
            json=fake_org,
        )
        result = await call(mcp, "get_organization", org_id=1)
        assert route.called
        assert result == fake_org


@pytest.mark.asyncio
async def test_get_org_permissions(mcp, bound_client):
    fake_perms = {"admin": True, "member": True}
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/orgs/1/permissions").respond(
            200,
            json=fake_perms,
        )
        result = await call(mcp, "get_org_permissions", org_id=1)
        assert route.called
        assert result == fake_perms
