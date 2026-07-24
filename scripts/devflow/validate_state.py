from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from config import load_project_config
from state_model import (
    StateError,
    TaskState,
    load_json_yaml,
    required_task_files,
)


def current_branch() -> str:
    return subprocess.check_output(
        ["git", "branch", "--show-current"],
        text=True,
    ).strip()


def validate_task_dir(
    task_dir: Path,
    *,
    no_git: bool,
    allow_checkout_branch: bool,
) -> dict[str, object]:
    data = load_json_yaml(task_dir / "task_state.yaml")
    state = TaskState.from_mapping(data)
    missing = [
        path.as_posix()
        for path in required_task_files(task_dir, state)
        if not path.is_file()
    ]
    errors = []
    if missing:
        errors.append(
            "missing required file(s): " + ", ".join(missing)
        )
    if not no_git:
        branch = current_branch()
        if branch != state.working_branch:
            config = load_project_config()
            allowed = (
                allow_checkout_branch
                and branch
                in {
                    config.default_branch,
                    state.working_branch,
                }
            )
            if not allowed:
                errors.append(
                    f"checkout branch {branch!r} does not match "
                    f"state branch {state.working_branch!r}"
                )
    return {
        "task_id": state.task_id,
        "status": state.status,
        "state_path": (
            task_dir / "task_state.yaml"
        ).as_posix(),
        "missing": missing,
        "errors": errors,
    }


def validate_active_tasks(
    root: Path,
    *,
    no_git: bool,
    allow_checkout_branch: bool,
) -> dict[str, object]:
    index_path = (
        root
        / "docs/implementation/ACTIVE_TASKS.yaml"
    )
    index = load_json_yaml(index_path)
    if index.get("schema_version") != 1:
        raise StateError(
            "ACTIVE_TASKS schema_version must equal 1"
        )
    tasks = index.get("tasks")
    if not isinstance(tasks, list):
        raise StateError(
            "ACTIVE_TASKS.tasks must be an array"
        )
    results = []
    ids = set()
    for entry in tasks:
        if not isinstance(entry, dict):
            raise StateError(
                "ACTIVE_TASKS entries must be objects"
            )
        task_id = entry.get("task_id")
        state_path = entry.get("state_path")
        if not isinstance(task_id, str) or not task_id:
            raise StateError(
                "ACTIVE_TASKS task_id must be non-empty"
            )
        if task_id in ids:
            raise StateError(
                f"duplicate task_id: {task_id}"
            )
        ids.add(task_id)
        if not isinstance(state_path, str) or not state_path:
            raise StateError(
                f"state_path missing for {task_id}"
            )
        task_dir = (root / state_path).parent
        result = validate_task_dir(
            task_dir,
            no_git=no_git,
            allow_checkout_branch=allow_checkout_branch,
        )
        if result["task_id"] != task_id:
            result["errors"].append(
                "task index and canonical state task_id differ"
            )
        results.append(result)
    errors = [
        error
        for result in results
        for error in result["errors"]
    ]
    return {
        "status": "PASS" if not errors else "FAIL",
        "task_count": len(results),
        "tasks": results,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(
        required=True
    )
    group.add_argument(
        "--all-active",
        action="store_true",
    )
    group.add_argument("--task-dir", type=Path)
    parser.add_argument(
        "--no-git",
        action="store_true",
    )
    parser.add_argument(
        "--allow-checkout-branch",
        action="store_true",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("devflow-state-result.json"),
    )
    args = parser.parse_args()

    try:
        if args.all_active:
            result = validate_active_tasks(
                Path("."),
                no_git=args.no_git,
                allow_checkout_branch=(
                    args.allow_checkout_branch
                ),
            )
        else:
            item = validate_task_dir(
                args.task_dir,
                no_git=args.no_git,
                allow_checkout_branch=(
                    args.allow_checkout_branch
                ),
            )
            result = {
                "status": (
                    "PASS"
                    if not item["errors"]
                    else "FAIL"
                ),
                "task_count": 1,
                "tasks": [item],
                "errors": item["errors"],
            }
    except (
        StateError,
        OSError,
        subprocess.SubprocessError,
    ) as exc:
        result = {
            "status": "FAIL",
            "task_count": 0,
            "tasks": [],
            "errors": [str(exc)],
        }

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
