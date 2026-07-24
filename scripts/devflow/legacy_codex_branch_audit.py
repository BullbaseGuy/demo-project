from __future__ import annotations

import argparse
import json
from pathlib import Path

from config import load_project_config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--branches",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "legacy-codex-branch-audit.json"
        ),
    )
    args = parser.parse_args()
    config = load_project_config()
    value = json.loads(
        args.branches.read_text(
            encoding="utf-8"
        )
    )
    branches = [
        item
        for item in value
        if (
            isinstance(item, str)
            and item.startswith(
                config.task_data_prefix
            )
        )
    ]
    result = {
        "status": "PASS",
        "managed_branches": sorted(
            branches
        ),
        "model_execution_attempts": 0,
        "note": (
            "Historical branches are data-only "
            "and never rerun automatically."
        ),
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
