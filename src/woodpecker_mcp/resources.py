from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from .errors import WoodpeckerError
from .formatting import format_pipeline, format_repo
from .tools._common import client


def register_resources(mcp: MCPServer) -> None:
    @mcp.resource(
        "woodpecker://repo/{repo_id}",
        name="repo",
        mime_type="text/markdown",
    )
    async def repo(repo_id: int) -> str:
        """A repository's details as Markdown, by internal Woodpecker ID.

        Args:
            repo_id: The internal Woodpecker repository ID.
        """
        try:
            return format_repo(await client().get_json(f"/repos/{repo_id}"))
        except WoodpeckerError as e:
            return f"**Error:** {e.message}"

    @mcp.resource(
        "woodpecker://pipeline/{repo_id}/{pipeline_number}",
        name="pipeline",
        mime_type="text/markdown",
    )
    async def pipeline(repo_id: int, pipeline_number: int) -> str:
        """A pipeline's details as Markdown, by repo ID and pipeline number.

        Args:
            repo_id: The internal Woodpecker repository ID.
            pipeline_number: The pipeline number (e.g. 42).
        """
        try:
            data = await client().get_json(f"/repos/{repo_id}/pipelines/{pipeline_number}")
            return format_pipeline(data)
        except WoodpeckerError as e:
            return f"**Error:** {e.message}"

    @mcp.resource(
        "woodpecker://self",
        name="current_user",
        mime_type="text/markdown",
    )
    async def current_user() -> str:
        """The currently authenticated user as Markdown."""
        try:
            data = await client().get_json("/user")
        except WoodpeckerError as e:
            return f"**Error:** {e.message}"
        return "\n".join(
            [
                f"# {data.get('login', '')}",
                "",
                f"**ID:** {data.get('id', '')}",
                f"**Email:** {data.get('email', '')}",
                f"**Admin:** {data.get('admin', False)}",
            ]
        )
