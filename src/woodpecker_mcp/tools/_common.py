from __future__ import annotations

import base64
import contextlib
from functools import wraps
from typing import Any

from mcp.server.mcpserver.exceptions import ToolError

from ..client import get_woodpecker_client
from ..errors import WoodpeckerError


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
            decoded.append(decode_b64(raw))
        else:
            decoded.append("")
    return decoded
