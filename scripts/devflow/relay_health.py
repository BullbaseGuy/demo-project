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
    del args.confirmation, args.purpose
    if (
        args.mode == "paid_responses_probe"
        or not config.relay_paid_probe
    ):
        if (
            args.mode
            == "paid_responses_probe"
        ):
            status = "BLOCKED"
            reason = (
                "PAID_PROBE_DISABLED_BY_"
                "REPOSITORY_POLICY"
            )
        else:
            status = "PASS"
            reason = (
                "CONFIGURATION_ONLY_"
                "ZERO_REQUESTS"
            )
    else:
        status = "BLOCKED"
        reason = (
            "PAID_PROBE_REQUIRES_"
            "SEPARATE_ACTIVATION"
        )
    result = {
        "status": status,
        "reason_code": reason,
        "responses_requests_sent": 0,
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
