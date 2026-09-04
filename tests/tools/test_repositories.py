import pytest
import respx

from tests.conftest import BASE_URL, call

API_PREFIX = "/api"


@pytest.mark.asyncio
async def test_search_repositories(mcp, bound_client):
    fake_repos = [
        {"id": 1, "name": "repo-one", "owner": "testuser", "active": True},
        {"id": 2, "name": "repo-two", "owner": "testuser", "active": False},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos").respond(
            200,
            json=fake_repos,
        )
        result = await call(mcp, "search_repositories")
        assert route.called
        assert result["items"] == fake_repos
        assert result["page"] == 1


@pytest.mark.asyncio
async def test_search_repositories_with_query(mcp, bound_client):
    fake_repos = [
        {"id": 1, "name": "repo-one", "owner": "testuser", "active": True},
    ]
    async with respx.mock:
        route = respx.get(
            f"{BASE_URL}{API_PREFIX}/repos",
            params={"query": "repo-one", "page": 1, "perPage": 50},
        ).respond(200, json=fake_repos)
        result = await call(mcp, "search_repositories", query="repo-one")
        assert route.called
        assert result["items"] == fake_repos


@pytest.mark.asyncio
async def test_get_repository(mcp, bound_client):
    fake_repo = {"id": 1, "name": "repo-one", "owner": "testuser", "active": True}
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1").respond(200, json=fake_repo)
        result = await call(mcp, "get_repository", repo_id=1)
        assert route.called
        assert result == fake_repo


@pytest.mark.asyncio
async def test_list_branches(mcp, bound_client):
    fake_branches = [
        {"name": "main", "commit": "abc123"},
        {"name": "develop", "commit": "def456"},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/branches").respond(
            200,
            json=fake_branches,
        )
        result = await call(mcp, "list_branches", repo_id=1)
        assert route.called
        assert result["branches"] == fake_branches


@pytest.mark.asyncio
async def test_list_pull_requests(mcp, bound_client):
    fake_prs = [
        {"number": 1, "title": "Fix bug", "state": "open"},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pull_requests").respond(
            200,
            json=fake_prs,
        )
        result = await call(mcp, "list_pull_requests", repo_id=1)
        assert route.called
        assert result["pull_requests"] == fake_prs


@pytest.mark.asyncio
async def test_repair_repository(mcp, bound_client):
    async with respx.mock:
        route = respx.post(f"{BASE_URL}{API_PREFIX}/repos/1/repair").respond(
            200,
            json={"status": "ok"},
        )
        result = await call(mcp, "repair_repository", repo_id=1)
        assert route.called
        assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_activate_repository(mcp, bound_client):
    fake_repo = {"id": 1, "full_name": "testuser/repo-one", "active": True}
    async with respx.mock:
        route = respx.post(
            f"{BASE_URL}{API_PREFIX}/repos",
            params={"forge_remote_id": "123456"},
        ).respond(200, json=fake_repo)
        result = await call(mcp, "activate_repository", forge_remote_id="123456")
        assert route.called
        assert result == fake_repo


@pytest.mark.asyncio
async def test_deactivate_repository(mcp, bound_client):
    async with respx.mock:
        route = respx.delete(f"{BASE_URL}{API_PREFIX}/repos/1").respond(200, json={})
        result = await call(mcp, "deactivate_repository", repo_id=1)
        assert route.called
        assert result == {"deleted": True}


@pytest.mark.asyncio
async def test_get_repository_not_found(mcp, bound_client):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/999").respond(404)
        with pytest.raises(Exception, match="not found"):
            await call(mcp, "get_repository", repo_id=999)
        assert route.called
