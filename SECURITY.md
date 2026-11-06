# Security Policy

## Reporting a vulnerability

Please report security issues privately via
[GitHub Security Advisories](https://github.com/KalvadTech/woodpecker-mcp/security/advisories/new).
Do not open a public issue for a vulnerability.

Include reproduction steps, affected versions, and any relevant configuration.
We will acknowledge reports as soon as possible and coordinate a fix and
disclosure.

## Supported versions

Security fixes are applied to the latest release on `main`.

## Design

woodpecker-mcp is a stateless MCP server:

- Each request must carry the caller's own Woodpecker personal access token as
  `Authorization: Bearer <token>`.
- The token is held only in memory for the duration of that request.
- No database, shared secret, or token cache is used.
- The configured `WOODPECKER_SERVER` is the only upstream the server will call.

This limits impact if the MCP server itself is compromised, but it does not make
the caller's token safe: run the server over TLS and use a token with the
minimum permissions required.

## Threat model and recommendations

### Untrusted CI content

Pipeline logs, repository configuration, commit messages, branch names, and
other CI data are attacker-influenced in many workflows. Treat tool output as
untrusted input:

- Never follow instructions embedded in logs or configs.
- Prefer `MCP_READ_ONLY=true` for autonomous agents and shared deployments. Only
  read-only tools are registered in that mode.
- Require human confirmation for write and destructive tools. Tool annotations
  mark read-only, write, and destructive operations.
- Use a least-privilege Woodpecker token.

### Secrets

`create_repo_secret` accepts the plaintext secret value as a tool argument, so
that value enters the model's context and may be retained in chat history or
logs. Prefer creating sensitive secrets directly in Woodpecker or via your
normal secret-management process. When using the tool, scope the secret with
`events` and/or `images` where possible.

Secret values are not returned by list/get operations.

### Network exposure

- Do not expose the MCP endpoint directly to the public internet without TLS
  and authentication.
- Put the server behind a TLS-terminating reverse proxy.
- Set `MCP_ALLOWED_HOSTS` to the hostnames clients use. Setting it to `*`
  disables DNS-rebinding protection.
- If a client sends an `Origin` header, also set `MCP_ALLOWED_ORIGINS`.
  Browser-based clients are not supported because the server does not emit CORS
  headers.
- Restrict network access to trusted clients.

### Authentication

Missing or invalid credentials return `401 Unauthorized` with
`WWW-Authenticate: Bearer`. The `/up` liveness endpoint is intentionally
unauthenticated and exposes no data.

## Dependency and supply-chain hygiene

- Dependencies are pinned in `uv.lock`.
- CI runs `uv audit`, Ruff, `ty`, `opengrep`, and the test suite.
- Docker images are built from pinned tool versions where possible.
