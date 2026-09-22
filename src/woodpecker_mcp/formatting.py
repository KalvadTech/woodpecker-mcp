from __future__ import annotations

from typing import Any


def format_pipeline(pipeline: dict[str, Any]) -> str:
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


def format_repo(repo: dict[str, Any]) -> str:
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
