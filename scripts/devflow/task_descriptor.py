from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import ProjectConfig, load_gate_profiles, load_project_config
from context_budget import ContextBudget, ContextBudgetError

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
RISK_CLASSES = {"low", "medium", "high"}


class TaskDescriptorError(ValueError):
    pass


def _string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TaskDescriptorError(
            f"{key} must be a non-empty string"
        )
    return value.strip()


def _strings(
    data: dict[str, Any],
    key: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    value = data.get(key)
    if (
        not isinstance(value, list)
        or not all(
            isinstance(item, str) and item.strip()
            for item in value
        )
    ):
        raise TaskDescriptorError(
            f"{key} must be a string array"
        )
    if not value and not allow_empty:
        raise TaskDescriptorError(f"{key} must not be empty")
    return tuple(item.strip() for item in value)


@dataclass(frozen=True)
class TaskDescriptor:
    schema_version: int
    task_id: str
    objective: str
    base_branch: str
    publish_branch: str
    allowed_files: tuple[str, ...]
    forbidden_patterns: tuple[str, ...]
    required_changes: tuple[str, ...]
    acceptance_notes: tuple[str, ...]
    gate_profile: str
    full_gate_profile: str
    post_merge_profile: str
    context_budget: ContextBudget
    risk_class: str
    auto_merge: bool
    notify_completion: bool
    expected_base_sha: str
    stop_conditions: tuple[str, ...]

    @classmethod
    def from_mapping(
        cls,
        data: dict[str, Any],
        *,
        config: ProjectConfig | None = None,
        profiles: (
            dict[str, tuple[tuple[str, ...], ...]] | None
        ) = None,
    ) -> TaskDescriptor:
        config = config or load_project_config()
        profiles = profiles or load_gate_profiles()
        schema_version = data.get("schema_version")
        if schema_version != 2:
            raise TaskDescriptorError(
                "task descriptor schema_version must equal 2"
            )

        values = {
            key: _string(data, key)
            for key in (
                "task_id",
                "objective",
                "base_branch",
                "publish_branch",
                "gate_profile",
                "full_gate_profile",
                "post_merge_profile",
                "risk_class",
                "expected_base_sha",
            )
        }
        if values["base_branch"] != config.default_branch:
            raise TaskDescriptorError(
                "base_branch must equal configured default branch"
            )
        if not values["publish_branch"].startswith(
            config.publish_prefix
        ):
            raise TaskDescriptorError(
                "publish_branch must use configured publish prefix"
            )
        if values["risk_class"] not in RISK_CLASSES:
            raise TaskDescriptorError(
                "risk_class must be low, medium or high"
            )
        if not SHA_RE.fullmatch(values["expected_base_sha"]):
            raise TaskDescriptorError(
                "expected_base_sha must be a lowercase "
                "40-character SHA"
            )

        allowed_files = _strings(data, "allowed_files")
        forbidden_patterns = _strings(
            data,
            "forbidden_patterns",
        )
        required_changes = _strings(data, "required_changes")
        acceptance_notes = _strings(
            data,
            "acceptance_notes",
            allow_empty=True,
        )
        stop_conditions = _strings(data, "stop_conditions")
        try:
            budget = ContextBudget.from_mapping(
                data.get("context_budget")
            )
        except ContextBudgetError as exc:
            raise TaskDescriptorError(str(exc)) from exc
        if len(allowed_files) > budget.max_allowed_files:
            raise TaskDescriptorError(
                "allowed_files exceeds context budget"
            )

        for profile_name in (
            values["gate_profile"],
            values["full_gate_profile"],
            values["post_merge_profile"],
        ):
            if profile_name not in profiles:
                raise TaskDescriptorError(
                    f"unknown gate profile: {profile_name}"
                )

        auto_merge = data.get("auto_merge")
        notify_completion = data.get("notify_completion")
        if (
            not isinstance(auto_merge, bool)
            or not isinstance(notify_completion, bool)
        ):
            raise TaskDescriptorError(
                "auto_merge and notify_completion must be boolean"
            )
        if auto_merge and not config.automatic_merge:
            raise TaskDescriptorError(
                "repository configuration disables automatic merge"
            )
        if auto_merge and values["risk_class"] != "low":
            raise TaskDescriptorError(
                "automatic merge requires low risk"
            )
        if notify_completion and not auto_merge:
            raise TaskDescriptorError(
                "notify_completion requires auto_merge"
            )

        for path in allowed_files:
            if (
                auto_merge
                and any(
                    fnmatch.fnmatch(path, pattern)
                    for pattern in config.protected
                )
            ):
                raise TaskDescriptorError(
                    "automatic merge cannot modify protected paths"
                )

        return cls(
            schema_version=schema_version,
            task_id=values["task_id"],
            objective=values["objective"],
            base_branch=values["base_branch"],
            publish_branch=values["publish_branch"],
            allowed_files=allowed_files,
            forbidden_patterns=forbidden_patterns,
            required_changes=required_changes,
            acceptance_notes=acceptance_notes,
            gate_profile=values["gate_profile"],
            full_gate_profile=values["full_gate_profile"],
            post_merge_profile=values["post_merge_profile"],
            context_budget=budget,
            risk_class=values["risk_class"],
            auto_merge=auto_merge,
            notify_completion=notify_completion,
            expected_base_sha=values["expected_base_sha"],
            stop_conditions=stop_conditions,
        )


def load_task_descriptor(path: Path) -> TaskDescriptor:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TaskDescriptorError(
            f"cannot load task descriptor: {path}"
        ) from exc
    if not isinstance(data, dict):
        raise TaskDescriptorError(
            "task descriptor root must be an object"
        )
    return TaskDescriptor.from_mapping(data)
