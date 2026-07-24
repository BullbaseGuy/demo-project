from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from render_task_docs import render_handoff, render_status
from state_model import (
    TaskState,
    load_json_yaml,
    required_task_files,
)

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class FinalizeError(ValueError):
    pass


def utc_now() -> str:
    return (
        datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _task_dir(
    root: Path,
    index: dict[str, object],
    task_id: str,
) -> tuple[Path, dict[str, object]]:
    tasks = index.get("tasks")
    if not isinstance(tasks, list):
        raise FinalizeError("ACTIVE_TASKS.tasks must be an array")
    matches = [
        item
        for item in tasks
        if isinstance(item, dict)
        and item.get("task_id") == task_id
    ]
    if len(matches) != 1:
        raise FinalizeError(
            f"expected one indexed task for {task_id!r}"
        )
    entry = matches[0]
    raw_state_path = entry.get("state_path")
    if not isinstance(raw_state_path, str) or not raw_state_path:
        raise FinalizeError("indexed task state_path is missing")
    relative = PurePosixPath(raw_state_path)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or relative.name != "task_state.yaml"
        or relative.parts[:2] != ("docs", "implementation")
    ):
        raise FinalizeError(
            "state_path must be a canonical docs/implementation path"
        )
    task_dir = (root / Path(*relative.parts)).parent.resolve()
    implementation_root = (
        root / "docs/implementation"
    ).resolve()
    if implementation_root not in task_dir.parents:
        raise FinalizeError("state_path escapes docs/implementation")
    return task_dir, entry


def finalize(
    root: Path,
    task_id: str,
    merge_sha: str,
    run_id: int,
) -> dict[str, object]:
    if not SHA_RE.fullmatch(merge_sha):
        raise FinalizeError("merge_sha must be a lowercase 40-character SHA")
    if run_id <= 0:
        raise FinalizeError("run_id must be positive")

    root = root.resolve()
    index_path = root / "docs/implementation/ACTIVE_TASKS.yaml"
    index = load_json_yaml(index_path)
    task_dir, entry = _task_dir(root, index, task_id)
    state_path = task_dir / "task_state.yaml"
    data = load_json_yaml(state_path)
    current = TaskState.from_mapping(data)
    if current.task_id != task_id:
        raise FinalizeError("task index and canonical state task_id differ")

    current_post = data.get("post_merge")
    if (
        current.status == "DONE"
        and isinstance(current_post, dict)
        and current_post.get("merge_sha") == merge_sha
    ):
        return data
    if current.acceptance_status != "PASS":
        raise FinalizeError(
            "finalization requires acceptance status PASS"
        )
    if current.security_status != "PASS":
        raise FinalizeError(
            "finalization requires security status PASS"
        )
    if current.human_required:
        raise FinalizeError(
            "finalization cannot bypass an active human gate"
        )

    data["status"] = "DONE"
    data["execution_status"] = "COMPLETED"
    data["last_completed_stage"] = data["current_stage"]
    data["human_gate"] = {
        "required": False,
        "reason": None,
        "minimum_action": None,
        "resume_from": None,
    }
    previous_runs = []
    if isinstance(current_post, dict):
        raw_runs = current_post.get("verified_run_ids")
        if isinstance(raw_runs, list):
            previous_runs = [
                item
                for item in raw_runs
                if isinstance(item, int)
                and not isinstance(item, bool)
                and item > 0
            ]
    data["post_merge"] = {
        "status": "PASS",
        "merge_sha": merge_sha,
        "verified_run_ids": sorted(
            set([*previous_runs, run_id])
        ),
    }
    data["last_product_commit_sha"] = merge_sha
    data["last_successful_step"] = (
        "exact_merge_post_merge_pass"
    )
    data["next_action"] = "none"
    revision = data.get("state_revision")
    if not isinstance(revision, int) or isinstance(revision, bool):
        raise FinalizeError("state_revision must be an integer")
    data["state_revision"] = revision + 1
    data["updated_at_utc"] = utc_now()

    prospective = TaskState.from_mapping(data)
    missing = [
        path.as_posix()
        for path in required_task_files(task_dir, prospective)
        if path.name != "FINAL_REPORT.md"
        and not path.is_file()
    ]
    if missing:
        raise FinalizeError(
            "cannot finalize with missing evidence: "
            + ", ".join(missing)
        )

    state_path.write_text(
        json.dumps(
            data,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (task_dir / "STATUS.md").write_text(
        render_status(data, prospective),
        encoding="utf-8",
    )
    (task_dir / "HANDOFF.md").write_text(
        render_handoff(data, prospective),
        encoding="utf-8",
    )
    report = f"""# Final report: {prospective.task_id}

- Merge SHA: `{merge_sha}`
- Post-Merge run: `{run_id}`
- Execution: COMPLETED
- Acceptance: {prospective.acceptance_domain}/PASS
- Security: PASS
- Finalized at: {data['updated_at_utc']}
"""
    (task_dir / "FINAL_REPORT.md").write_text(
        report,
        encoding="utf-8",
    )

    entry["status"] = "DONE"
    entry["current_stage"] = data["current_stage"]
    entry["pull_request"] = data.get("pull_request")
    index_path.write_text(
        json.dumps(
            index,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
    )
    parser.add_argument(
        "--task-id",
        required=True,
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
        args.repo_root,
        args.task_id,
        args.merge_sha,
        args.run_id,
    )
    print("TASK_FINALIZED=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
