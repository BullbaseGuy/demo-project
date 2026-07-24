from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_KEYS = {
    "schema_version",
    "project",
    "branches",
    "features",
    "paths",
    "recovery",
    "workflows",
}
FORBIDDEN_EXECUTABLES = {
    "bash",
    "sh",
    "zsh",
    "fish",
    "pwsh",
    "powershell",
    "cmd",
    "cmd.exe",
}
BRANCH_PREFIX_RE = re.compile(r"^[A-Za-z0-9._/-]+$")


class ConfigError(ValueError):
    pass


def _object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{field} must be an object")
    return value


def _non_empty(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field} must be a non-empty string")
    return value.strip()


def _string_list(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ConfigError(f"{field} must be a non-empty string array")
    return tuple(_non_empty(item, field) for item in value)


@dataclass(frozen=True)
class ProjectConfig:
    default_branch: str
    allowed_actors: tuple[str, ...]
    notification_mentions: tuple[str, ...]
    python_version: str
    work_prefix: str
    task_data_prefix: str
    publish_prefix: str
    automatic_merge: bool
    agent_execution: str
    relay_paid_probe: bool
    branch_gc_execute: bool
    docs_only: tuple[str, ...]
    framework: tuple[str, ...]
    protected: tuple[str, ...]
    infrastructure_retry_limit: int
    same_root_cause_limit: int
    workflows: dict[str, str]


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot load JSON object: {path}") from exc
    if not isinstance(value, dict):
        raise ConfigError(f"JSON root must be an object: {path}")
    return value


def load_project_config(root: Path = Path(".")) -> ProjectConfig:
    path = root / ".devflow/project.json"
    data = load_json_object(path)
    unknown = sorted(set(data) - PROJECT_KEYS)
    if unknown:
        raise ConfigError(f"unknown project configuration field(s): {', '.join(unknown)}")
    if data.get("schema_version") != 1:
        raise ConfigError("project schema_version must equal 1")

    project = _object(data.get("project"), "project")
    branches = _object(data.get("branches"), "branches")
    features = _object(data.get("features"), "features")
    paths = _object(data.get("paths"), "paths")
    recovery = _object(data.get("recovery"), "recovery")
    workflows_raw = _object(data.get("workflows"), "workflows")

    prefixes = {
        key: _non_empty(branches.get(key), f"branches.{key}")
        for key in ("work_prefix", "task_data_prefix", "publish_prefix")
    }
    for field, prefix in prefixes.items():
        if not BRANCH_PREFIX_RE.fullmatch(prefix) or not prefix.endswith(("/", "-")):
            raise ConfigError(
                f"branches.{field} must be a safe prefix ending in / or -"
            )

    automatic_merge = features.get("automatic_merge")
    relay_paid_probe = features.get("relay_paid_probe")
    branch_gc_execute = features.get("branch_gc_execute")
    if not all(
        isinstance(item, bool)
        for item in (automatic_merge, relay_paid_probe, branch_gc_execute)
    ):
        raise ConfigError("feature switches must be boolean")
    agent_execution = _non_empty(
        features.get("agent_execution"), "features.agent_execution"
    )
    if agent_execution not in {"disabled", "enabled"}:
        raise ConfigError("features.agent_execution must be disabled or enabled")

    infra_limit = recovery.get("infrastructure_retry_limit")
    same_root_limit = recovery.get("same_root_cause_limit")
    if (
        not isinstance(infra_limit, int)
        or isinstance(infra_limit, bool)
        or infra_limit < 0
    ):
        raise ConfigError(
            "recovery.infrastructure_retry_limit must be a non-negative integer"
        )
    if (
        not isinstance(same_root_limit, int)
        or isinstance(same_root_limit, bool)
        or same_root_limit < 1
    ):
        raise ConfigError(
            "recovery.same_root_cause_limit must be a positive integer"
        )

    workflows = {
        key: _non_empty(value, f"workflows.{key}")
        for key, value in workflows_raw.items()
    }
    required_workflows = {
        "state_consistency",
        "product_gate",
        "post_merge",
        "secret_audit",
        "relay_health",
        "agent_task",
    }
    missing = sorted(required_workflows - set(workflows))
    if missing:
        raise ConfigError(f"missing workflow name(s): {', '.join(missing)}")

    return ProjectConfig(
        default_branch=_non_empty(
            project.get("default_branch"), "project.default_branch"
        ),
        allowed_actors=_string_list(
            project.get("allowed_actors"), "project.allowed_actors"
        ),
        notification_mentions=_string_list(
            project.get("notification_mentions"),
            "project.notification_mentions",
        ),
        python_version=_non_empty(
            project.get("python_version"), "project.python_version"
        ),
        work_prefix=prefixes["work_prefix"],
        task_data_prefix=prefixes["task_data_prefix"],
        publish_prefix=prefixes["publish_prefix"],
        automatic_merge=automatic_merge,
        agent_execution=agent_execution,
        relay_paid_probe=relay_paid_probe,
        branch_gc_execute=branch_gc_execute,
        docs_only=_string_list(paths.get("docs_only"), "paths.docs_only"),
        framework=_string_list(paths.get("framework"), "paths.framework"),
        protected=_string_list(paths.get("protected"), "paths.protected"),
        infrastructure_retry_limit=infra_limit,
        same_root_cause_limit=same_root_limit,
        workflows=workflows,
    )


def load_gate_profiles(
    root: Path = Path("."),
) -> dict[str, tuple[tuple[str, ...], ...]]:
    path = root / ".devflow/gate-profiles.json"
    data = load_json_object(path)
    if set(data) != {"schema_version", "profiles"}:
        raise ConfigError(
            "gate profile file accepts only schema_version and profiles"
        )
    if data.get("schema_version") != 1:
        raise ConfigError("gate profile schema_version must equal 1")
    raw_profiles = _object(data.get("profiles"), "profiles")
    if not raw_profiles:
        raise ConfigError("profiles must not be empty")

    profiles: dict[str, tuple[tuple[str, ...], ...]] = {}
    for name, raw_commands in raw_profiles.items():
        profile_name = _non_empty(name, "profile name")
        if not isinstance(raw_commands, list) or not raw_commands:
            raise ConfigError(f"profile {profile_name} must contain commands")
        commands = []
        for index, raw_command in enumerate(raw_commands):
            if not isinstance(raw_command, list) or not raw_command:
                raise ConfigError(
                    f"profile {profile_name} command {index} must be an array"
                )
            command = tuple(
                _non_empty(item, f"{profile_name}[{index}]")
                for item in raw_command
            )
            executable = Path(command[0]).name.lower()
            if executable in FORBIDDEN_EXECUTABLES:
                raise ConfigError(
                    f"profile {profile_name} uses forbidden shell: {executable}"
                )
            if any("\n" in item or "\x00" in item for item in command):
                raise ConfigError(
                    f"profile {profile_name} contains unsafe command bytes"
                )
            commands.append(command)
        profiles[profile_name] = tuple(commands)
    return profiles
