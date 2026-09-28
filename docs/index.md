# woodpecker-mcp

MCP server for [Woodpecker CI](https://woodpecker-ci.org). Stateless — each
request carries its own authentication token, so the server scales
horizontally without a database or shared secret.

The server exposes the Woodpecker API as MCP tools, so an AI assistant can
query repositories, pipelines, logs, cron jobs, secrets, agents,
organizations, users, and system info — and act on it.

## Features

- Query repositories, pipelines, logs, cron jobs, secrets, agents, organizations, users, and system info
- Trigger, restart, cancel, approve, and decline pipelines
- Manage cron jobs and repository secrets
- Diagnose pipeline failures with the AI-native `explain_pipeline_failure` tool
- Per-request authentication (stateless, horizontally scalable)
- Read-only MCP resources (`woodpecker://`) for repositories, pipelines, and the current user

## Get started

Jump into [Setup](setup.md) to install and run the server, or head straight to
the [Usage Guide](usage/index.md) for the full list of tools.

!!! note
    The server never stores your Woodpecker token. Each request must carry its
    own `Authorization: Bearer <token>` header, scoped to the permissions of
    that token.