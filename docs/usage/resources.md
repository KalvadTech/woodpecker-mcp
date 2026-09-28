# Resources

The server also exposes read-only MCP resources that clients can attach or
read directly:

| URI | Description |
|---|---|
| `woodpecker://repo/{repo_id}` | Repository details as Markdown |
| `woodpecker://pipeline/{repo_id}/{pipeline_number}` | Pipeline details as Markdown |
| `woodpecker://self` | Currently authenticated user |

These complement (but do not replace) the `open_woodpecker_url` tool: resource
support varies by client, while the tool works everywhere. For pasted
Woodpecker links, prefer `open_woodpecker_url`.