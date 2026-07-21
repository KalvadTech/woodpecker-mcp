from mcp.server.fastmcp import FastMCP

from . import repositories


def register_all(mcp: FastMCP) -> None:
    repositories.register(mcp)
