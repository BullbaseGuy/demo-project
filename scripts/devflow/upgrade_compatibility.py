from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from state_model import StateError, TaskState
from task_descriptor import (
    TaskDescriptor,
    TaskDescriptorError,
)


def load_object(
    path: Path,
) -> dict[str, Any]:
    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )
    if not isinstance(value, dict):
        raise ValueError(
            f"fixture root must be object: {path}"
        )
    return value


def preview_state_v2(
    value: dict[str, Any],
) -> dict[str, Any]:
    if value.get("schema_version") == 2:
        TaskState.from_mapping(value)
        return deepcopy(value)
    if value.get("schema_version") != 1:
        raise StateError(
            "unsupported state schema"
        )
    migrated = deepcopy(value)
    legacy = migrated.pop(
        "acceptance_status",
        migrated.pop(
            "research_acceptance_status",
            None,
        ),
    )
    if not isinstance(legacy, str):
        raise StateError(
            "schema v1 migration requires "
            "acceptance status"
        )
    migrated["schema_version"] = 2
    migrated["acceptance"] = {
        "domain": "generic",
        "status": legacy,
        "reason_code": None,
        "details_path": None,
    }
    migrated.setdefault(
        "security_status",
        (
            "PASS"
            if migrated.get("status") == "DONE"
            else "PENDING"
        ),
    )
    TaskState.from_mapping(migrated)
    return migrated


def run_matrix(
    root: Path,
) -> dict[str, object]:
    cases: dict[str, dict[str, object]] = {}
    failed = []

    def record(name: str, function) -> None:
        try:
            details = function()
        except Exception as exc:
            cases[name] = {
                "status": "FAIL",
                "error_type": type(exc).__name__,
                "error": str(exc)[:300],
            }
            failed.append(name)
        else:
            cases[name] = {
                "status": "PASS",
                **(details or {}),
            }

    state_v1 = load_object(
        root / "state-v1-done.json"
    )
    state_v2 = load_object(
        root / "state-v2-running.json"
    )
    descriptor_v2 = load_object(
        root / "descriptor-v2.json"
    )

    record(
        "state_v1_read",
        lambda: {
            "status_value": (
                TaskState.from_mapping(
                    state_v1
                ).status
            )
        },
    )
    record(
        "state_v2_read",
        lambda: {
            "status_value": (
                TaskState.from_mapping(
                    state_v2
                ).status
            )
        },
    )
    record(
        "descriptor_v2_read",
        lambda: {
            "task_id": (
                TaskDescriptor.from_mapping(
                    descriptor_v2
                ).task_id
            )
        },
    )

    def migration() -> dict[str, object]:
        original = deepcopy(state_v1)
        preview = preview_state_v2(state_v1)
        repeated = preview_state_v2(preview)
        if (
            original != state_v1
            or preview != repeated
        ):
            raise AssertionError(
                "migration preview is not idempotent"
            )
        return {
            "schema_version": preview[
                "schema_version"
            ],
            "status_preserved": preview["status"],
        }

    record(
        "state_v1_to_v2_preview",
        migration,
    )

    def unknown_state() -> dict[str, object]:
        invalid = deepcopy(state_v2)
        invalid["schema_version"] = 99
        try:
            TaskState.from_mapping(invalid)
        except StateError:
            return {"rejected": True}
        raise AssertionError(
            "unknown state schema accepted"
        )

    record(
        "unknown_state_rejected",
        unknown_state,
    )

    def unknown_descriptor() -> dict[str, object]:
        invalid = deepcopy(descriptor_v2)
        invalid["schema_version"] = 99
        try:
            TaskDescriptor.from_mapping(
                invalid
            )
        except TaskDescriptorError:
            return {"rejected": True}
        raise AssertionError(
            "unknown descriptor schema accepted"
        )

    record(
        "unknown_descriptor_rejected",
        unknown_descriptor,
    )
    return {
        "status": (
            "PASS"
            if not failed
            else "FAIL"
        ),
        "cases": cases,
        "failed_cases": failed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fixtures-root",
        type=Path,
        default=Path(
            "tests/fixtures/devflow"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "devflow-upgrade-compatibility.json"
        ),
    )
    args = parser.parse_args()
    result = run_matrix(
        args.fixtures_root
    )
    args.output.write_text(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
