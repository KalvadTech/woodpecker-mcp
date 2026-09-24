import pytest
import respx

from tests.conftest import BASE_URL, call

API_PREFIX = "/api"


@pytest.mark.asyncio
async def test_list_users(mcp, bound_client):
    fake_users = [
        {"id": 1, "login": "admin", "admin": True},
        {"id": 2, "login": "dev", "admin": False},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/users").respond(
            200,
            json=fake_users,
        )
        result = await call(mcp, "list_users")
        assert route.called
        assert result["items"] == fake_users


@pytest.mark.asyncio
async def test_get_current_user(mcp, bound_client):
    fake_user = {"id": 1, "login": "admin", "admin": True}
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/user").respond(
            200,
            json=fake_user,
        )
        result = await call(mcp, "get_current_user")
        assert route.called
        assert result == fake_user


@pytest.mark.asyncio
async def test_get_user_repos(mcp, bound_client):
    fake_repos = [
        {"id": 1, "full_name": "testuser/repo-one", "active": True, "last_pipeline": None},
        {"id": 2, "full_name": "testuser/repo-two", "active": True, "last_pipeline": None},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/user/repos").respond(
            200,
            json=fake_repos,
        )
        result = await call(mcp, "get_user_repos")
        assert route.called
        assert result["repos"] == fake_repos


@pytest.mark.asyncio
async def test_get_user_repos_with_filters(mcp, bound_client):
    fake_repos = [
        {"id": 1, "full_name": "testuser/repo-one", "active": True, "last_pipeline": None},
    ]
    async with respx.mock:
        route = respx.get(
            f"{BASE_URL}{API_PREFIX}/user/repos",
            params={"all": True, "name": "repo"},
        ).respond(200, json=fake_repos)
        result = await call(mcp, "get_user_repos", include_inactive=True, name="repo")
        assert route.called
        assert result["repos"] == fake_repos


@pytest.mark.asyncio
async def test_get_user_feed(mcp, bound_client):
    fake_feed = [
        {"id": 42, "status": "success", "repo_id": 1},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/user/feed").respond(
            200,
            json=fake_feed,
        )
        result = await call(mcp, "get_user_feed")
        assert route.called
        assert result["items"] == fake_feed
