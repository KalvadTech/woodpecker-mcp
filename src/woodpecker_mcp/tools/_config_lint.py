from __future__ import annotations

import re
from typing import Any

import yaml

VALID_EVENTS = {
    "push",
    "pull_request",
    "pull_request_closed",
    "pull_request_metadata",
    "tag",
    "release",
    "deployment",
    "cron",
    "manual",
}

STEP_KEYS = {
    "name",
    "image",
    "commands",
    "when",
    "environment",
    "secrets",
    "volumes",
    "network_mode",
    "group",
    "depends_on",
    "settings",
    "backend",
    "privileged",
    "detach",
    "pull",
    "directory",
    "failure",
    "success",
    "status",
    "platform",
    "labels",
    "runs_on",
}

PIPELINE_KEYS = {
    "when",
    "steps",
    "depends_on",
    "skip_clone",
    "labels",
    "platform",
    "environment",
    "secrets",
    "volumes",
    "network_mode",
    "clone",
    "runs_on",
    "concurrency",
    "branches",
}

_SECRET_REF_RE = re.compile(r"\$\{?([A-Z][A-Z0-9_]*)\}?")
_SECRET_ISH = re.compile(r"(TOKEN|KEY|SECRET|PASSWORD)")
_IMAGE_TAG_RE = re.compile(r"\d+(\.\d+)+")


def lint_config(name: str, content: str) -> dict[str, Any]:
    """Parse a Woodpecker config and run the deterministic lint rules.

    Args:
        name: The config file name (e.g. '.woodpecker.yml').
        content: The raw YAML content of the config file.

    Returns:
        Dict with 'name' and 'findings', each finding having 'rule',
        'severity' ('error' or 'warn'), 'location', and 'message'.
    """
    try:
        doc = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        return {
            "name": name,
            "findings": [
                {
                    "rule": "yaml-parse-error",
                    "severity": "error",
                    "location": "",
                    "message": f"invalid YAML: {exc}",
                }
            ],
        }
    if not isinstance(doc, dict):
        return {
            "name": name,
            "findings": [
                {
                    "rule": "yaml-parse-error",
                    "severity": "error",
                    "location": "",
                    "message": "config root must be a mapping",
                }
            ],
        }

    findings: list[dict[str, Any]] = []
    findings.extend(_rule_invalid_when_event(doc))
    findings.extend(_rule_when_without_event(doc))
    findings.extend(_rule_unpinned_image(doc))
    findings.extend(_rule_deprecated_secrets(doc))
    findings.extend(_rule_deprecated_group(doc))
    findings.extend(_rule_deprecated_platform(doc))
    findings.extend(_rule_undeclared_secret(doc))
    findings.extend(_rule_unknown_step_key(doc))
    findings.extend(_rule_unknown_pipeline_key(doc))
    return {"name": name, "findings": findings}


