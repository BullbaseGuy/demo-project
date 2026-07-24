from __future__ import annotations

import json
import re
from pathlib import Path

from validate_codex_entrypoints import (
    validate as validate_codex_entrypoints,
)

ACTION_REF = re.compile(
    r"^\s*-?\s*uses:\s*([^\s#]+)",
    re.MULTILINE,
)
FULL_SHA = re.compile(
    r"^[0-9a-f]{40}$"
)
REQUIRED_WORKFLOWS = (
    "test.yml",
    "devflow-state-consistency.yml",
    "devflow-upgrade-compatibility.yml",
    "devflow-auto-recovery.yml",
    "devflow-incident.yml",
    "devflow-product-gate.yml",
    "devflow-post-merge.yml",
    "devflow-branch-gc.yml",
    "codex-task.yml",
    "devflow-relay-health.yml",
    "devflow-secret-audit.yml",
    "devflow-legacy-codex-rerun-audit.yml",
)


def check_action_pins(
    path: Path,
    text: str,
    errors: list[str],
) -> None:
    for reference in ACTION_REF.findall(text):
        if reference.startswith("./"):
            continue
        if "@" not in reference:
            errors.append(
                f"{path}: action lacks revision: "
                f"{reference}"
            )
            continue
        _, revision = reference.rsplit("@", 1)
        if not FULL_SHA.fullmatch(revision):
            errors.append(
                f"{path}: action must use full SHA: "
                f"{reference}"
            )


def validate_file(
    path: Path,
) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors = []
    if "pull_request_target" in text:
        errors.append(
            f"{path}: pull_request_target is forbidden"
        )
    if "permissions: write-all" in text:
        errors.append(
            f"{path}: write-all is forbidden"
        )
    if (
        "eval " in text
        or 'bash -c "${{' in text
    ):
        errors.append(
            f"{path}: evaluated workflow input is forbidden"
        )
    check_action_pins(path, text, errors)

    if path.name == "codex-task.yml":
        for fragment in (
            "workflow_dispatch:",
            "CODEX_MODEL_INVOCATION=DISABLED",
            "persist-credentials: false",
            "codex_candidate_review.py",
        ):
            if fragment not in text:
                errors.append(
                    f"{path}: missing disabled-mode "
                    f"fragment: {fragment}"
                )
        for forbidden in (
            "environment:",
            "secrets.",
            "openai/codex-action@",
        ):
            if forbidden in text:
                errors.append(
                    f"{path}: forbidden model/secret "
                    f"field: {forbidden}"
                )

    if (
        path.name
        == "devflow-auto-recovery.yml"
    ):
        for forbidden in (
            "Codex Candidate Review",
            "Devflow Relay Health",
            "codex-task.yml/dispatches",
            "RETRY_CODEX",
        ):
            if forbidden in text:
                errors.append(
                    f"{path}: automatic model or paid "
                    f"path forbidden: {forbidden}"
                )
        if (
            "rerun-failed-jobs" not in text
            or "recovery_policy.py" not in text
        ):
            errors.append(
                f"{path}: bounded infrastructure "
                "recovery is incomplete"
            )

    if (
        path.name
        == "devflow-secret-audit.yml"
        and "workflow_run:" in text
    ):
        errors.append(
            f"{path}: secret audit must not "
            "trigger automatically"
        )

    if (
        path.name == "devflow-incident.yml"
        and "workflow_run:" in text
    ):
        errors.append(
            f"{path}: incident workflow must "
            "receive classified dispatch only"
        )
    return errors


def main() -> int:
    root = Path(".github/workflows")
    errors = []
    found = []
    for name in REQUIRED_WORKFLOWS:
        path = root / name
        if not path.is_file():
            errors.append(
                f"missing workflow: {path}"
            )
            continue
        found.append(path.as_posix())
        errors.extend(
            validate_file(path)
        )
    for temporary in sorted(
        root.glob("apply-scaffold.yml")
    ):
        errors.append(
            "temporary bootstrap workflow "
            f"must be removed: {temporary}"
        )
    if Path("bootstrap").exists():
        errors.append(
            "temporary bootstrap directory "
            "must be removed"
        )
    entrypoints = validate_codex_entrypoints()
    errors.extend(
        f"codex-entrypoint: {item}"
        for item in entrypoints["errors"]
    )
    summary = {
        "status": (
            "PASS"
            if not errors
            else "FAIL"
        ),
        "files": found,
        "automatic_model_paths": (
            entrypoints[
                "automatic_model_paths"
            ]
        ),
        "automatic_paid_probe_retries": (
            entrypoints[
                "automatic_paid_probe_retries"
            ]
        ),
        "errors": errors,
    }
    Path(
        "devflow-workflow-validation.json"
    ).write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
