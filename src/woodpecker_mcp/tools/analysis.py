from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from ..errors import WoodpeckerError
from ._common import client, decode_b64, decode_log_entries

_LOG_TRUNCATION_LIMIT = 200


def register(mcp: MCPServer) -> None:
    @mcp.tool()
    async def explain_pipeline_failure(
        repo_id: int,
        pipeline_number: int | None = None,
    ) -> dict[str, Any]:
        """Explain why a pipeline failed. Defaults to the most recent failure."""
        c = client()

        if pipeline_number is None:
            pipeline_number = await _find_latest_failure(c, repo_id)
            if pipeline_number is None:
                return {"message": "no failed pipelines found in this repository"}

        try:
            pipeline = await c.get_json(f"/repos/{repo_id}/pipelines/{pipeline_number}")
        except WoodpeckerError:
            return {
                "pipeline": {"number": pipeline_number},
                "message": f"Pipeline #{pipeline_number} not found.",
            }

        status = pipeline.get("status", "")
        if status not in ("failure", "error"):
            return {
                "pipeline": {"number": pipeline_number, "status": status},
                "message": f"Pipeline #{pipeline_number} is {status}, not a failure.",
            }

        try:
            config_data = await c.get_json(f"/repos/{repo_id}/pipelines/{pipeline_number}/config")
        except WoodpeckerError:
            config_data = []
        config_files = config_data if isinstance(config_data, list) else []

        workflows_raw = pipeline.get("workflows", [])
        workflows_out = await _process_workflows(c, repo_id, pipeline_number, workflows_raw)

        p_started = pipeline.get("started") or 0
        p_finished = pipeline.get("finished") or 0

        return {
            "pipeline": {
                "number": pipeline.get("number"),
                "status": pipeline.get("status"),
                "event": pipeline.get("event"),
                "branch": pipeline.get("branch"),
                "message": pipeline.get("message"),
                "author": pipeline.get("author"),
                "commit": pipeline.get("commit"),
                "created": pipeline.get("created"),
                "duration_seconds": (p_finished - p_started) if p_finished > p_started else None,
                "changed_files": pipeline.get("changed_files", []),
            },
            "workflows": workflows_out,
            "config": [
                {"name": f.get("name", ""), "data": decode_b64(f.get("data", ""))}
                for f in config_files
            ],
        }


async def _find_latest_failure(c: Any, repo_id: int) -> int | None:
    data = await c.paginate(f"/repos/{repo_id}/pipelines", page=1, per_page=50)
    for p in data.get("items", []):
        if p.get("status") in ("failure", "error"):
            return p.get("number")
    return None


async def _process_workflows(
    c: Any,
    repo_id: int,
    pipeline_number: int,
    workflows_raw: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    workflows_out: list[dict[str, Any]] = []

    for wf in workflows_raw:
        wf_name = wf.get("name", "unknown")
        wf_state = wf.get("state", "")
        wf_error = wf.get("error")

        children = wf.get("children", [])
        steps_out = await _process_steps(c, repo_id, pipeline_number, children)

        wf_entry: dict[str, Any] = {
            "name": wf_name,
            "state": wf_state,
            "steps": steps_out,
        }
        if wf_error:
            wf_entry["error"] = wf_error

        wf_started = wf.get("started") or 0
        wf_finished = wf.get("finished") or 0
        if wf_finished > wf_started:
            wf_entry["duration_seconds"] = wf_finished - wf_started

        workflows_out.append(wf_entry)

    return workflows_out


async def _process_steps(
    c: Any,
    repo_id: int,
    pipeline_number: int,
    children: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    steps_out: list[dict[str, Any]] = []

    for child in children:
        step_state = child.get("state", "")
        exit_code = child.get("exit_code")

        step_entry: dict[str, Any] = {
            "pid": child.get("pid"),
            "name": child.get("name", ""),
            "state": step_state,
            "exit_code": exit_code,
            "type": child.get("type"),
        }

        started = child.get("started") or 0
        finished = child.get("finished") or 0
        if finished > started:
            step_entry["duration_seconds"] = finished - started

        if step_state in ("failure", "error") or (exit_code is not None and exit_code != 0):
            step_id = child.get("id")
            if step_id:
                step_entry["logs"] = await _fetch_logs(c, repo_id, pipeline_number, step_id)

        steps_out.append(step_entry)

    return steps_out


async def _fetch_logs(
    c: Any,
    repo_id: int,
    pipeline_number: int,
    step_id: int,
) -> dict[str, Any]:
    data = await c.get_json(f"/repos/{repo_id}/logs/{pipeline_number}/{step_id}")
    lines = data if isinstance(data, list) else []
    decoded = decode_log_entries(lines)

    truncated = len(decoded) > _LOG_TRUNCATION_LIMIT
    if truncated:
        decoded = decoded[:_LOG_TRUNCATION_LIMIT]

    return {
        "total_lines": len(lines),
        "truncated": truncated,
        "text": "\n".join(decoded),
    }
