from __future__ import annotations

import json
from pathlib import Path

from codex_policy import load_policy


def validate(
    root: Path = Path("."),
) -> dict[str, object]:
    errors = []
    policy = load_policy(
        root / ".devflow/codex-policy.yaml"
    )
    manifest_path = (
        root
        / ".devflow/codex-entrypoints.yaml"
    )
    try:
        manifest = json.loads(
            manifest_path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        return {
            "status": "FAIL",
            "automatic_model_paths": 0,
            "automatic_paid_probe_retries": 0,
            "errors": [str(exc)],
        }
    if policy["mode"] != "disabled":
        errors.append(
            "default scaffold policy "
            "must remain disabled"
        )
    if (
        manifest.get("policy_mode")
        != "disabled"
    ):
        errors.append(
            "entrypoint manifest policy "
            "must remain disabled"
        )
    text = "\n".join(
        path.read_text(
            encoding="utf-8"
        )
        for path in sorted(
            (root / ".github").rglob("*")
        )
        if path.is_file()
    )
    forbidden = (
        "openai/codex-action@",
        (
            "actions/workflows/"
            "codex-task.yml/dispatches"
        ),
        "RETRY_CODEX",
    )
    automatic_model_paths = sum(
        text.count(item)
        for item in forbidden
    )
    if automatic_model_paths:
        errors.append(
            "automatic model path detected"
        )
    recovery_path = (
        root
        / ".github/workflows/devflow-auto-recovery.yml"
    )
    recovery_text = (
        recovery_path.read_text(encoding="utf-8")
        if recovery_path.is_file()
        else ""
    )
    auto_paid = int(
        "rerun-failed-jobs" in recovery_text
        and "Devflow Relay Health" in recovery_text
    )
    if auto_paid:
        errors.append(
            "automatic paid-probe retry detected"
        )
    return {
        "status": (
            "PASS"
            if not errors
            else "FAIL"
        ),
        "automatic_model_paths": (
            automatic_model_paths
        ),
        "automatic_paid_probe_retries": (
            auto_paid
        ),
        "errors": errors,
    }


if __name__ == "__main__":
    result = validate()
    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )
    raise SystemExit(
        0
        if result["status"] == "PASS"
        else 1
    )
