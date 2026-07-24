import sys
from pathlib import Path

DEVFLOW = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "devflow"
)
sys.path.insert(0, str(DEVFLOW))

from upgrade_compatibility import run_matrix  # noqa: E402


def test_compatibility_matrix_passes() -> None:
    result = run_matrix(
        Path("tests/fixtures/devflow")
    )
    assert result["status"] == "PASS"
