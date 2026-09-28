# MCP Clients

## Claude Code

Add a `.mcp.json` file to your project root:

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

## opencode

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

Set `WOODPECKER_TOKEN` in your shell before starting opencode (same env var as
the Woodpecker CLI). If `{env:...}` interpolation doesn't work in your version,
use `{file:~/.config/opencode/.secrets/woodpecker-token}` instead, or hardcode
the token.

## Other MCP clients

Point your MCP client to the Streamable HTTP endpoint
(`http://localhost:8080/mcp`) and send your Woodpecker personal access token as
`Authorization: Bearer <token>` with each request.