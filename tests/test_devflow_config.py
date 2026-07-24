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

from config import (  # noqa: E402
    ConfigError,
    load_gate_profiles,
    load_project_config,
)


def test_project_config_loads() -> None:
    config = load_project_config()
    assert config.default_branch == "main"
    assert config.agent_execution == "disabled"
    assert config.automatic_merge is False


def test_gate_profiles_are_argument_arrays() -> None:
    profiles = load_gate_profiles()
    assert (
        profiles["repository-full"][0][0]
        == "python"
    )


def test_shell_executable_is_rejected(
    tmp_path: Path,
) -> None:
    (tmp_path / ".devflow").mkdir()
    (
        tmp_path
        / ".devflow/gate-profiles.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "profiles": {
                    "bad": [
                        [
                            "bash",
                            "-c",
                            "echo x",
                        ]
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(
        ConfigError,
        match="forbidden shell",
    ):
        load_gate_profiles(tmp_path)


def project_data() -> dict[str, object]:
    return json.loads(
        Path(".devflow/project.json").read_text(
            encoding="utf-8"
        )
    )


def write_project(
    tmp_path: Path,
    value: dict[str, object],
) -> None:
    (tmp_path / ".devflow").mkdir()
    (tmp_path / ".devflow/project.json").write_text(
        json.dumps(value),
        encoding="utf-8",
    )


def test_nested_unknown_field_fails_closed(
    tmp_path: Path,
) -> None:
    value = project_data()
    value["project"]["typo"] = True
    write_project(tmp_path, value)
    with pytest.raises(
        ConfigError,
        match="unknown project field",
    ):
        load_project_config(tmp_path)


def test_unsafe_default_branch_is_rejected(
    tmp_path: Path,
) -> None:
    value = project_data()
    value["project"]["default_branch"] = "../main"
    write_project(tmp_path, value)
    with pytest.raises(
        ConfigError,
        match="safe Git ref",
    ):
        load_project_config(tmp_path)
