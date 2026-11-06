# Deployment

## Docker

```sh
docker run --rm -p 8080:8080 \
  -e WOODPECKER_SERVER=https://ci.example.com \
  -e MCP_ALLOWED_HOSTS=ci-mcp.example.com \
  ghcr.io/kalvadtech/woodpecker-mcp:latest
```

The image is multi-stage Alpine, runs as a non-root user, and exposes port
8080. Set `MCP_ALLOWED_HOSTS` to the host you access the server from if it is
not `localhost` (use `*` only when you accept disabling DNS-rebinding
protection).

## TLS and reverse proxies

Terminate TLS at a reverse proxy and forward requests to the container. Preserve
the `Host` header and set `MCP_ALLOWED_HOSTS` to the public hostname. If a
non-browser client sends an `Origin` header, list it in `MCP_ALLOWED_ORIGINS`.

Browser-based MCP clients are not supported because the server does not emit
CORS headers. For autonomous agents, set `MCP_READ_ONLY=true` to register only
read-only tools.
