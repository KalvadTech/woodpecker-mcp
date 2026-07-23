from mcp.server.fastmcp import FastMCP

from . import (
    agents,
    cron,
    forges,
    logs,
    organizations,
    pipelines,
    repositories,
    secrets,
    system,
    urls,
    users,
)


def register_all(mcp: FastMCP) -> None:
    agents.register(mcp)
    cron.register(mcp)
    forges.register(mcp)
    logs.register(mcp)
    organizations.register(mcp)
    pipelines.register(mcp)
    repositories.register(mcp)
    secrets.register(mcp)
    system.register(mcp)
    urls.register(mcp)
    users.register(mcp)
