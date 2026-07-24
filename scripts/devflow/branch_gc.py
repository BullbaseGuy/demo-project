from __future__ import annotations

import argparse
import json
from pathlib import Path

from config import load_project_config
from state_model import load_json_yaml


def build_plan(
    candidates: list[str],
    active_branches: set[str],
    open_pr_heads: set[str],
    *,
    execute_requested: bool,
) -> dict[str, object]:
    config = load_project_config()
    managed_prefixes = (
        config.task_data_prefix,
        config.publish_prefix,
    )
    deletable = []
    blocked = []
    for branch in sorted(set(candidates)):
        if not branch.startswith(
            managed_prefixes
        ):
            blocked.append(
                {
                    "branch": branch,
                    "reason": "UNMANAGED_PREFIX",
                }
            )
        elif branch in active_branches:
            blocked.append(
                {
                    "branch": branch,
                    "reason": "ACTIVE_TASK",
                }
            )
        elif branch in open_pr_heads:
            blocked.append(
                {
                    "branch": branch,
                    "reason": "OPEN_PULL_REQUEST",
                }
            )
        else:
            deletable.append(branch)
    execute = bool(
        execute_requested
        and config.branch_gc_execute
    )
    return {
        "status": "PASS",
        "mode": (
            "EXECUTE"
            if execute
            else "DRY_RUN"
        ),
        "deletable": deletable,
        "blocked": blocked,
        "execute_allowed": (
            config.branch_gc_execute
        ),
    }


def active_task_branches(
    index: dict[str, object],
) -> set[str]:
    result = set()
    tasks = index.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError(
            "ACTIVE_TASKS.tasks must be an array"
        )
    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        if entry.get("status") == "DONE":
            continue
        for key in (
            "branch",
            "task_branch",
            "publish_branch",
        ):
            value = entry.get(key)
            if isinstance(value, str) and value:
                result.add(value)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--active-tasks",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--open-prs",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--candidate",
        action="append",
        default=[],
    )
    parser.add_argument(
        "--execute",
        action="store_true",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("branch-gc-plan.json"),
    )
    args = parser.parse_args()
    index = load_json_yaml(args.active_tasks)
    active = active_task_branches(index)
    raw_prs = json.loads(
        args.open_prs.read_text(
            encoding="utf-8"
        )
    )
    open_heads = {
        entry.get("head")
        for entry in raw_prs
        if (
            isinstance(entry, dict)
            and isinstance(
                entry.get("head"),
                str,
            )
        )
    }
    result = build_plan(
        args.candidate,
        active,
        open_heads,
        execute_requested=args.execute,
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
