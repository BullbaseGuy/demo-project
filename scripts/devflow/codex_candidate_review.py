from __future__ import annotations

import argparse
import json
from pathlib import Path

from codex_policy import load_policy
from context_budget import inspect_allowed_files
from task_descriptor import load_task_descriptor


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workspace-root",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--task-file",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )
    args = parser.parse_args()
    policy = load_policy()
    task = load_task_descriptor(
        args.task_file
    )
    budget = inspect_allowed_files(
        args.workspace_root,
        task.allowed_files,
        task.context_budget,
    )
    result = {
        "status": (
            "BLOCKED"
            if policy["mode"] == "disabled"
            else "ELIGIBLE"
        ),
        "blocking_reason": (
            "CODEX_POLICY_DISABLED"
            if policy["mode"] == "disabled"
            else None
        ),
        "model_invocation": False,
        "task_id": task.task_id,
        "context_budget": budget,
        "changed_files": [],
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
