# woodpecker-mcp

MCP server for [Woodpecker CI](https://woodpecker-ci.org). Stateless — each request carries its own authentication token.

## Features

- Query repositories, pipelines, logs, cron jobs, secrets, agents, organizations, users, and system info
- Trigger, restart, cancel, approve, and decline pipelines
- Manage cron jobs and repository secrets
- Per-request authentication (stateless, horizontally scalable)

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `WOODPECKER_SERVER` | Yes | — | Your Woodpecker server URL (e.g. `https://ci.example.com`) |
| `WOODPECKER_API_PREFIX` | No | `/api` | API path prefix under `WOODPECKER_URL` |
| `MCP_ALLOWED_HOSTS` | No | `localhost` | DNS-rebinding protection allowlist (`*` to disable) |

Authentication is handled per-request via the `Authorization: Bearer <token>` HTTP header.

## Quick Start

```bash
# Install dependencies
make install

# Set your Woodpecker server URL (same env var as the Woodpecker CLI)
export WOODPECKER_SERVER=https://ci.example.com

# Start the server
make run
```

The server listens on `http://127.0.0.1:8080`.

## Connecting MCP clients

### opencode

Add a remote MCP server to your `opencode.json`:

```json
{
  "mcp": {
    "woodpecker": {
      "type": "remote",
      "url": "http://localhost:8080/mcp",
      "enabled": true,
      "oauth": false,
      "headers": {
        "Authorization": "Bearer {env:WOODPECKER_TOKEN}"
      }
    }
  }
}
```

Set `WOODPECKER_TOKEN` in your shell before starting opencode (same env var as the Woodpecker CLI). If `{env:...}` interpolation doesn't work in your version, use `{file:~/.config/opencode/.secrets/woodpecker-token}` instead, or hardcode the token.

### Other MCP clients

Point your MCP client to the Streamable HTTP endpoint (`http://localhost:8080/mcp`) and send your Woodpecker personal access token as `Authorization: Bearer <token>` with each request.

## Available tools

| Category | Tools |
|---|---|
| **Repositories** | `search_repositories`, `get_repository`, `list_branches`, `list_pull_requests`, `repair_repository` |

*More tool categories coming soon: pipelines, logs, cron, secrets, agents, organizations, users, system, forges.*

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

## License

MIT
