# Setup

## Prerequisites

- Python 3.14+
- [uv](https://github.com/astral-sh/uv) (package manager)
- A Woodpecker CI server with a personal access token for your user

## Installation

```bash
git clone https://github.com/KalvadTech/woodpecker-mcp.git
cd woodpecker-mcp
make install
```

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `WOODPECKER_SERVER` | Yes | - | Your Woodpecker server URL (e.g. `https://ci.example.com`) |
| `MCP_ALLOWED_HOSTS` | No | `localhost` | DNS-rebinding protection allowlist (`*` to disable) |

Authentication is handled per-request via the `Authorization: Bearer <token>`
HTTP header. The server is stateless - it stores nothing and does not keep the
token between requests.

## Quick start

```bash
# Set your Woodpecker server URL (same env var as the Woodpecker CLI)
export WOODPECKER_SERVER=https://ci.example.com

# Start the server
make run
```

The server listens on `http://127.0.0.1:8080`, exposing the MCP Streamable
HTTP endpoint at `http://127.0.0.1:8080/mcp`.

## Development

```bash
make install    # Install dependencies
make run        # Start the server (requires WOODPECKER_SERVER)
make test       # Run tests
make lint       # Lint with ruff
make format     # Format with ruff
make typecheck  # Type-check with ty
make check      # Run all checks (lint + format + typecheck + test)
make clean      # Remove virtual environment
```