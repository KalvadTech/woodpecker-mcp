# Deployment

## Docker

```sh
docker run --rm -p 8080:8080 \
  -e WOODPECKER_SERVER=https://ci.example.com \
  ghcr.io/kalvadtech/woodpecker-mcp:latest
```

The image is multi-stage Alpine, runs as a non-root user, and exposes port
8080. Set `MCP_ALLOWED_HOSTS` to the host you access the server from if it is
not `localhost`.