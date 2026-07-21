from __future__ import annotations

from typing import Any


class WoodpeckerError(Exception):
    def __init__(
        self,
        status: int,
        message: str,
        errors: list[str] | None = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.errors = errors or []
        self.body = body

    def __str__(self) -> str:
        if self.errors:
            return f"Woodpecker {self.status}: {self.message} ({'; '.join(self.errors)})"
        return f"Woodpecker {self.status}: {self.message}"


class AuthHeaderError(Exception):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
