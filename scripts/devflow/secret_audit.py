from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import urllib.parse
from collections import Counter
from pathlib import Path

STATIC_PATTERNS = {
    "PRIVATE_KEY": re.compile(
        "-----BEGIN "
        + r"(?:RSA |EC |OPENSSH |DSA )?"
        + "PRIVATE KEY-----"
    ),
    "GITHUB_TOKEN": re.compile(
        r"(?:"
        + "gh"
        + r"[pousr]_[A-Za-z0-9]{30,}|"
        + "github"
        + r"_pat_[A-Za-z0-9_]{50,})"
    ),
    "AWS_ACCESS_KEY": re.compile(
        "AK" + r"IA[0-9A-Z]{16}"
    ),
    "API_KEY": re.compile(
        "s" + r"k-[A-Za-z0-9_-]{24,}"
    ),
    "SLACK_TOKEN": re.compile(
        "xo" + r"x[baprs]-[A-Za-z0-9-]{20,}"
    ),
}


def secret_variants(value: str) -> set[str]:
    raw = value.encode()
    return {
        value,
        urllib.parse.quote(value, safe=""),
        base64.b64encode(raw).decode(),
        base64.urlsafe_b64encode(raw).decode().rstrip("="),
    }


def tracked_files(root: Path) -> list[Path]:
    try:
        output = subprocess.check_output(
            ["git", "ls-files", "-z"],
            cwd=root,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return [
            path
            for path in root.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
        ]
    return [
        root / item.decode("utf-8")
        for item in output.split(bytes([0]))
        if item
    ]


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
    matching_files = 0
    checked = 0
    match_types: Counter[str] = Counter()
    for path in tracked_files(root):
        if not path.is_file():
            continue
        checked += 1
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
        found = set()
        if any(
            item and item in text
            for item in variants
        ):
            found.add("EXPLICIT_VALUE")
        for name, pattern in STATIC_PATTERNS.items():
            if pattern.search(text):
                found.add(name)
        if found:
            matching_files += 1
            match_types.update(found)
    return {
        "status": (
            "PASS"
            if matching_files == 0
            else "FAIL"
        ),
        "checked_files": checked,
        "matching_files": matching_files,
        "match_type_counts": dict(
            sorted(match_types.items())
        ),
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
