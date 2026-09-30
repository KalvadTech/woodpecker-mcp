# Monitor pipelines

Beyond the two AI-powered tools, the server exposes the full Woodpecker API as
thin, reliable tools for everyday CI monitoring. Here are the questions your
AI assistant can answer, and the tools it uses.

## "Is CI healthy right now?"

The assistant checks the queue and server state:

| Question | Tools used |
|---|---|
| "Is CI healthy?" | `get_health`, `get_version` |
| "Is anything running right now?" | `get_queue_info` |
| "What pipelines are queued across all repos?" | `list_queued_pipelines` |
| "Which agents are available?" | `list_agents`, `get_agent`, `list_agent_tasks` |

Example:

> What's queued across all repos right now?

`list_queued_pipelines` returns the global pipeline queue - every run waiting
or executing, with repo, branch, status, and author - so the model can tell you
whether a deploy is stuck behind a long build.

## "What happened recently?"

| Question | Tools used |
|---|---|
| "What pipelines ran in the last hour?" | `get_user_feed` |
| "What did my repos build recently?" | `get_user_repos` |
| "List pipelines for repo X" | `list_pipelines` |
| "Show me pipeline #42 in repo X" | `get_pipeline`, `get_pipeline_metadata` |

## "Show me the logs"

| Question | Tools used |
|---|---|
| "Show me the logs for pipeline #42 in repo X" | `summarize_logs`, `get_step_logs` |
| "What steps ran in pipeline #42?" | `list_pipeline_steps` |
| "Give me the raw log for a step" | `download_step_logs` |
| "What config did pipeline #42 use?" | `get_pipeline_config`, `review_pipeline_config` |

`summarize_logs` returns logs plus error/warning counts - a fast way to scan a
step without dumping everything into context. `list_pipeline_steps` reveals the
step ids (`pid`s) needed by the log tools.

## "Restart or rerun"

| Question | Tools used |
|---|---|
| "Restart the last failed pipeline in repo Y" | `rerun_last_failed` |
| "Restart pipeline #42" | `restart_pipeline` |
| "Cancel the running pipeline" | `cancel_pipeline` |
| "Approve the blocked pipeline" | `approve_pipeline` |

## "Schedule or manage"

| Question | Tools used |
|---|---|
| "Create a nightly cron job on main" | `create_cron_job`, `trigger_cron_job` |
| "List / show cron jobs" | `list_cron_jobs`, `get_cron_job` |
| "List / add a repo secret" | `list_repo_secrets`, `get_repo_secret`, `create_repo_secret` |

## Finding a repo id

Most tools take the **internal Woodpecker repo id** (not the GitHub id). Find
it with `search_repositories` or `get_repository_by_name`:

> Use `get_repository_by_name(repo_full_name="owner/repo")` to get the internal
> `id`, then pass that to the pipeline tools.