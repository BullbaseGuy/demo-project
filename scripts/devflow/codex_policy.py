from __future__ import annotations

import json
from pathlib import Path


class CodexPolicyError(ValueError):
    pass


def load_policy(
    path: Path = Path(
        ".devflow/codex-policy.yaml"
    ),
) -> dict[str, object]:
    try:
        value = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise CodexPolicyError(
            "cannot load Codex policy"
        ) from exc
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != 1
    ):
        raise CodexPolicyError(
            "unsupported Codex policy"
        )
    if value.get("mode") not in {
        "disabled",
        "enabled",
    }:
        raise CodexPolicyError(
            "Codex policy mode must be "
            "disabled or enabled"
        )
    limits = value.get("limits")
    if not isinstance(limits, dict):
        raise CodexPolicyError(
            "Codex policy limits must "
            "be an object"
        )
    for key in (
        "calls_per_task",
        "calls_per_fingerprint",
    ):
        if limits.get(key) != 1:
            raise CodexPolicyError(
                f"{key} must equal 1"
            )
    for key in (
        "automatic_second_session",
        "recovery_generations",
    ):
        if limits.get(key) != 0:
            raise CodexPolicyError(
                f"{key} must equal 0"
            )
    return value
