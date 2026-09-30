# Review CI config

`review_pipeline_config` lints the `.woodpecker` config files used by a
pipeline. Unlike asking a model to "look at the config", it runs
**deterministic, schema-aware checks** in code - so the same config always
produces the same findings, and it never hallucinates a "looks good" verdict.

## The rules

| Rule | Severity | What it catches | How to fix |
|---|---|---|---|
| `yaml-parse-error` | error | The config is not valid YAML | Fix the YAML syntax |
| `invalid-when-event` | error | `when.event` uses a value outside the valid set (push, pull_request, pull_request_closed, pull_request_metadata, tag, release, deployment, cron, manual) | Correct the event name (watch for typos like `pull-request`) |
| `when-without-event` | warn | A `when` block has no `event` filter, so the step runs on **all** events | Add an `event:` filter |
| `unpinned-image` | warn | A step `image` has no tag, uses `latest`, or a floating tag (`node:24`, `debian:stable`) | Pin a version tag (`node:24.19.0`) or a digest |
| `deprecated-secrets-list` | warn | Step uses the `secrets: [...]` list | Use `environment` with `from_secret` |
| `deprecated-step-group` | warn | Step uses `group:` | Use `depends_on` |
| `deprecated-platform` | warn | Uses `platform:` | Use `labels:` |
| `undeclared-secret-reference` | warn | A command references a `$TOKEN`/`$KEY`/`$SECRET`/`$PASSWORD`-shaped variable that isn't declared in the step's `secrets`/`environment` | Declare it, or remove the reference |
| `unknown-step-key` / `unknown-pipeline-key` | warn | A key that isn't part of the expected config surface | Remove or rename the key |

## Walkthrough: "Review the CI config before a release"

Ask your AI assistant:

> Review the CI config for pipeline 42 in repo 1 before we release - anything risky or deprecated?

The assistant calls `review_pipeline_config(repo_id=1, pipeline_number=42)`
and receives:

```json
{
  "config_files": [
    {
      "name": "deploy",
      "findings": [
        {
          "rule": "unpinned-image",
          "severity": "warn",
          "location": "steps.deploy.image",
          "message": "image 'registry.example.com/plugins/coolify' is not pinned; use a version tag (e.g. 'node:24.19.0') or a digest"
        }
      ]
    },
    {
      "name": "build",
      "findings": [
        {
          "rule": "unpinned-image",
          "severity": "warn",
          "location": "steps.build.image",
          "message": "image 'plugins/docker-buildx' is not pinned; use a version tag (e.g. 'node:24.19.0') or a digest"
        }
      ]
    }
  ],
  "summary": {"files": 2, "errors": 0, "warnings": 2}
}
```

The assistant summarizes: *"2 warnings across `build` and `deploy` - both CI
plugin images are unpinned, so builds/deploys could pick up different plugin
versions between runs. Want me to draft pinned versions?"*

## Why deterministic beats "just read it"

- **No hallucination** - a finding only exists if a rule actually matched.
  The tool never confidently says "everything looks good" when it isn't.
- **Citable** - findings have a `rule`, `severity`, and `location`, so the
  model can quote them and you can diff findings before/after a fix.
- **Consistent** - the same config yields the same findings on every model
  and every run.

## Tips

- **Works for any pipeline** - unlike `explain_pipeline_failure`, this tool
  doesn't care about the pipeline status; it reviews the config regardless.
- **Pair with `get_pipeline_config`** if you need the raw, undecoded YAML.
- **Pair with `explain_pipeline_failure`** when a pipeline *failed to parse*:
  `review_pipeline_config` will surface the `yaml-parse-error` or
  `invalid-when-event` that caused it.