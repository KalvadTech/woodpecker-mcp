from __future__ import annotations

import httpx
import pytest
import respx

from tests.conftest import BASE_URL
from woodpecker_mcp.client import WoodpeckerClient
from woodpecker_mcp.errors import WoodpeckerError

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


@pytest.mark.asyncio
async def test_retry_on_500_error(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(500),
            httpx.Response(200, json={"id": 1}),
        ]
        result = await client.get_json("/items")
        assert result == {"id": 1}
        assert route.call_count == 3


@pytest.mark.asyncio
async def test_retry_on_502_error(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [
            httpx.Response(502),
            httpx.Response(200, json={"id": 1}),
        ]
        result = await client.get_json("/items")
        assert result == {"id": 1}
        assert route.call_count == 2


@pytest.mark.asyncio
async def test_retry_on_503_error(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [
            httpx.Response(503),
            httpx.Response(200, json={"id": 1}),
        ]
        result = await client.get_json("/items")
        assert result == {"id": 1}
        assert route.call_count == 2


@pytest.mark.asyncio
async def test_retry_on_504_error(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [
            httpx.Response(504),
            httpx.Response(200, json={"id": 1}),
        ]
        result = await client.get_json("/items")
        assert result == {"id": 1}
        assert route.call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted_on_500(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(500),
            httpx.Response(500),
            httpx.Response(500),
        ]
        with pytest.raises(WoodpeckerError) as exc_info:
            await client.get_json("/items")
        assert exc_info.value.status == 500
        assert route.call_count == 4


@pytest.mark.asyncio
async def test_retry_on_429_with_retry_after(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "0.1"}),
            httpx.Response(200, json={"id": 1}),
        ]
        result = await client.get_json("/items")
        assert result == {"id": 1}
        assert route.call_count == 2


@pytest.mark.asyncio
async def test_no_retry_on_400_error(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [httpx.Response(400)]
        with pytest.raises(WoodpeckerError) as exc_info:
            await client.get_json("/items")
        assert exc_info.value.status == 400
        assert route.call_count == 1


@pytest.mark.asyncio
async def test_no_retry_on_401_error(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [httpx.Response(401)]
        with pytest.raises(WoodpeckerError) as exc_info:
            await client.get_json("/items")
        assert exc_info.value.status == 401
        assert route.call_count == 1


@pytest.mark.asyncio
async def test_no_retry_on_403_error(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [httpx.Response(403)]
        with pytest.raises(WoodpeckerError) as exc_info:
            await client.get_json("/items")
        assert exc_info.value.status == 403
        assert route.call_count == 1


@pytest.mark.asyncio
async def test_no_retry_on_404_error(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [httpx.Response(404)]
        with pytest.raises(WoodpeckerError) as exc_info:
            await client.get_json("/items")
        assert exc_info.value.status == 404
        assert route.call_count == 1


@pytest.mark.asyncio
async def test_get_retries_by_default(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(200, json={"id": 1}),
        ]
        result = await client.get_json("/items")
        assert result == {"id": 1}
        assert route.call_count == 2


@pytest.mark.asyncio
async def test_delete_retries_by_default(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.delete(f"{BASE_URL}{API_PREFIX}/items/1")
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(204),
        ]
        await client.delete("/items/1")
        assert route.call_count == 2


@pytest.mark.asyncio
async def test_post_does_not_retry_by_default(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.post(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [httpx.Response(500)]
        with pytest.raises(WoodpeckerError) as exc_info:
            await client.post_json("/items", json={"name": "test"})
        assert exc_info.value.status == 500
        assert route.call_count == 1


@pytest.mark.asyncio
async def test_post_retries_when_enabled(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.post(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(200, json={"id": 1}),
        ]
        result = await client.post_json("/items", json={"name": "test"}, retry=True)
        assert result == {"id": 1}
        assert route.call_count == 2


@pytest.mark.asyncio
async def test_custom_max_retries():
    async with WoodpeckerClient(BASE_URL, "test-token", max_retries=1) as client, respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(500),
            httpx.Response(500),
        ]
        with pytest.raises(WoodpeckerError) as exc_info:
            await client.get_json("/items")
        assert exc_info.value.status == 500
        assert route.call_count == 2


@pytest.mark.asyncio
async def test_disable_retries():
    async with WoodpeckerClient(BASE_URL, "test-token", max_retries=0) as client, respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(200, json={"id": 1}),
        ]
        with pytest.raises(WoodpeckerError) as exc_info:
            await client.get_json("/items")
        assert exc_info.value.status == 500
        assert route.call_count == 1


@pytest.mark.asyncio
async def test_override_retry_false(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [httpx.Response(500)]
        with pytest.raises(WoodpeckerError) as exc_info:
            await client.get_json("/items", retry=False)
        assert exc_info.value.status == 500
        assert route.call_count == 1


@pytest.mark.asyncio
async def test_retry_on_connect_error(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [
            httpx.ConnectError("Connection failed"),
            httpx.Response(200, json={"id": 1}),
        ]
        result = await client.get_json("/items")
        assert result == {"id": 1}
        assert route.call_count == 2


@pytest.mark.asyncio
async def test_retry_on_timeout_error(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [
            httpx.ReadTimeout("Timeout"),
            httpx.Response(200, json={"id": 1}),
        ]
        result = await client.get_json("/items")
        assert result == {"id": 1}
        assert route.call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted_on_connect_error(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [httpx.ConnectError("Connection failed")] * 5
        with pytest.raises(httpx.ConnectError):
            await client.get_json("/items")
        assert route.call_count == 4


@pytest.mark.asyncio
async def test_retry_exhausted_on_timeout_error(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.get(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [httpx.ReadTimeout("Timeout")] * 5
        with pytest.raises(httpx.ReadTimeout):
            await client.get_json("/items")
        assert route.call_count == 4


@pytest.mark.asyncio
async def test_no_retry_on_connect_error_for_post(client: WoodpeckerClient):
    async with respx.mock:
        route = respx.post(f"{BASE_URL}{API_PREFIX}/items")
        route.side_effect = [httpx.ConnectError("Connection failed")]
        with pytest.raises(httpx.ConnectError):
            await client.post_json("/items", json={"name": "test"})
        assert route.call_count == 1


@pytest.mark.asyncio
async def test_calculate_delay_exponential_backoff(client: WoodpeckerClient):
    delay0 = client._calculate_delay(0)
    delay1 = client._calculate_delay(1)
    delay2 = client._calculate_delay(2)

    assert 1.0 <= delay0 < 2.0
    assert 2.0 <= delay1 < 3.0
    assert 4.0 <= delay2 < 5.0


@pytest.mark.asyncio
async def test_calculate_delay_respects_max(client: WoodpeckerClient):
    delay = client._calculate_delay(10)
    assert delay <= 10.0


@pytest.mark.asyncio
async def test_calculate_delay_with_retry_after(client: WoodpeckerClient):
    delay = client._calculate_delay(0, "5.0")
    assert delay == 5.0


@pytest.mark.asyncio
async def test_calculate_delay_with_invalid_retry_after(client: WoodpeckerClient):
    delay = client._calculate_delay(0, "invalid")
    assert 1.0 <= delay < 2.0
