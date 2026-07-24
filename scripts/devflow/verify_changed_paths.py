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
) -> list[str]:
    output = subprocess.check_output(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            base,
            head,
        ],
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
            fnmatch.fnmatch(path, pattern)
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
        "status": (
            "PASS"
            if not violations
            else "FAIL"
        ),
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
    task = load_task_descriptor(args.task_file)
    result = verify(
        git_changed_files(
            args.base,
            args.head,
        ),
        task.allowed_files,
        task.forbidden_patterns,
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
