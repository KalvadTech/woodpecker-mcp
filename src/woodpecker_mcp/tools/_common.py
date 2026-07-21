from __future__ import annotations

from typing import Any

from ..client import get_woodpecker_client


def client() -> Any:
    return get_woodpecker_client()
