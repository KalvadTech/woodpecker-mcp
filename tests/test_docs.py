from __future__ import annotations

from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_DOCS = [_ROOT / "README.md", _ROOT / "docs" / "usage" / "index.md"]


@pytest.mark.asyncio
async def test_documented_tools_match_registry(mcp):
    names = {tool.name for tool in await mcp.list_tools()}

    for path in _DOCS:
        text = path.read_text()
        missing = sorted(name for name in names if f"`{name}`" not in text)
        assert not missing, f"{path.relative_to(_ROOT)} is missing tools: {missing}"
        assert f"**Total: {len(names)} tools**" in text, (
            f"{path.relative_to(_ROOT)} does not document the current tool count ({len(names)})"
        )
