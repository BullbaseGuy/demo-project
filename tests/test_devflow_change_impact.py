import subprocess
import sys
from pathlib import Path

DEVFLOW = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "devflow"
)
sys.path.insert(0, str(DEVFLOW))

from change_impact import (  # noqa: E402
    changed_files,
    classify_paths,
)
from verify_changed_paths import (  # noqa: E402
    git_changed_files,
    verify,
)


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


def test_forbidden_path_is_rejected() -> None:
    result = verify(
        ["scripts/devflow/config.py"],
        ("src/**",),
        ("scripts/devflow/**",),
    )
    assert result["status"] == "FAIL"
    assert result["violations"][0]["reason"] == "FORBIDDEN_PATTERN"


def test_deleted_file_is_returned_by_git_diff(
    tmp_path: Path,
) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        check=True,
    )
    tracked = tmp_path / "protected.txt"
    tracked.write_text("tracked\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "base"],
        cwd=tmp_path,
        check=True,
    )
    base = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        text=True,
    ).strip()
    tracked.unlink()
    subprocess.run(
        ["git", "add", "-A"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "delete"],
        cwd=tmp_path,
        check=True,
    )
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        text=True,
    ).strip()
    assert changed_files(
        base,
        head,
        tmp_path,
    ) == ["protected.txt"]
    assert git_changed_files(
        base,
        head,
        tmp_path,
    ) == ["protected.txt"]
