from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit

from mcp.server.mcpserver import MCPServer

from ._common import client

_REPO_PATTERN = re.compile(r"^/repos/(\d+)$")
_PIPELINE_PATTERN = re.compile(r"^/repos/(\d+)/pipeline/(\d+)$")


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    async def open_woodpecker_url(url: str) -> str:
        """Open a Woodpecker URL and return the entity as Markdown.

        Use this when the user pastes a Woodpecker link (e.g.
        https://ci.example.com/repos/11/pipeline/422) and the automatic
        resource template was not used by the client.

        Args:
            url: A Woodpecker URL pointing to a repository or pipeline.
                 Supported formats:
                 - https://ci.example.com/repos/<id>
                 - https://ci.example.com/repos/<id>/pipeline/<id>

        Returns:
            Markdown-formatted string with entity details, or an error message
            if the URL is unsupported or doesn't belong to the configured instance.
        """
        c = client()
        base_url = c.base_url
        parsed = urlsplit(url)
        base_parsed = urlsplit(base_url)

        if parsed.scheme != base_parsed.scheme or parsed.netloc != base_parsed.netloc:
            return (
                f"The URL {url} does not belong to the configured Woodpecker instance ({base_url})."
            )

        relative = parsed.path.rstrip("/")

        if match := _PIPELINE_PATTERN.match(relative):
            data = await c.get_json(f"/repos/{match.group(1)}/pipelines/{match.group(2)}")
            return _format_pipeline(data)

        if match := _REPO_PATTERN.match(relative):
            data = await c.get_json(f"/repos/{match.group(1)}")
            return _format_repo(data)

        return (
            f"Unsupported Woodpecker URL: {url}\n\n"
            f"Currently supported: {base_url}/repos/<id> "
            f"and {base_url}/repos/<id>/pipeline/<id>."
        )


def _format_pipeline(pipeline: dict[str, Any]) -> str:
    lines: list[str] = [
        f"# Pipeline #{pipeline.get('number', '')}",
        "",
        f"**Status:** {pipeline.get('status', 'unknown')}",
        f"**Branch:** {pipeline.get('branch', '')}",
        f"**Event:** {pipeline.get('event', '')}",
        f"**Author:** {pipeline.get('author', '')}",
        f"**Commit:** {pipeline.get('commit', '')}",
        f"**Message:** {pipeline.get('message', '')}",
    ]
    if title := pipeline.get("title"):
        lines.append(f"**Title:** {title}")

    workflows = pipeline.get("workflows", [])
    if workflows:
        lines.append("")
        lines.append("## Workflows")
        lines.append("")
        lines.append("| Workflow | Status | Duration |")
        lines.append("|---|---|---|")
        for wf in workflows:
            started = wf.get("started", 0) or 0
            finished = wf.get("finished", 0) or 0
            duration = f"{finished - started}s" if finished > started else ""
            lines.append(f"| {wf.get('name', '')} | {wf.get('state', '')} | {duration} |")

    return "\n".join(lines)


def _format_repo(repo: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {repo.get('full_name', '')}",
            "",
            f"**Forge URL:** {repo.get('forge_url', '')}",
            f"**Default branch:** {repo.get('default_branch', '')}",
            f"**Visibility:** {repo.get('visibility', '')}",
            f"**Active:** {repo.get('active', False)}",
            f"**Timeout:** {repo.get('timeout', 0)}s",
        ]
    )
