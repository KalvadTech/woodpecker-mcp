# Contributing

Thank you for your interest in contributing!

See the full [contributing guidelines](https://github.com/KalvadTech/woodpecker-mcp/blob/main/CONTRIBUTING.md)
in the repository for details on development setup, code style, testing, and
the pull request process.

## Quick summary

- **Python 3.14+**, managed with `uv`.
- Follow PEP 8, use type hints (enforced by `ty`), line length 100.
- Tooling: `ruff format`, `ruff check`, `ty`, `pytest` with `pytest-asyncio`.
- Run all checks with `make check` before submitting a PR.

## Adding new tools

1. Create `src/woodpecker_mcp/tools/<name>.py` (or extend an existing module).
2. Implement `register(mcp: MCPServer)` with tool functions using `@mcp.tool()`.
3. Add tests in `tests/tools/test_<name>.py` using `respx` to mock HTTP.
4. Register the module in `src/woodpecker_mcp/tools/__init__.py`.
5. Update the "Available tools" table in this documentation and the README.

## Test hygiene

Never use real repository names, usernames, emails, commit hashes, or data
from a live instance in tests. Use neutral fakes such as `testuser/repo-one`
and `test@example.com`.