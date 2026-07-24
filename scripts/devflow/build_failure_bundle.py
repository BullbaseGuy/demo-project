from __future__ import annotations

import argparse
import json
from pathlib import Path


def bounded_lines(
    path: Path,
    limit: int,
) -> list[str]:
    if not path.is_file():
        return []
    lines = path.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines()
    return lines[-limit:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--decision",
        type=Path,
        required=True,
    )
    parser.add_argument("--log", type=Path)
    parser.add_argument(
        "--max-lines",
        type=int,
        default=100,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("failure-bundle.json"),
    )
    args = parser.parse_args()
    if (
        args.max_lines < 1
        or args.max_lines > 300
    ):
        raise SystemExit(
            "max-lines must be between 1 and 300"
        )
    decision_value = json.loads(
        args.decision.read_text(
            encoding="utf-8"
        )
    )
    bundle = {
        "schema_version": 1,
        "reason_code": decision_value.get(
            "reason_code"
        ),
        "fingerprint": decision_value.get(
            "fingerprint"
        ),
        "source_workflow": decision_value.get(
            "source_workflow"
        ),
        "source_run_id": decision_value.get(
            "source_run_id"
        ),
        "failure_steps": decision_value.get(
            "failure_steps",
            [],
        ),
        "minimum_action": decision_value.get(
            "minimum_action"
        ),
        "bounded_log_tail": (
            bounded_lines(
                args.log,
                args.max_lines,
            )
            if args.log
            else []
        ),
    }
    args.output.write_text(
        json.dumps(
            bundle,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print("FAILURE_BUNDLE=CREATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
