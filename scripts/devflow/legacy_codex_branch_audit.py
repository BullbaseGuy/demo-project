from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from config import load_project_config

ALLOWED_TASK_DATA_PATHS = {
    ".agent/current_task.yaml",
}


def command(
    args: list[str],
    *,
    cwd: Path,
) -> str:
    return subprocess.check_output(
        args,
        cwd=cwd,
        text=True,
    ).strip()


def audit_branch(
    repo_root: Path,
    default_branch: str,
    branch: str,
) -> dict[str, object]:
    remote_ref = f"refs/remotes/origin/{branch}"
    try:
        subprocess.run(
            [
                "git",
                "fetch",
                "--no-tags",
                "origin",
                f"+refs/heads/{branch}:{remote_ref}",
            ],
            cwd=repo_root,
            check=True,
            text=True,
            stdout=subprocess.DEVNULL,
        )
        merge_base = command(
            [
                "git",
                "merge-base",
                f"origin/{default_branch}",
                remote_ref,
            ],
            cwd=repo_root,
        )
        output = command(
            [
                "git",
                "diff",
                "--no-renames",
                "--name-only",
                "--diff-filter=ACMRTD",
                merge_base,
                remote_ref,
            ],
            cwd=repo_root,
        )
    except subprocess.SubprocessError as exc:
        return {
            "branch": branch,
            "status": "FAIL",
            "reason": "BRANCH_FETCH_OR_DIFF_FAILED",
            "error_type": type(exc).__name__,
            "changed_paths": [],
            "violations": [],
        }
    changed = sorted(
        line
        for line in output.splitlines()
        if line.strip()
    )
    violations = [
        path
        for path in changed
        if path not in ALLOWED_TASK_DATA_PATHS
    ]
    return {
        "branch": branch,
        "status": "PASS" if not violations else "FAIL",
        "reason": (
            "DATA_ONLY"
            if not violations
            else "CONTROL_OR_PRODUCT_PATH_CHANGED"
        ),
        "changed_paths": changed,
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--branches",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "legacy-codex-branch-audit.json"
        ),
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    config = load_project_config(repo_root)
    value = json.loads(
        args.branches.read_text(
            encoding="utf-8"
        )
    )
    if not isinstance(value, list):
        raise SystemExit("branches input must be an array")
    branches = sorted(
        item
        for item in value
        if (
            isinstance(item, str)
            and item.startswith(
                config.task_data_prefix
            )
        )
    )
    subprocess.run(
        [
            "git",
            "fetch",
            "--no-tags",
            "origin",
            config.default_branch,
        ],
        cwd=repo_root,
        check=True,
        text=True,
        stdout=subprocess.DEVNULL,
    )
    results = [
        audit_branch(
            repo_root,
            config.default_branch,
            branch,
        )
        for branch in branches
    ]
    failures = [
        item
        for item in results
        if item["status"] != "PASS"
    ]
    result = {
        "status": "PASS" if not failures else "FAIL",
        "managed_branch_count": len(branches),
        "failed_branch_count": len(failures),
        "branches": results,
        "model_execution_attempts": 0,
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
