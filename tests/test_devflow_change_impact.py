import sys
from pathlib import Path

DEVFLOW = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "devflow"
)
sys.path.insert(0, str(DEVFLOW))

from change_impact import classify_paths  # noqa: E402


def test_docs_only() -> None:
    assert (
        classify_paths(["README.md"]).impact
        == "docs_only"
    )


def test_framework_change() -> None:
    assert (
        classify_paths(
            ["scripts/devflow/config.py"]
        ).impact
        == "devflow_only"
    )


def test_unknown_path_is_product() -> None:
    assert (
        classify_paths(["src/example.py"]).impact
        == "product"
    )


def test_empty_diff_runs_safe_gate() -> None:
    assert (
        classify_paths([]).impact
        == "devflow_only"
    )
