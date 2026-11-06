# Deployment

## Docker

```sh
docker run --rm -p 8080:8080 \
  -e WOODPECKER_SERVER=https://ci.example.com \
  -e MCP_ALLOWED_HOSTS=ci-mcp.example.com \
  ghcr.io/kalvadtech/woodpecker-mcp:latest
```

The image is multi-stage Alpine, runs as a non-root user, binds to
`0.0.0.0:8080` inside the container, and includes a `/up` healthcheck. Set
`MCP_ALLOWED_HOSTS` to the host you access the server from if it is not
`localhost` (use `*` only when you accept disabling DNS-rebinding protection).
