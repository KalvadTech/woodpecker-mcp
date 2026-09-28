# Usage Guide

Once the server is running, point an MCP client at the Streamable HTTP
endpoint and send your Woodpecker personal access token as
`Authorization: Bearer <token>` with each request.

## Available tools

| Category | Tools |
|---|---|
| **Repositories** | `search_repositories`, `get_repository`, `get_repository_by_name`, `list_branches`, `list_pull_requests`, `repair_repository`, `activate_repository`, `deactivate_repository`, `get_repo_permissions` |
| **Pipelines** | `list_pipelines`, `get_pipeline`, `trigger_pipeline`, `restart_pipeline`, `cancel_pipeline`, `approve_pipeline`, `get_pipeline_config`, `get_pipeline_metadata`, `rerun_last_failed` |
| **Analysis** | `explain_pipeline_failure` |
| **Logs** | `get_step_logs`, `list_pipeline_steps`, `summarize_logs`, `download_step_logs` |
| **Cron** | `list_cron_jobs`, `get_cron_job`, `create_cron_job`, `delete_cron_job`, `trigger_cron_job` |
| **Secrets** | `list_repo_secrets`, `get_repo_secret`, `create_repo_secret`, `delete_repo_secret` |
| **Agents** | `list_agents`, `get_agent`, `list_agent_tasks` |
| **Organizations** | `list_organizations`, `get_organization`, `get_org_permissions` |
| **Users** | `list_users`, `get_current_user`, `get_user_feed`, `get_user_repos` |
| **System** | `get_health`, `get_version`, `get_queue_info`, `list_queued_pipelines`, `get_signature_public_key` |
| **Forges** | `list_forges` |
| **URLs** | `open_woodpecker_url` |

**Total: 49 tools**

## Examples

Questions you can ask your AI assistant when this MCP server is connected:

| Question | Tools used |
|---|---|
| "Why did the last pipeline fail?" | `explain_pipeline_failure` |
| "Is a deployment running right now?" | `get_queue_info` |
| "What pipelines ran in the last hour?" | `get_user_feed` |
| "Show me the logs for pipeline #42 in repo X" | `summarize_logs` |
| "Restart the last failed pipeline in repo Y" | `rerun_last_failed` |
| "Create a nightly cron job on main" | `create_cron_job` |
| "List all agents and their tasks" | `list_agents`, `list_agent_tasks` |