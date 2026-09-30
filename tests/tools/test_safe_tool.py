from woodpecker_mcp.errors import WoodpeckerError
from woodpecker_mcp.tools._common import safe


async def _ok(value):
    return value


async def _boom(message):
    raise WoodpeckerError(404, message)


async def _other():
    raise RuntimeError("boom")


def _wrapped(fn):
    return safe(fn)


async def test_safe_passes_through_success():
    assert await _wrapped(_ok)("value") == "value"


async def test_safe_converts_woodpecker_error_to_tool_error():
    wrapped = _wrapped(_boom)
    try:
        await wrapped("not found")
    except Exception as exc:
        from mcp.server.mcpserver.exceptions import ToolError

        assert isinstance(exc, ToolError)
        assert "not found" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ToolError")


async def test_safe_propagates_non_woodpecker_errors():
    wrapped = _wrapped(_other)
    try:
        await wrapped()
    except Exception as exc:
        assert isinstance(exc, RuntimeError)
    else:  # pragma: no cover
        raise AssertionError("expected RuntimeError")