def _iter_steps(doc: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Yield (step_name, step_dict) for both map and list step definitions."""
    steps = doc.get("steps")
    result: list[tuple[str, dict[str, Any]]] = []
    if isinstance(steps, dict):
        for name, step in steps.items():
            if isinstance(step, dict):
                result.append((str(name), step))
    elif isinstance(steps, list):
        for step in steps:
            if isinstance(step, dict):
                result.append((str(step.get("name", "")), step))
    return result


def _when_items(when: Any) -> list[dict[str, Any]]:
    """Normalize a `when` value (dict or list of dicts) into dicts."""
    if isinstance(when, dict):
        return [when]
    if isinstance(when, list):
        return [w for w in when if isinstance(w, dict)]
    return []


def _rule_invalid_when_event(doc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for when in _when_items(doc.get("when")):
        findings.extend(_invalid_events_in_when(when, "when"))
    for name, step in _iter_steps(doc):
        for when in _when_items(step.get("when")):
            findings.extend(_invalid_events_in_when(when, f"steps.{name}.when"))
    return findings


def _invalid_events_in_when(when: dict[str, Any], location: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    event = when.get("event")
    if event is None:
        return findings
    values = event if isinstance(event, list) else [event]
    for value in values:
        if isinstance(value, str) and value not in VALID_EVENTS:
            findings.append(
                {
                    "rule": "invalid-when-event",
                    "severity": "error",
                    "location": f"{location}.event",
                    "message": f"'{value}' is not a valid Woodpecker event",
                }
            )
    return findings


def _rule_when_without_event(doc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if doc.get("when") is not None:
        for when in _when_items(doc.get("when")):
            if "event" not in when:
                findings.append(
                    {
                        "rule": "when-without-event",
                        "severity": "warn",
                        "location": "when",
                        "message": "when block has no 'event' filter; runs on all events",
                    }
                )
    for name, step in _iter_steps(doc):
        if step.get("when") is not None:
            for when in _when_items(step.get("when")):
                if "event" not in when:
                    findings.append(
                        {
                            "rule": "when-without-event",
                            "severity": "warn",
                            "location": f"steps.{name}.when",
                            "message": "when block has no 'event' filter; runs on all events",
                        }
                    )
    return findings


def _is_pinned_image(image: Any) -> bool:
    if not isinstance(image, str):
        return True
    if "@sha256:" in image:
        return True
    last = image.rsplit("/", 1)[-1]
    if ":" not in last:
        return False
    tag = last.rsplit(":", 1)[1]
    if tag == "latest":
        return False
    return bool(_IMAGE_TAG_RE.fullmatch(tag))


def _rule_unpinned_image(doc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for name, step in _iter_steps(doc):
        image = step.get("image")
        if image is not None and not _is_pinned_image(image):
            findings.append(
                {
                    "rule": "unpinned-image",
                    "severity": "warn",
                    "location": f"steps.{name}.image",
                    "message": (
                        f"image {image!r} is not pinned; use a version tag "
                        "(e.g. 'node:24.19.0') or a digest"
                    ),
                }
            )
    return findings


def _is_secret_list(secrets: Any) -> bool:
    return isinstance(secrets, list)


def _rule_deprecated_secrets(doc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if _is_secret_list(doc.get("secrets")):
        findings.append(
            {
                "rule": "deprecated-secrets-list",
                "severity": "warn",
                "location": "secrets",
                "message": "'secrets' list is deprecated; use environment.from_secret",
            }
        )
    for name, step in _iter_steps(doc):
        if _is_secret_list(step.get("secrets")):
            findings.append(
                {
                    "rule": "deprecated-secrets-list",
                    "severity": "warn",
                    "location": f"steps.{name}.secrets",
                    "message": "'secrets' list is deprecated; use environment.from_secret",
                }
            )
    return findings


def _rule_deprecated_group(doc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for name, step in _iter_steps(doc):
        if "group" in step:
            findings.append(
                {
                    "rule": "deprecated-step-group",
                    "severity": "warn",
                    "location": f"steps.{name}.group",
                    "message": "'group' was removed; use 'depends_on' instead",
                }
            )
    return findings


def _rule_deprecated_platform(doc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if "platform" in doc:
        findings.append(
            {
                "rule": "deprecated-platform",
                "severity": "warn",
                "location": "platform",
                "message": "'platform' is deprecated; use 'labels' instead",
            }
        )
    for name, step in _iter_steps(doc):
        if "platform" in step:
            findings.append(
                {
                    "rule": "deprecated-platform",
                    "severity": "warn",
                    "location": f"steps.{name}.platform",
                    "message": "'platform' is deprecated; use 'labels' instead",
                }
            )
    return findings


def _declared_names(step: dict[str, Any]) -> set[str]:
    declared: set[str] = set()
    for secret in step.get("secrets") or []:
        if isinstance(secret, str):
            declared.add(secret.upper())
    environment = step.get("environment")
    if isinstance(environment, dict):
        declared.update(k.upper() for k in environment)
    return declared


def _rule_undeclared_secret(doc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for name, step in _iter_steps(doc):
        commands = step.get("commands")
        if not isinstance(commands, list):
            continue
        declared = _declared_names(step)
        for line in commands:
            if not isinstance(line, str):
                continue
            for match in _SECRET_REF_RE.finditer(line):
                var = match.group(1)
                if var.upper().startswith(("CI_", "WOODPECKER_")):
                    continue
                if _SECRET_ISH.search(var) and var.upper() not in declared:
                    findings.append(
                        {
                            "rule": "undeclared-secret-reference",
                            "severity": "warn",
                            "location": f"steps.{name}.commands",
                            "message": (
                                f"${var} looks like a secret but is not declared in "
                                "the step's secrets/environment"
                            ),
                        }
                    )
    return findings


def _rule_unknown_step_key(doc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for name, step in _iter_steps(doc):
        for key in step:
            if key not in STEP_KEYS:
                findings.append(
                    {
                        "rule": "unknown-step-key",
                        "severity": "warn",
                        "location": f"steps.{name}.{key}",
                        "message": f"unknown step key {key!r}",
                    }
                )
    return findings


def _rule_unknown_pipeline_key(doc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for key in doc:
        if key not in PIPELINE_KEYS:
            findings.append(
                {
                    "rule": "unknown-pipeline-key",
                    "severity": "warn",
                    "location": key,
                    "message": f"unknown pipeline key {key!r}",
                }
            )
    return findings
