import pytest
import respx

from tests.conftest import BASE_URL

API_PREFIX = "/api"

FAKE_REPO = {
    "id": 1,
    "full_name": "testuser/repo-one",
    "forge_url": "https://github.com/testuser/repo-one",
    "default_branch": "main",
    "visibility": "public",
    "active": True,
    "timeout": 60,
}

FAKE_PIPELINE = {
    "number": 42,
    "status": "success",
    "branch": "main",
    "event": "push",
    "author": "testuser",
    "commit": "abc123",
    "message": "fix: something",
    "workflows": [
        {
            "name": "build",
            "state": "success",
            "started": 1000,
            "finished": 1060,
        }
    ],
}

FAKE_USER = {
    "id": 7,
    "login": "testuser",
    "email": "test@example.com",
    "admin": True,
}


@pytest.mark.asyncio
async def test_list_resource_templates(mcp, bound_client):
    templates = await mcp.list_resource_templates()
    uris = {t.uri_template for t in templates}
    assert "woodpecker://repo/{repo_id}" in uris
    assert "woodpecker://pipeline/{repo_id}/{pipeline_number}" in uris


@pytest.mark.asyncio
async def test_list_resources_contains_static(mcp, bound_client):
    resources = await mcp.list_resources()
    uris = {r.uri for r in resources}
    assert "woodpecker://self" in uris


@pytest.mark.asyncio
async def test_read_repo_resource(mcp, bound_client):
    async with respx.mock:
        respx.get(f"{BASE_URL}{API_PREFIX}/repos/1").respond(200, json=FAKE_REPO)
        contents = [c for c in await mcp.read_resource("woodpecker://repo/1")]
        assert len(contents) == 1
        text = contents[0].content
        assert isinstance(text, str)
        assert "# testuser/repo-one" in text
        assert "**Default branch:** main" in text


@pytest.mark.asyncio
async def test_read_pipeline_resource(mcp, bound_client):
    async with respx.mock:
        respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/pipelines/42").respond(200, json=FAKE_PIPELINE)
        contents = [c for c in await mcp.read_resource("woodpecker://pipeline/1/42")]
        assert len(contents) == 1
        text = contents[0].content
        assert isinstance(text, str)
        assert "# Pipeline #42" in text
        assert "| build | success | 60s |" in text


@pytest.mark.asyncio
async def test_read_self_resource(mcp, bound_client):
    async with respx.mock:
        respx.get(f"{BASE_URL}{API_PREFIX}/user").respond(200, json=FAKE_USER)
        contents = [c for c in await mcp.read_resource("woodpecker://self")]
        assert len(contents) == 1
        text = contents[0].content
        assert isinstance(text, str)
        assert "# testuser" in text
        assert "**Email:** test@example.com" in text


@pytest.mark.asyncio
async def test_read_resource_not_found(mcp, bound_client):
    async with respx.mock:
        respx.get(f"{BASE_URL}{API_PREFIX}/repos/999").respond(404)
        contents = [c for c in await mcp.read_resource("woodpecker://repo/999")]
        assert len(contents) == 1
        text = contents[0].content
        assert isinstance(text, str)
        assert "**Error:** not found" in text
