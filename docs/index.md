# woodpecker-mcp

MCP server for [Woodpecker CI](https://woodpecker-ci.org). Stateless - each
request carries its own authentication token, so the server scales
horizontally without a database or shared secret.

The server exposes the Woodpecker API as MCP tools, so an AI assistant can
query repositories, pipelines, logs, cron jobs, secrets, agents,
organizations, users, and system info - and act on it.

## Featured workflows

The server isn't just a 1-to-1 mirror of the Woodpecker API - it ships
**AI-native tools** that aggregate and analyze for you:

- [**Diagnose pipeline failures**](guides/diagnose-failures.md) - ask *"Why did
  the last pipeline fail?"* and get the failing step, its logs, and the config
  that ran, all in one call (`explain_pipeline_failure`).
- [**Review CI config**](guides/review-ci-config.md) - ask *"Is the CI config
  sound before we release?"* and get deterministic lint findings on images,
  events, deprecated keys, and secret usage (`review_pipeline_config`).
- [**Monitor pipelines**](guides/monitor-pipelines.md) - everyday questions
  about the queue, recent runs, logs, and scheduling, answered by the 50 thin
  read/action tools.

## Features

- Query repositories, pipelines, logs, cron jobs, secrets, agents, organizations, users, and system info
- Trigger, restart, cancel, approve, and decline pipelines
- Manage cron jobs and repository secrets
- Diagnose pipeline failures with the AI-native `explain_pipeline_failure` tool
- Lint CI configs with the deterministic `review_pipeline_config` tool
- Per-request authentication (stateless, horizontally scalable)
- Read-only MCP resources (`woodpecker://`) for repositories, pipelines, and the current user

## Get started

Jump into [Setup](setup.md) to install and run the server, head to the
[Usage Guide](usage/index.md) for the full list of tools, or start with a
[Featured workflow](#featured-workflows) above.

!!! note
    The server never stores your Woodpecker token. Each request must carry its
    own `Authorization: Bearer <token>` header, scoped to the permissions of
    that token.