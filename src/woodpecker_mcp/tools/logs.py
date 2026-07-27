from __future__ import annotations

import base64
import contextlib
from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_step_logs(
        repo_id: int,
        pipeline_number: int,
        step_id: int,
    ) -> dict[str, Any]:
        """Get logs for a specific pipeline step."""
        data = await client().get_json(f"/repos/{repo_id}/logs/{pipeline_number}/{step_id}")
        return {"logs": data if isinstance(data, list) else []}

    @mcp.tool()
    async def list_pipeline_steps(
        repo_id: int,
        pipeline_number: int,
    ) -> dict[str, Any]:
        """List all workflows and steps for a pipeline with their status."""
        data = await client().get_json(f"/repos/{repo_id}/pipelines/{pipeline_number}")
        workflows = data.get("workflows", []) if isinstance(data, dict) else []
        steps = []
        for wf in workflows:
            wf_name = wf.get("name", "unknown")
            for child in wf.get("children", []):
                steps.append(
                    {
                        "workflow": wf_name,
                        "pid": child.get("pid"),
                        "name": child.get("name", ""),
                        "state": child.get("state", ""),
                        "started": child.get("started"),
                        "finished": child.get("finished"),
                        "exit_code": child.get("exit_code"),
                    }
                )
        return {"steps": steps, "workflows": workflows}

    @mcp.tool()
    async def summarize_logs(
        repo_id: int,
        pipeline_number: int,
        step_id: int,
    ) -> dict[str, Any]:
        """Get logs for a pipeline step and return them as text with summary statistics."""
        data = await client().get_json(f"/repos/{repo_id}/logs/{pipeline_number}/{step_id}")
        lines = data if isinstance(data, list) else []
        decoded: list[str] = []
        for entry in lines:
            if isinstance(entry, dict):
                raw = entry.get("data") or ""
                with contextlib.suppress(Exception):
                    raw = base64.b64decode(raw).decode("utf-8", errors="replace")
                decoded.append(raw)
            else:
                decoded.append("")
        text = "\n".join(decoded)
        error_count = sum(1 for line in decoded if "error" in line.lower())
        warning_count = sum(1 for line in decoded if "warning" in line.lower())
        return {
            "total_lines": len(lines),
            "error_lines": error_count,
            "warning_lines": warning_count,
            "text": text,
        }
