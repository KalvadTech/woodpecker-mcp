from woodpecker_mcp.tools._config_lint import lint_config


def _findings(content: str) -> list[dict]:
    return lint_config(".woodpecker.yml", content)["findings"]


def _rules(content: str) -> set[str]:
    return {f["rule"] for f in _findings(content)}


CLEAN_CONFIG = """
steps:
  - name: build
    image: node:24.19.0
    commands:
      - pnpm install
      - pnpm build
    when:
      event: push
"""


def test_clean_config_no_findings():
    assert _findings(CLEAN_CONFIG) == []


def test_yaml_parse_error():
    findings = _findings("steps:\n  - name: [broken")
    assert findings[0]["rule"] == "yaml-parse-error"
    assert findings[0]["severity"] == "error"


def test_non_mapping_root():
    findings = _findings("- just\n- a\n- list")
    assert findings[0]["rule"] == "yaml-parse-error"


def test_invalid_when_event_pipeline_level():
    findings = _findings("when:\n  event: pushh\nsteps:\n  - name: build\n    image: alpine")
    assert any(
        f["rule"] == "invalid-when-event" and f["location"] == "when.event" for f in findings
    )


def test_invalid_when_event_step_level_list():
    config = """
steps:
  - name: build
    image: alpine
    when:
      event: [push, pull-request]
"""
    assert "invalid-when-event" in _rules(config)


def test_when_without_event():
    config = """
steps:
  - name: deploy
    image: alpine
    when:
      branch: main
"""
    assert "when-without-event" in _rules(config)


def test_no_when_not_flagged():
    assert "when-without-event" not in _rules(CLEAN_CONFIG)


def test_unpinned_image_no_tag():
    config = "steps:\n  - name: build\n    image: alpine"
    assert "unpinned-image" in _rules(config)


def test_unpinned_image_latest_and_floating():
    for image in ("node:latest", "node:24", "debian:stable-slim"):
        config = f"steps:\n  - name: build\n    image: {image}"
        assert "unpinned-image" in _rules(config), image


def test_pinned_images_not_flagged():
    for image in ("node:24.19.0", "debian:12.9", "alpine@sha256:abc123"):
        config = f"steps:\n  - name: build\n    image: {image}"
        assert "unpinned-image" not in _rules(config), image


def test_deprecated_secrets_list():
    config = """
steps:
  - name: build
    image: alpine
    secrets: [DOCKER_TOKEN]
"""
    assert "deprecated-secrets-list" in _rules(config)


def test_deprecated_step_group():
    config = """
steps:
  - name: build
    image: alpine
    group: build
"""
    assert "deprecated-step-group" in _rules(config)


def test_deprecated_platform():
    config = """
platform: linux/amd64
steps:
  - name: build
    image: alpine
"""
    assert "deprecated-platform" in _rules(config)


def test_undeclared_secret_reference():
    config = """
steps:
  - name: build
    image: alpine
    commands:
      - echo $DOCKER_PASSWORD
"""
    assert "undeclared-secret-reference" in _rules(config)


def test_declared_secret_not_flagged():
    config = """
steps:
  - name: build
    image: alpine
    environment:
      DOCKER_PASSWORD:
        from_secret: docker_password
    commands:
      - echo $DOCKER_PASSWORD
"""
    assert "undeclared-secret-reference" not in _rules(config)


def test_builtin_env_var_not_flagged():
    config = """
steps:
  - name: build
    image: alpine
    commands:
      - echo $CI_COMMIT_BRANCH
"""
    assert "undeclared-secret-reference" not in _rules(config)


def test_unknown_step_key():
    config = """
steps:
  - name: build
    image: alpine
    priviledged: true
"""
    assert "unknown-step-key" in _rules(config)


def test_unknown_pipeline_key():
    config = """
stps:
  - name: build
    image: alpine
"""
    assert "unknown-pipeline-key" in _rules(config)
