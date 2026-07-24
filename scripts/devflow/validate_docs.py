from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

LINK_RE = re.compile(
    r"(?<!!)\[[^\]]+\]\(([^)]+)\)"
)
REQUIRED = (
    Path("AGENTS.md"),
    Path("README.md"),
    Path("docs/process/README.md"),
    Path("docs/process/PROJECT_INSTRUCTIONS.md"),
    Path("docs/implementation/ACTIVE_TASKS.yaml"),
    Path(
        "docs/process/templates/"
        "task_state.template.yaml"
    ),
)


def validate(root: Path) -> dict[str, object]:
    errors = []
    checked_links = 0
    for path in REQUIRED:
        if not (root / path).is_file():
            errors.append(
                "missing required document: "
                + path.as_posix()
            )

    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for raw in LINK_RE.findall(text):
            target = raw.split("#", 1)[0].strip()
            if (
                not target
                or "://" in target
                or target.startswith(("mailto:", "#"))
            ):
                continue
            checked_links += 1
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(
                    f"{path}: relative link escapes "
                    f"repository: {raw}"
                )
                continue
            if not resolved.exists():
                errors.append(
                    f"{path}: broken relative link: {raw}"
                )

    for path in sorted(
        (root / "docs").rglob("*.yaml")
    ):
        try:
            value = json.loads(
                path.read_text(encoding="utf-8")
            )
        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:
            errors.append(
                f"{path}: JSON-as-YAML parse failure: {exc}"
            )
            continue
        if not isinstance(value, dict):
            errors.append(
                f"{path}: JSON-as-YAML root must be an object"
            )

    return {
        "status": "PASS" if not errors else "FAIL",
        "checked_links": checked_links,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "devflow-docs-validation.json"
        ),
    )
    args = parser.parse_args()
    result = validate(Path("."))
    args.output.write_text(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
