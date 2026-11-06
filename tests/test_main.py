from __future__ import annotations

import sys

import pytest
import uvicorn

from woodpecker_mcp.__main__ import main


def test_main_passes_cli_options_to_uvicorn(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, object] = {}
    app = object()

    monkeypatch.setattr("woodpecker_mcp.server.build_app", lambda: app)
    monkeypatch.setattr(
        uvicorn,
        "run",
        lambda application, **kwargs: captured.update(kwargs, app=application),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["woodpecker-mcp", "--host", "0.0.0.0", "--port", "9000", "--log-level", "warning"],
    )

    main()

    assert captured["app"] is app
    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 9000
    assert captured["log_level"] == "warning"
