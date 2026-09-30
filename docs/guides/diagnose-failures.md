# Diagnose pipeline failures

`explain_pipeline_failure` is the flagship AI-native tool. Instead of asking
the model to piece together a failure from raw API calls, it gathers everything
a diagnosis needs in **one** deterministic call and returns a structured
summary the model can reason about.

## What it does under the hood

Given a repository (and optionally a specific pipeline), it:

1. Fetches the pipeline object (`get_pipeline`) - status, event, branch,
   author, commit, changed files, workflow/step states.
2. Fetches the `.woodpecker` config files used by that run.
3. For every **failed or errored** step, fetches its log and **truncates it**
   (first 200 lines) so huge builds can't blow up the context.
4. If no `pipeline_number` is given, it finds the most recent failed pipeline
   in the repository automatically.

It only produces a full diagnosis for failed pipelines - if the pipeline is
green, it says so and stops.

## Walkthrough: "Why did the last pipeline fail?"

Ask your AI assistant:

> Why did the last pipeline fail in repo 1?

The assistant calls `explain_pipeline_failure(repo_id=1)` and receives
something like:

```json
{
  "pipeline": {
    "number": 42,
    "status": "failure",
    "event": "pull_request",
    "branch": "main",
    "message": "fix: broken build",
    "author": "dev",
    "duration_seconds": 110,
    "changed_files": ["src/main.py"]
  },
  "workflows": [
    {
      "name": "build",
      "state": "failure",
      "error": "exit code 1",
      "steps": [
        {"pid": 1, "name": "clone", "state": "success", "exit_code": 0},
        {
          "pid": 2,
          "name": "test",
          "state": "failure",
          "exit_code": 1,
          "logs": {"total_lines": 2, "truncated": false, "text": "Cloning...\nError: test failed with exit code 1"}
        }
      ]
    }
  ],
  "config": [
    {"name": ".woodpecker.yml", "data": "steps:\n  - name: build\n    image: python:3.12\n    ..."}
  ]
}
```

The assistant then summarizes: *"Pipeline #42 failed in the `test` step (exit
code 1) of the `build` workflow. The log shows an assertion error..."* - with
the exact failing step, log excerpt, and config in context.

## Reading the result

- **`pipeline`** - the headline facts: number, status, event, branch, commit,
  author, duration, and which files changed (useful to spot an obvious culprit
  in the diff).
- **`workflows` / `steps`** - the exact step that failed (`state`, `exit_code`,
  `error`), plus per-step duration. Steps that succeeded have **no** `logs`
  key, so the payload stays small.
- **`logs`** - only present for failed steps; `truncated` tells you whether
  more output exists beyond what's shown.
- **`config`** - the decoded `.woodpecker` files for that run, so the model can
  reason about *why* the step failed (wrong command, bad image, missing env).

## Tips

- **Be explicit for PRs**: for a pull-request pipeline, pass
  `pipeline_number` - otherwise the tool picks the latest *failed* run, which
  may be a different pipeline.
- **Combine with other tools**: after the diagnosis, `get_step_logs` or
  `download_step_logs` can fetch the *full* log of the failing step, and
  `get_pipeline_metadata` gives the previous pipeline for context (e.g. "this
  worked before commit X").
- **Rerun after fixing**: `rerun_last_failed` restarts the same failed
  pipeline to verify the fix.