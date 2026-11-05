from __future__ import annotations

import pytest
from mcp.server.mcpserver import MCPServer

from woodpecker_mcp.server import build_mcp
from woodpecker_mcp.tools import register_all


@pytest.mark.asyncio
async def test_server_metadata():
    server = build_mcp()
    assert server.name == "woodpecker"
    assert server.title == "Woodpecker CI"
    assert server.version
    assert "untrusted input" in (server.instructions or "")


@pytest.mark.asyncio
async def test_all_tools_have_annotations(mcp):
    tools = await mcp.list_tools()
    assert len(tools) == 51
    assert all(t.annotations is not None for t in tools)


@pytest.mark.asyncio
async def test_read_tools_are_marked_read_only(mcp):
    tools = {t.name: t for t in await mcp.list_tools()}
    for name in ("list_pipelines", "get_step_logs", "search_repositories", "get_queue_info"):
        assert tools[name].annotations.read_only_hint is True


@pytest.mark.asyncio
async def test_write_and_destructive_tools_are_marked(mcp):
    tools = {t.name: t for t in await mcp.list_tools()}

    assert tools["trigger_pipeline"].annotations.read_only_hint is False
    assert tools["trigger_pipeline"].annotations.destructive_hint is False

    for name in ("cancel_pipeline", "delete_repo_secret", "deactivate_repository"):
        assert tools[name].annotations.read_only_hint is False
        assert tools[name].annotations.destructive_hint is True


@pytest.mark.asyncio
async def test_read_only_mode_hides_write_tools(monkeypatch):
    monkeypatch.setenv("MCP_READ_ONLY", "true")
    server = MCPServer("woodpecker-read-only")
    register_all(server)

    names = {t.name for t in await server.list_tools()}
    assert "list_pipelines" in names
    assert "get_step_logs" in names
    assert "trigger_pipeline" not in names
    assert "cancel_pipeline" not in names
    assert "delete_repo_secret" not in names
