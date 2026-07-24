from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from render_task_docs import (
    render_handoff,
    render_status,
)
from state_model import (
    TaskState,
    load_json_yaml,
)


def utc_now() -> str:
    return (
        datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def finalize(
    task_dir: Path,
    merge_sha: str,
    run_id: int,
) -> dict[str, object]:
    path = task_dir / "task_state.yaml"
    data = load_json_yaml(path)
    data["status"] = "DONE"
    data["execution_status"] = "COMPLETED"
    if data.get("schema_version") == 2:
        data["acceptance"]["status"] = "PASS"
    else:
        data["acceptance_status"] = "PASS"
    data["security_status"] = "PASS"
    data["last_completed_stage"] = (
        data["current_stage"]
    )
    data["human_gate"] = {
        "required": False,
        "reason": None,
        "minimum_action": None,
        "resume_from": None,
    }
    data["post_merge"] = {
        "status": "PASS",
        "merge_sha": merge_sha,
        "verified_run_ids": [run_id],
    }
    data["last_successful_step"] = (
        "exact_merge_post_merge_pass"
    )
    data["next_action"] = "none"
    data["updated_at_utc"] = utc_now()
    state = TaskState.from_mapping(data)
    path.write_text(
        json.dumps(
            data,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (task_dir / "STATUS.md").write_text(
        render_status(data, state),
        encoding="utf-8",
    )
    (task_dir / "HANDOFF.md").write_text(
        render_handoff(data, state),
        encoding="utf-8",
    )
    report = f"""# Final report: {state.task_id}

- Merge SHA: `{merge_sha}`
- Post-Merge run: `{run_id}`
- Execution: COMPLETED
- Acceptance: PASS
- Security: PASS
- Finalized at: {data['updated_at_utc']}
"""
    (task_dir / "FINAL_REPORT.md").write_text(
        report,
        encoding="utf-8",
    )
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "task_dir",
        type=Path,
    )
    parser.add_argument(
        "--merge-sha",
        required=True,
    )
    parser.add_argument(
        "--run-id",
        required=True,
        type=int,
    )
    args = parser.parse_args()
    finalize(
        args.task_dir,
        args.merge_sha,
        args.run_id,
    )
    print("TASK_FINALIZED=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
