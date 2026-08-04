# Contributing to woodpecker-mcp

Thank you for your interest in contributing!

## How Can I Contribute?

### Reporting Bugs
- Use GitHub Issues
- Include: steps to reproduce, expected vs actual behavior, environment details

### Suggesting Features
- Use GitHub Issues with "enhancement" label
- Describe the use case and proposed solution

### Pull Requests
1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Run checks: `make check`
6. Submit PR

## Development Setup

### Prerequisites
- Python 3.14+
- uv (package manager)
- Woodpecker CI server (for testing)

### Getting Started
```bash
git clone https://github.com/KalvadTech/woodpecker-mcp.git
cd woodpecker-mcp
make install
export WOODPECKER_SERVER=https://your-ci.example.com
make run
```

## Code Style

### Python Conventions
- Follow PEP 8
- Use type hints (enforced by `ty`)
- Line length: 100 characters
- Use `from __future__ import annotations`

### Tooling
- **Formatter**: ruff format
- **Linter**: ruff check
- **Type checker**: ty
- **Test framework**: pytest with pytest-asyncio

### Running Checks
```bash
make check  # Runs lint + format + typecheck + test
```

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/).

**Format:**
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(tools): add explain_pipeline_failure tool
fix(client): handle empty response in paginate
docs: update README with new tool
test(analysis): add test for log truncation
```

## Testing

### Requirements
- All new features must have tests
- Maintain or improve test coverage
- Use `respx` for mocking HTTP requests
- Follow existing test patterns in `tests/tools/`

### Running Tests
```bash
make test           # Run all tests
pytest tests/tools/test_analysis.py  # Run specific test file
```

### Test Structure
```
tests/
├── conftest.py          # Shared fixtures
├── test_client.py       # Client unit tests
└── tools/               # Tool integration tests
    ├── test_analysis.py
    ├── test_pipelines.py
    └── ...
```

## Adding New Tools

1. Create `src/woodpecker_mcp/tools/<name>.py`
2. Implement `register(mcp: MCPServer)` function
3. Add tool functions with `@mcp.tool()` decorator
4. Add tests in `tests/tools/test_<name>.py`
5. Register in `src/woodpecker_mcp/tools/__init__.py`

### Tool Template
```python
from __future__ import annotations
from typing import Any
from mcp.server.mcpserver import MCPServer
from ._common import client

def register(mcp: MCPServer) -> None:
    @mcp.tool()
    async def my_tool(param: int) -> dict[str, Any]:
        """Brief description of what the tool does."""
        return await client().get_json(f"/endpoint/{param}")
```

## Review Process

1. At least one maintainer must approve
2. All CI checks must pass
3. Address review comments
4. Maintainer will merge

## Questions?

Open an issue or reach out to the maintainers.
