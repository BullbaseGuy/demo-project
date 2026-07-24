from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


def inspect_runtime(
    endpoint: str,
    api_key: str,
    model: str,
) -> dict[str, object]:
    failures = []
    if not endpoint:
        failures.append("MISSING_ENDPOINT")
    else:
        parsed = urlparse(endpoint)
        if (
            parsed.scheme != "https"
            or not parsed.netloc
        ):
            failures.append(
                "INVALID_ENDPOINT"
            )
    if not api_key:
        failures.append("MISSING_API_KEY")
    if not model:
        failures.append("MISSING_MODEL")
    return {
        "status": (
            "PASS"
            if not failures
            else "FAIL"
        ),
        "failure_codes": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--endpoint",
        default="",
    )
    parser.add_argument(
        "--api-key",
        default="",
    )
    parser.add_argument(
        "--model",
        default="",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "runtime-preflight.json"
        ),
    )
    args = parser.parse_args()
    result = inspect_runtime(
        args.endpoint,
        args.api_key,
        args.model,
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
