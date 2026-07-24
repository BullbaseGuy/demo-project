from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from config import load_project_config

IMPACT_ORDER = {
    "docs_only": 0,
    "devflow_only": 1,
    "product": 2,
}


@dataclass(frozen=True)
class ImpactResult:
    impact: str
    changed_files: tuple[str, ...]
    reasons: tuple[str, ...]
    run_devflow_gate: bool
    run_full_test: bool


def _matches(
    path: str,
    patterns: tuple[str, ...],
) -> bool:
    return any(
        path == pattern
        or fnmatch.fnmatch(path, pattern)
        for pattern in patterns
    )


def _normalize(path: str) -> str:
    value = path.strip()
    while value.startswith("./"):
        value = value[2:]
    return value


def classify_paths(
    paths: list[str],
) -> ImpactResult:
    config = load_project_config()
    normalized = sorted(
        {
            _normalize(path)
            for path in paths
            if _normalize(path)
        }
    )
    impact = "docs_only"
    reasons = []
    for path in normalized:
        if _matches(path, config.framework):
            if IMPACT_ORDER[impact] < 1:
                impact = "devflow_only"
            reasons.append(f"devflow:{path}")
        elif _matches(path, config.docs_only):
            reasons.append(f"docs:{path}")
        else:
            impact = "product"
            reasons.append(
                f"product_or_unknown:{path}"
            )
    if not normalized:
        impact = "devflow_only"
        reasons.append(
            "empty_diff_requires_safe_devflow_gate"
        )
    return ImpactResult(
        impact=impact,
        changed_files=tuple(normalized),
        reasons=tuple(reasons),
        run_devflow_gate=impact
        in {"devflow_only", "product"},
        run_full_test=impact == "product",
    )


def changed_files(
    base: str,
    head: str,
    repo_root: Path = Path("."),
) -> list[str]:
    output = subprocess.check_output(
        [
            "git",
            "diff",
            "--no-renames",
            "--name-only",
            "--diff-filter=ACMRTD",
            base,
            head,
        ],
        cwd=repo_root,
        text=True,
    )
    return [
        line
        for line in output.splitlines()
        if line.strip()
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument(
        "--head",
        default="HEAD",
    )
    parser.add_argument(
        "--paths-file",
        type=Path,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("change-impact.json"),
    )
    parser.add_argument(
        "--github-output",
        type=Path,
    )
    args = parser.parse_args()
    if args.paths_file:
        paths = args.paths_file.read_text(
            encoding="utf-8"
        ).splitlines()
    elif args.base:
        paths = changed_files(
            args.base,
            args.head,
        )
    else:
        raise SystemExit(
            "provide --base or --paths-file"
        )
    result = classify_paths(paths)
    text = json.dumps(
        asdict(result),
        indent=2,
        sort_keys=True,
    )
    args.output.write_text(
        text + "\n",
        encoding="utf-8",
    )
    if args.github_output:
        with args.github_output.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(
                f"impact={result.impact}\n"
            )
            handle.write(
                "run_devflow_gate="
                f"{str(result.run_devflow_gate).lower()}\n"
            )
            handle.write(
                "run_full_test="
                f"{str(result.run_full_test).lower()}\n"
            )
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
