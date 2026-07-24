import json
import sys
from pathlib import Path

import pytest

DEVFLOW = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "devflow"
)
sys.path.insert(0, str(DEVFLOW))

from branch_gc import active_task_branches  # noqa: E402
from finalize_task import FinalizeError, finalize  # noqa: E402
from secret_audit import audit  # noqa: E402


def build_task(root: Path, acceptance: str = "PASS") -> Path:
    task_id = "sample"
    task_dir = root / "docs/implementation" / task_id
    task_dir.mkdir(parents=True)
    state = json.loads(
        Path(
            "tests/fixtures/devflow/state-v2-running.json"
        ).read_text(encoding="utf-8")
    )
    state.update(
        {
            "task_id": task_id,
            "title": "Sample",
            "status": "VERIFYING",
            "execution_status": "COMPLETED",
            "security_status": "PASS",
            "working_branch": "feature/sample",
            "pull_request": 7,
            "last_successful_step": "full_gate_pass",
            "next_action": "post_merge",
        }
    )
    state["acceptance"]["status"] = acceptance
    state["notification"]["control_issue_number"] = 3
    (task_dir / "task_state.yaml").write_text(
        json.dumps(state, indent=2) + "\n",
        encoding="utf-8",
    )
    for name in (
        "00_contract.md",
        "01_master_plan.md",
        "STATUS.md",
        "HANDOFF.md",
        "DECISIONS.md",
        "W00_plan.md",
        "W00_result.md",
    ):
        (task_dir / name).write_text(
            f"# {name}\n",
            encoding="utf-8",
        )
    index = {
        "schema_version": 1,
        "tasks": [
            {
                "task_id": task_id,
                "title": "Sample",
                "status": "VERIFYING",
                "branch": "feature/sample",
                "task_branch": "task/agent-sample",
                "publish_branch": "agent/sample",
                "pull_request": 7,
                "current_stage": "W00",
                "post_merge_profile": "post-merge",
                "notify_completion": True,
                "state_path": (
                    "docs/implementation/sample/task_state.yaml"
                ),
            }
        ],
    }
    (root / "docs/implementation/ACTIVE_TASKS.yaml").write_text(
        json.dumps(index, indent=2) + "\n",
        encoding="utf-8",
    )
    return task_dir


def test_finalize_preserves_acceptance_and_security(
    tmp_path: Path,
) -> None:
    task_dir = build_task(tmp_path)
    result = finalize(
        tmp_path,
        "sample",
        "b" * 40,
        123,
    )
    assert result["status"] == "DONE"
    assert result["acceptance"]["status"] == "PASS"
    assert result["security_status"] == "PASS"
    assert result["post_merge"]["merge_sha"] == "b" * 40
    assert (task_dir / "FINAL_REPORT.md").is_file()
    index = json.loads(
        (
            tmp_path
            / "docs/implementation/ACTIVE_TASKS.yaml"
        ).read_text(encoding="utf-8")
    )
    assert index["tasks"][0]["status"] == "DONE"


def test_finalize_refuses_unaccepted_domain_result(
    tmp_path: Path,
) -> None:
    build_task(tmp_path, acceptance="REVIEW_REQUIRED")
    with pytest.raises(
        FinalizeError,
        match="acceptance status PASS",
    ):
        finalize(
            tmp_path,
            "sample",
            "b" * 40,
            123,
        )


def test_all_active_task_branches_are_protected() -> None:
    index = {
        "tasks": [
            {
                "status": "RUNNING",
                "branch": "feature/sample",
                "task_branch": "task/agent-sample",
                "publish_branch": "agent/sample",
            },
            {
                "status": "DONE",
                "branch": "feature/old",
                "task_branch": "task/agent-old",
                "publish_branch": "agent/old",
            },
        ]
    }
    assert active_task_branches(index) == {
        "feature/sample",
        "task/agent-sample",
        "agent/sample",
    }


def test_explicit_secret_value_is_detected_without_disclosure(
    tmp_path: Path,
) -> None:
    value = "test-secret-value-for-audit"
    (tmp_path / "tracked.txt").write_text(
        value,
        encoding="utf-8",
    )
    result = audit(tmp_path, [value])
    assert result["status"] == "FAIL"
    assert result["matching_files"] == 1
    assert value not in json.dumps(result)
