import json
from pathlib import Path

FORBIDDEN_PRODUCT_MARKERS = (
    "ashare" + "_f10",
    "ashare" + "-f10",
    "688" + "521",
    "300" + "308",
    "east" + "money",
    "cn" + "info",
)


def tracked_text() -> str:
    chunks = []
    for path in Path(".").rglob("*"):
        if (
            not path.is_file()
            or ".git" in path.parts
        ):
            continue
        if path.suffix in {".pyc", ".xz"}:
            continue
        if path.as_posix() == "tests/test_devflow_neutrality.py":
            continue
        chunks.append(
            path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        )
    return "\n".join(chunks).lower()


def test_source_product_markers_absent() -> None:
    text = tracked_text()
    for marker in FORBIDDEN_PRODUCT_MARKERS:
        assert marker not in text


def test_actor_is_centralized() -> None:
    config = json.loads(
        Path(".devflow/project.json").read_text(
            encoding="utf-8"
        )
    )
    actor = config["project"][
        "allowed_actors"
    ][0]
    occurrences = []
    excluded = {
        ".devflow/project.json",
        ".devflow/codex-policy.yaml",
    }
    for path in Path(".").rglob("*"):
        if (
            not path.is_file()
            or ".git" in path.parts
            or path.as_posix() in excluded
        ):
            continue
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
        if actor in text:
            occurrences.append(
                path.as_posix()
            )
    assert occurrences == []
