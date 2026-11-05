from __future__ import annotations

import base64
import contextlib
import os
import re
from functools import wraps
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from ..client import get_woodpecker_client
from ..errors import WoodpeckerError

_ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

READ_ONLY = ToolAnnotations(read_only_hint=True)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False)
DESTRUCTIVE = ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=False)
IDEMPOTENT_WRITE = ToolAnnotations(
    read_only_hint=False, destructive_hint=False, idempotent_hint=True
)


def read_only_enabled() -> bool:
    """Return True when MCP_READ_ONLY is set to a truthy value."""
    return os.environ.get("MCP_READ_ONLY", "").strip().lower() in {"1", "true", "yes", "on"}


def tool(
    mcp: MCPServer,
    *,
    annotations: ToolAnnotations = READ_ONLY,
) -> Any:
    """Register a tool with annotations, honoring MCP_READ_ONLY.

    In read-only mode only tools marked read-only are registered, so an agent
    cannot trigger pipelines, modify secrets, or delete resources.
    """

    def decorator(fn: Any) -> Any:
        if read_only_enabled() and annotations.read_only_hint is not True:
            return fn
        return mcp.tool(annotations=annotations)(fn)

    return decorator


def client() -> Any:
    return get_woodpecker_client()


def safe(fn: Any) -> Any:
    """Convert WoodpeckerError into a clean MCP ToolError.

    Woodpecker API failures (401/403/404/5xx) otherwise bubble up as opaque
    'unexpected exception' tool errors whose real message never reaches the
    client. This wrapper re-raises them as ToolError so the model gets an
    actionable message instead.
    """

    @wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await fn(*args, **kwargs)
        except WoodpeckerError as e:
            raise ToolError(e.message) from e

    return wrapper


def decode_b64(text: str) -> str:
    with contextlib.suppress(Exception):
        return base64.b64decode(text).decode("utf-8", errors="replace")
    return text


def decode_log_entries(entries: list[dict]) -> list[str]:
    decoded: list[str] = []
    for entry in entries:
        if isinstance(entry, dict):
            raw = entry.get("data") or ""
            decoded.append(strip_ansi(decode_b64(raw)))
        else:
            decoded.append("")
    return decoded


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences (colors, cursor movement) from log text."""
    return _ANSI_RE.sub("", text)


def truncate_text(
    text: str,
    *,
    max_lines: int | None = None,
    max_chars: int | None = None,
    tail: bool = True,
) -> tuple[str, bool]:
    """Trim log text to a line and/or character budget.

    Args:
        text: The log text to truncate.
        max_lines: Maximum number of lines to keep, or None for no limit.
        max_chars: Maximum number of characters to keep, or None for no limit.
        tail: Keep the end of the log (usually where failures appear) when True.

    Returns:
        A tuple of (truncated_text, was_truncated).
    """
    truncated = False
    if max_lines is not None and max_lines >= 0:
        lines = text.splitlines()
        if len(lines) > max_lines:
            lines = lines[-max_lines:] if tail else lines[:max_lines]
            text = "\n".join(lines)
            truncated = True
    if max_chars is not None and max_chars >= 0 and len(text) > max_chars:
        text = text[-max_chars:] if tail else text[:max_chars]
        truncated = True
    return text, truncated
