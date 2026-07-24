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

from task_descriptor import (  # noqa: E402
    TaskDescriptor,
    TaskDescriptorError,
)


def descriptor() -> dict[str, object]:
    return json.loads(
        Path(
            "tests/fixtures/devflow/"
            "descriptor-v2.json"
        ).read_text(encoding="utf-8")
    )


def test_descriptor_loads() -> None:
    task = TaskDescriptor.from_mapping(
        descriptor()
    )
    assert task.task_id == "fixture"
    assert task.auto_merge is False


def test_config_disables_auto_merge() -> None:
    data = descriptor()
    data["auto_merge"] = True
    with pytest.raises(
        TaskDescriptorError,
        match="disables automatic merge",
    ):
        TaskDescriptor.from_mapping(data)


def test_publish_prefix_is_enforced() -> None:
    data = descriptor()
    data["publish_branch"] = "other/task"
    with pytest.raises(
        TaskDescriptorError,
        match="publish prefix",
    ):
        TaskDescriptor.from_mapping(data)


def test_unknown_field_fails_closed() -> None:
    data = descriptor()
    data["unexpected"] = True
    with pytest.raises(
        TaskDescriptorError,
        match="unknown task descriptor field",
    ):
        TaskDescriptor.from_mapping(data)


def test_path_traversal_is_rejected() -> None:
    data = descriptor()
    data["allowed_files"] = ["../outside.py"]
    with pytest.raises(
        TaskDescriptorError,
        match="stay inside the repository",
    ):
        TaskDescriptor.from_mapping(data)


def test_all_repository_protected_paths_are_required() -> None:
    data = descriptor()
    data["forbidden_patterns"] = [".github/**"]
    with pytest.raises(
        TaskDescriptorError,
        match="must include repository protected paths",
    ):
        TaskDescriptor.from_mapping(data)
