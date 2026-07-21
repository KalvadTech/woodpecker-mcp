from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from woodpecker_mcp.client import (
    WoodpeckerClient,
    reset_current_client,
    set_current_client,
)
from woodpecker_mcp.tools import register_all

BASE_URL = "https://woodpecker.test"
API_TOKEN = "woodpecker-test-token-1234567890abcdef"


@pytest.fixture
def mcp() -> FastMCP:
    server = FastMCP("woodpecker-test")
    register_all(server)
    return server


@pytest.fixture
async def bound_client() -> AsyncIterator[WoodpeckerClient]:
    client = WoodpeckerClient(BASE_URL, API_TOKEN)
    token = set_current_client(client)
    try:
        yield client
    finally:
        reset_current_client(token)
        await client.aclose()


async def call(mcp: FastMCP, tool_name: str, /, **arguments: Any) -> Any:
    result = await mcp.call_tool(tool_name, arguments)
    if isinstance(result, tuple) and len(result) == 2:
        _, structured = result
        if structured is not None:
            return structured
        result = result[0]
    if isinstance(result, dict):
        return result
    if not result:
        return None
    block = result[0]
    if isinstance(block, TextContent):
        try:
            return json.loads(block.text)
        except json.JSONDecodeError:
            return block.text
    return block
