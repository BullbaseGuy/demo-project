from __future__ import annotations

import argparse
import base64
import json
import urllib.parse
from pathlib import Path


def secret_variants(value: str) -> set[str]:
    raw = value.encode()
    return {
        value,
        urllib.parse.quote(value, safe=""),
        base64.b64encode(raw).decode(),
        base64.urlsafe_b64encode(raw).decode().rstrip("="),
    }


def audit(
    root: Path,
    values: list[str],
) -> dict[str, object]:
    variants = set()
    for value in values:
        if value:
            variants.update(
                secret_variants(value)
            )
    matches = 0
    checked = 0
    for path in root.rglob("*"):
        if (
            not path.is_file()
            or ".git" in path.parts
        ):
            continue
        checked += 1
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
        if any(
            item and item in text
            for item in variants
        ):
            matches += 1
    return {
        "status": (
            "PASS"
            if matches == 0
            else "FAIL"
        ),
        "checked_files": checked,
        "matching_files": matches,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--value",
        action="append",
        default=[],
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("secret-audit.json"),
    )
    args = parser.parse_args()
    result = audit(
        Path("."),
        args.value,
    )
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
