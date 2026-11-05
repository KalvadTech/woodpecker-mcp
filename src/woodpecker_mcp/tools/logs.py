from __future__ import annotations

import re
from typing import Any

from mcp.server.mcpserver import MCPServer

from ._common import (
    READ_ONLY,
    client,
    decode_log_entries,
    safe,
    strip_ansi,
    tool,
    truncate_text,
)

_DEFAULT_MAX_LINES = 500
_DEFAULT_MAX_CHARS = 200_000
_ERROR_RE = re.compile(r"\berror\b", re.IGNORECASE)
_WARNING_RE = re.compile(r"\bwarning\b", re.IGNORECASE)


def register(mcp: MCPServer) -> None:
    @tool(mcp, annotations=READ_ONLY)
    @safe
    async def get_step_logs(
        repo_id: int,
        pipeline_number: int,
        step_id: int,
        max_lines: int | None = _DEFAULT_MAX_LINES,
        max_chars: int | None = _DEFAULT_MAX_CHARS,
        tail: bool = True,
    ) -> dict[str, Any]:
        """Get logs for a specific pipeline step.

        Fetches the decoded log output from a single step in a pipeline workflow.

        Args:
            repo_id: The internal Woodpecker repository ID.
            pipeline_number: The pipeline number (e.g. 42).
            step_id: The step's database ID (the `id` field returned by
                     list_pipeline_steps). Note that `pid` is only the step's
                     display/order index and is not accepted here.
            max_lines: Maximum lines to return. Defaults to 500; set to null for
                       no line limit.
            max_chars: Maximum characters to return. Defaults to 200000; set to
                       null for no character limit.
            tail: Keep the end of the log (where failures usually appear) when
                  truncating. Set to false to keep the beginning.

        Returns:
            Dict with 'total_lines', 'returned_lines', 'truncated', and 'text'.
            ANSI escape sequences are stripped from 'text'.

        Related tools:
            - list_pipeline_steps: Discover step IDs for a pipeline.
            - summarize_logs: Get logs with error/warning counts.
        """
        data = await client().get_json(f"/repos/{repo_id}/logs/{pipeline_number}/{step_id}")
        lines = data if isinstance(data, list) else []
        text = "\n".join(decode_log_entries(lines))
        text, truncated = truncate_text(text, max_lines=max_lines, max_chars=max_chars, tail=tail)
        return {
            "total_lines": len(lines),
            "returned_lines": len(text.splitlines()),
            "truncated": truncated,
            "text": text,
        }

    @tool(mcp, annotations=READ_ONLY)
    @safe
    async def download_step_logs(
        repo_id: int,
        pipeline_number: int,
        step_id: int,
        max_lines: int | None = _DEFAULT_MAX_LINES,
        max_chars: int | None = _DEFAULT_MAX_CHARS,
        tail: bool = True,
    ) -> dict[str, Any]:
        """Download the raw log output for a pipeline step.

        Fetches the plain-text log for a step, unlike get_step_logs which
        returns structured JSON log entries.

        Args:
            repo_id: The internal Woodpecker repository ID.
            pipeline_number: The pipeline number (e.g. 42).
            step_id: The step's database ID (the `id` field returned by
                     list_pipeline_steps). Note that `pid` is only the step's
                     display/order index and is not accepted here.
            max_lines: Maximum lines to return. Defaults to 500; set to null for
                       no line limit.
            max_chars: Maximum characters to return. Defaults to 200000; set to
                       null for no character limit.
            tail: Keep the end of the log (where failures usually appear) when
                  truncating. Set to false to keep the beginning.

        Returns:
            Dict with 'total_lines', 'returned_lines', 'truncated', and 'text'.
            ANSI escape sequences are stripped from 'text'.

        Related tools:
            - list_pipeline_steps: Discover step IDs for a pipeline.
            - get_step_logs: Get structured log entries instead.
            - summarize_logs: Get logs with error/warning counts.
        """
        raw = await client().get_text(f"/repos/{repo_id}/logs/{pipeline_number}/{step_id}/download")
        total_lines = len(raw.splitlines())
        text, truncated = truncate_text(
            strip_ansi(raw), max_lines=max_lines, max_chars=max_chars, tail=tail
        )
        return {
            "total_lines": total_lines,
            "returned_lines": len(text.splitlines()),
            "truncated": truncated,
            "text": text,
        }

    @tool(mcp, annotations=READ_ONLY)
    @safe
    async def list_pipeline_steps(
        repo_id: int,
        pipeline_number: int,
    ) -> dict[str, Any]:
        """List all workflows and steps for a pipeline with their status.

        Use this to discover step IDs (the `id` field) needed by get_step_logs or
        summarize_logs, and to see the overall pipeline structure.

        Args:
            repo_id: The internal Woodpecker repository ID.
            pipeline_number: The pipeline number (e.g. 42).

        Returns:
            Dict with 'steps' list (each having 'workflow', 'id', 'pid', 'name',
            'state', 'started', 'finished', 'exit_code') and 'workflows' list.
            Use the step 'id' (not 'pid') with get_step_logs or summarize_logs.

        Related tools:
            - get_step_logs: Fetch logs for a specific step using its id.
            - summarize_logs: Get logs with error/warning counts.
        """
        data = await client().get_json(f"/repos/{repo_id}/pipelines/{pipeline_number}")
        workflows = data.get("workflows", []) if isinstance(data, dict) else []
        steps = []
        for wf in workflows:
            wf_name = wf.get("name", "unknown")
            for child in wf.get("children", []):
                steps.append(
                    {
                        "workflow": wf_name,
                        "id": child.get("id"),
                        "pid": child.get("pid"),
                        "name": child.get("name", ""),
                        "state": child.get("state", ""),
                        "started": child.get("started"),
                        "finished": child.get("finished"),
                        "exit_code": child.get("exit_code"),
                    }
                )
        return {"steps": steps, "workflows": workflows}

    @tool(mcp, annotations=READ_ONLY)
    @safe
    async def summarize_logs(
        repo_id: int,
        pipeline_number: int,
        step_id: int,
        max_lines: int | None = _DEFAULT_MAX_LINES,
        max_chars: int | None = _DEFAULT_MAX_CHARS,
        tail: bool = True,
    ) -> dict[str, Any]:
        """Get logs for a pipeline step and return them as text with summary statistics.

        Fetches logs and counts error/warning lines for quick analysis. Counts
        cover the full log, even when 'text' is truncated.

        Args:
            repo_id: The internal Woodpecker repository ID.
            pipeline_number: The pipeline number (e.g. 42).
            step_id: The step's database ID (the `id` field returned by
                     list_pipeline_steps). Note that `pid` is only the step's
                     display/order index and is not accepted here.
            max_lines: Maximum lines to return. Defaults to 500; set to null for
                       no line limit.
            max_chars: Maximum characters to return. Defaults to 200000; set to
                       null for no character limit.
            tail: Keep the end of the log (where failures usually appear) when
                  truncating. Set to false to keep the beginning.

        Returns:
            Dict with 'total_lines', 'returned_lines', 'error_lines' (count of
            lines containing the word 'error'), 'warning_lines' (count of lines
            containing the word 'warning'), 'truncated', and 'text'.

        Related tools:
            - get_step_logs: Get raw logs without statistics.
            - list_pipeline_steps: Discover step IDs for a pipeline.
        """
        data = await client().get_json(f"/repos/{repo_id}/logs/{pipeline_number}/{step_id}")
        lines = data if isinstance(data, list) else []
        decoded = decode_log_entries(lines)
        error_count = sum(1 for line in decoded if _ERROR_RE.search(line))
        warning_count = sum(1 for line in decoded if _WARNING_RE.search(line))
        text, truncated = truncate_text(
            "\n".join(decoded), max_lines=max_lines, max_chars=max_chars, tail=tail
        )
        return {
            "total_lines": len(lines),
            "returned_lines": len(text.splitlines()),
            "error_lines": error_count,
            "warning_lines": warning_count,
            "truncated": truncated,
            "text": text,
        }
