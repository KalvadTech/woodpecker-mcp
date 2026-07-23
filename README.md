# woodpecker-mcp

[![ci](https://github.com/KalvadTech/woodpecker-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/KalvadTech/woodpecker-mcp/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://www.python.org/downloads/)

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

### Claude Code

`.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "woodpecker": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp",
      "headers": {
        "Authorization": "Bearer {env:WOODPECKER_TOKEN}"
      }
    }
  }
}
```

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
| **Pipelines** | `list_pipelines`, `get_pipeline`, `trigger_pipeline`, `restart_pipeline`, `cancel_pipeline`, `approve_pipeline`, `get_pipeline_config` |
| **Logs** | `get_step_logs`, `list_pipeline_steps` |
| **Cron** | `list_cron_jobs`, `create_cron_job`, `delete_cron_job`, `trigger_cron_job` |
| **Secrets** | `list_repo_secrets`, `create_repo_secret`, `delete_repo_secret` |
| **Agents** | `list_agents`, `get_agent`, `list_agent_tasks` |
| **Organizations** | `list_organizations`, `get_organization`, `get_org_permissions` |
| **Users** | `list_users`, `get_current_user`, `get_user_feed` |
| **System** | `get_health`, `get_version`, `get_queue_info` |
| **Forges** | `list_forges` |

**Total: 36 tools**

## Deployment

```sh
docker run --rm -p 8080:8080 \
  -e WOODPECKER_SERVER=https://ci.example.com \
  ghcr.io/kalvadtech/woodpecker-mcp:latest
```

The image is multi-stage Alpine, runs as a non-root user, and exposes 8080.

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

## Contributing

Pull requests are welcome. Please:

- follow [Conventional Commits](https://www.conventionalcommits.org/),
- keep changes terse and well-scoped (one logical change per commit),
- add or update tests for any behaviour change,
- run `pytest`, `ruff`, and `ty` clean before opening the PR.

## License

[MIT](LICENSE) (c) 2026 Kalvad.
