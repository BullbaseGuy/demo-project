import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

DEVFLOW = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "devflow"
)
sys.path.insert(0, str(DEVFLOW))

from state_model import (  # noqa: E402
    StateError,
    TaskState,
)


def valid_state() -> dict[str, object]:
    return json.loads(
        Path(
            "tests/fixtures/devflow/"
            "state-v2-running.json"
        ).read_text(encoding="utf-8")
    )


def test_state_separates_statuses() -> None:
    state = TaskState.from_mapping(
        valid_state()
    )
    assert state.execution_status == "RUNNING"
    assert state.acceptance_domain == "generic"
    assert state.security_status == "PENDING"


def test_done_requires_post_merge_pass() -> None:
    data = valid_state()
    data.update(
        {
            "status": "DONE",
            "execution_status": "COMPLETED",
            "security_status": "PASS",
            "last_completed_stage": "W00",
        }
    )
    data["acceptance"]["status"] = "PASS"
    with pytest.raises(
        StateError,
        match="post_merge PASS",
    ):
        TaskState.from_mapping(data)


def test_human_gate_requires_resume() -> None:
    data = valid_state()
    data["status"] = "WAITING_HUMAN"
    data["human_gate"] = {
        "required": True,
        "reason": "permission",
        "minimum_action": None,
        "resume_from": None,
    }
    with pytest.raises(
        StateError,
        match="human_gate.minimum_action",
    ):
        TaskState.from_mapping(data)


def test_unknown_schema_fails_closed() -> None:
    data = deepcopy(valid_state())
    data["schema_version"] = 99
    with pytest.raises(
        StateError,
        match="unsupported",
    ):
        TaskState.from_mapping(data)
