from __future__ import annotations

import argparse
import json
from pathlib import Path

from config import load_project_config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=(
            "configuration_only",
            "paid_responses_probe",
        ),
        default="configuration_only",
    )
    parser.add_argument(
        "--confirmation",
        default="",
    )
    parser.add_argument(
        "--purpose",
        default="",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("relay-health.json"),
    )
    args = parser.parse_args()
    config = load_project_config()

    if args.mode == "configuration_only":
        status = "PASS"
        reason = "CONFIGURATION_ONLY_ZERO_REQUESTS"
    elif not config.relay_paid_probe:
        status = "BLOCKED"
        reason = "PAID_PROBE_DISABLED_BY_REPOSITORY_POLICY"
    else:
        status = "BLOCKED"
        reason = "PAID_PROBE_REQUIRES_SEPARATE_ACTIVATION"

    result = {
        "status": status,
        "reason_code": reason,
        "responses_requests_sent": 0,
        "confirmation_provided": bool(
            args.confirmation.strip()
        ),
        "purpose_provided": bool(args.purpose.strip()),
    }
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
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
