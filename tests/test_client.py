from __future__ import annotations

import pytest
import respx

from tests.conftest import BASE_URL
from woodpecker_mcp.client import WoodpeckerClient

API_PREFIX = "/api"


@pytest.fixture
async def client() -> WoodpeckerClient:
    async with WoodpeckerClient(BASE_URL, "test-token") as c:
        yield c


@pytest.mark.asyncio
async def test_paginate_defaults(client: WoodpeckerClient):
    fake_data = [{"id": 1}, {"id": 2}]
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items").respond(200, json=fake_data)
        result = await client.paginate("/items")

        assert route.called
        assert result["items"] == fake_data
        assert result["page"] == 1
        assert result["per_page"] == 50


@pytest.mark.asyncio
async def test_paginate_custom_page_and_per_page(client: WoodpeckerClient):
    fake_data = [{"id": 1}]
    async with respx.mock:
        route = respx.get(
            f"{BASE_URL}{API_PREFIX}/items",
            params={"page": "3", "perPage": "25"},
        ).respond(200, json=fake_data)
        result = await client.paginate("/items", page=3, per_page=25)

        assert route.called
        assert result["items"] == fake_data
        assert result["page"] == 3
        assert result["per_page"] == 25


@pytest.mark.asyncio
async def test_paginate_with_extra_params(client: WoodpeckerClient):
    fake_data = [{"id": 1}]
    async with respx.mock:
        route = respx.get(
            f"{BASE_URL}{API_PREFIX}/items",
            params={"page": "1", "perPage": "50", "status": "active"},
        ).respond(200, json=fake_data)
        result = await client.paginate("/items", params={"status": "active"})

        assert route.called
        assert result["items"] == fake_data
        assert result["page"] == 1
        assert result["per_page"] == 50


@pytest.mark.asyncio
async def test_paginate_caps_per_page_at_max(client: WoodpeckerClient):
    fake_data = [{"id": 1}]
    async with respx.mock:
        route = respx.get(
            f"{BASE_URL}{API_PREFIX}/items",
            params={"page": "1", "perPage": "100"},
        ).respond(200, json=fake_data)
        result = await client.paginate("/items", per_page=500)

        assert route.called
        assert result["items"] == fake_data
        assert result["per_page"] == 100


@pytest.mark.asyncio
async def test_paginate_wraps_list_response(client: WoodpeckerClient):
    fake_list = [{"id": 1}, {"id": 2}, {"id": 3}]
    async with respx.mock:
        respx.get(f"{BASE_URL}{API_PREFIX}/items").respond(200, json=fake_list)
        result = await client.paginate("/items")

        assert result["items"] == fake_list
        assert isinstance(result["items"], list)
        assert len(result["items"]) == 3


@pytest.mark.asyncio
async def test_paginate_wraps_non_list_response(client: WoodpeckerClient):
    fake_dict = {"data": [{"id": 1}], "total": 100}
    async with respx.mock:
        respx.get(f"{BASE_URL}{API_PREFIX}/items").respond(200, json=fake_dict)
        result = await client.paginate("/items")

        assert result["items"] == fake_dict
        assert result["page"] == 1
        assert result["per_page"] == 50


@pytest.mark.asyncio
async def test_paginate_empty_response(client: WoodpeckerClient):
    async with respx.mock:
        respx.get(f"{BASE_URL}{API_PREFIX}/items").respond(200, json=[])
        result = await client.paginate("/items")

        assert result["items"] == []
        assert result["page"] == 1
        assert result["per_page"] == 50
