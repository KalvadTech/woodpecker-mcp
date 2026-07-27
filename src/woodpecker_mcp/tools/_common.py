from __future__ import annotations

import base64
import contextlib
from typing import Any

from ..client import get_woodpecker_client


def client() -> Any:
    return get_woodpecker_client()


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
