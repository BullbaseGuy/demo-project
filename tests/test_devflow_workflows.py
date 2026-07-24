import sys
from pathlib import Path

DEVFLOW = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "devflow"
)
sys.path.insert(0, str(DEVFLOW))

from validate_codex_entrypoints import (  # noqa: E402
    validate,
)
from validate_workflows import validate_file  # noqa: E402


def test_workflows_pass_policy() -> None:
    for path in Path(
        ".github/workflows"
    ).glob("*.yml"):
        assert validate_file(path) == []


def test_no_automatic_model_path() -> None:
    result = validate()
    assert result["status"] == "PASS"
    assert (
        result["automatic_model_paths"]
        == 0
    )
    assert (
        result[
            "automatic_paid_probe_retries"
        ]
        == 0
    )
