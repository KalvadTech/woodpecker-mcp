# Troubleshooting

## "invalid Woodpecker API token or unauthorized" (401)

The `Authorization` header is missing, malformed, or the token was rejected.
Make sure you send `Authorization: Bearer <token>` with **every** request and
that the token is valid for the configured `WOODPECKER_SERVER`.

## "forbidden" (403)

The token is valid but does not have the required permission for the endpoint.
Admin-gated tools (e.g. listing all users) need a token with admin rights.

## "not found" (404)

A repository, pipeline, or resource does not exist or is not visible to the
token in use. Double-check the `repo_id` / `pipeline_number` (use
`search_repositories` to find the internal Woodpecker repo id).

## DNS-rebinding / connection refused

By default `MCP_ALLOWED_HOSTS` only allows `localhost`. When accessing the
server from another host, set `MCP_ALLOWED_HOSTS` to that host (or `*` to
disable the protection).

## Pasted Woodpecker links don't resolve

Resource support varies by client. Use the `open_woodpecker_url` tool for
pasted links - it works in every client.