import pytest
import respx

from tests.conftest import BASE_URL, call

API_PREFIX = "/api"


@pytest.mark.asyncio
async def test_list_cron_jobs(mcp, bound_client):
    fake_crons = [
        {"id": 1, "name": "nightly", "schedule": "0 0 * * *", "branch": "main"},
    ]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/repos/1/cron").respond(
            200,
            json=fake_crons,
        )
        result = await call(mcp, "list_cron_jobs", repo_id=1)
        assert route.called
        assert result["items"] == fake_crons


@pytest.mark.asyncio
async def test_create_cron_job(mcp, bound_client):
    async with respx.mock:
        route = respx.post(
            f"{BASE_URL}{API_PREFIX}/repos/1/cron",
            json={"name": "daily", "schedule": "0 6 * * *", "branch": "main"},
        ).respond(200, json={"id": 2, "name": "daily"})
        result = await call(mcp, "create_cron_job", repo_id=1, name="daily", schedule="0 6 * * *")
        assert route.called
        assert result["name"] == "daily"


@pytest.mark.asyncio
async def test_delete_cron_job(mcp, bound_client):
    async with respx.mock:
        route = respx.delete(f"{BASE_URL}{API_PREFIX}/repos/1/cron/5").respond(204)
        result = await call(mcp, "delete_cron_job", repo_id=1, cron_id=5)
        assert route.called
        assert result["deleted"] is True


@pytest.mark.asyncio
async def test_trigger_cron_job(mcp, bound_client):
    async with respx.mock:
        route = respx.post(f"{BASE_URL}{API_PREFIX}/repos/1/cron/5").respond(
            200, json={"id": 10, "status": "pending"}
        )
        result = await call(mcp, "trigger_cron_job", repo_id=1, cron_id=5)
        assert route.called
        assert result["status"] == "pending"
