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
        "--control-root",
        type=Path,
        required=True,
    )
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
    control_root = args.control_root.resolve()
    workspace_root = args.workspace_root.resolve()
    policy = load_policy(
        control_root / ".devflow/codex-policy.yaml"
    )
    task = load_task_descriptor(
        args.task_file,
        control_root,
    )
    budget = inspect_allowed_files(
        workspace_root,
        task.allowed_files,
        task.context_budget,
    )
    if budget["status"] != "PASS":
        status = "BLOCKED"
        blocking_reason = "CONTEXT_BUDGET_FAILED"
    elif policy["mode"] == "disabled":
        status = "BLOCKED"
        blocking_reason = "CODEX_POLICY_DISABLED"
    else:
        status = "ELIGIBLE"
        blocking_reason = None
    result = {
        "status": status,
        "blocking_reason": blocking_reason,
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
