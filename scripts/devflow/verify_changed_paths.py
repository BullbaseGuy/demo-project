from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from pathlib import Path

from task_descriptor import load_task_descriptor


def git_changed_files(
    base: str,
    head: str,
    repo_root: Path = Path("."),
) -> list[str]:
    output = subprocess.check_output(
        [
            "git",
            "diff",
            "--no-renames",
            "--name-only",
            "--diff-filter=ACMRTD",
            base,
            head,
        ],
        cwd=repo_root,
        text=True,
    )
    return [
        line
        for line in output.splitlines()
        if line.strip()
    ]


def verify(
    paths: list[str],
    allowed: tuple[str, ...],
    forbidden: tuple[str, ...],
) -> dict[str, object]:
    violations = []
    for path in sorted(set(paths)):
        if any(
            path == pattern
            or fnmatch.fnmatch(path, pattern)
            for pattern in forbidden
        ):
            violations.append(
                {
                    "path": path,
                    "reason": "FORBIDDEN_PATTERN",
                }
            )
            continue
        if not any(
            path == pattern
            or fnmatch.fnmatch(path, pattern)
            for pattern in allowed
        ):
            violations.append(
                {
                    "path": path,
                    "reason": "OUTSIDE_ALLOWED_FILES",
                }
            )
    return {
        "status": "PASS" if not violations else "FAIL",
        "changed_files": sorted(set(paths)),
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--task-file",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--config-root",
        type=Path,
        default=Path("."),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
    )
    parser.add_argument(
        "--base",
        required=True,
    )
    parser.add_argument(
        "--head",
        default="HEAD",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("scope-result.json"),
    )
    args = parser.parse_args()
    config_root = args.config_root.resolve()
    repo_root = args.repo_root.resolve()
    task = load_task_descriptor(
        args.task_file,
        config_root,
    )
    changed = git_changed_files(
        args.base,
        args.head,
        repo_root,
    )
    result = verify(
        changed,
        task.allowed_files,
        task.forbidden_patterns,
    )
    violations = result["violations"]
    if not changed:
        violations.append(
            {
                "path": None,
                "reason": "NO_CHANGED_FILES",
            }
        )
    if task.auto_merge and len(changed) > 5:
        violations.append(
            {
                "path": None,
                "reason": "AUTO_MERGE_FILE_LIMIT_EXCEEDED",
            }
        )
    result["status"] = (
        "PASS"
        if not violations
        else "FAIL"
    )
    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
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
