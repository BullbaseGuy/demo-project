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


def require_fragments(
    path: Path,
    text: str,
    fragments: tuple[str, ...],
    errors: list[str],
) -> None:
    for fragment in fragments:
        if fragment not in text:
            errors.append(
                f"{path}: missing required fragment: {fragment}"
            )


def forbid_fragments(
    path: Path,
    text: str,
    fragments: tuple[str, ...],
    errors: list[str],
) -> None:
    for fragment in fragments:
        if fragment in text:
            errors.append(
                f"{path}: forbidden fragment: {fragment}"
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
        require_fragments(
            path,
            text,
            (
                "workflow_dispatch:",
                "path: control",
                "path: workspace",
                "--control-root .",
                "CODEX_MODEL_INVOCATION=DISABLED",
                "persist-credentials: false",
                "codex_candidate_review.py",
            ),
            errors,
        )
        forbid_fragments(
            path,
            text,
            (
                "environment:",
                "secrets.",
                "openai/codex-action@",
            ),
            errors,
        )

    if path.name == "devflow-product-gate.yml":
        require_fragments(
            path,
            text,
            (
                "path: control",
                "path: task-data",
                "path: candidate",
                "--config-root control",
                "--repo-root candidate",
                "--workdir candidate",
                "Run trusted targeted gate",
                "Run trusted full gate",
                "Merge exact reviewed candidate without executing it",
                "expected_base_sha",
                "publish_commit_sha",
            ),
            errors,
        )
        if text.count("permissions:\n      contents: write") < 2:
            errors.append(
                f"{path}: notification and merge write jobs must be isolated"
            )

    if path.name == "devflow-post-merge.yml":
        require_fragments(
            path,
            text,
            (
                "pull_request:",
                "types:\n      - closed",
                "path: workspace",
                "path: control",
                "Run independent exact-merge profile",
                "finalize_task.py",
                "Commit canonical task completion",
                "devflow_notify",
            ),
            errors,
        )

    if path.name == "devflow-auto-recovery.yml":
        require_fragments(
            path,
            text,
            (
                "actions: write",
                "contents: write",
                "rerun-failed-jobs",
                "recovery_policy.py",
                "value['task_id'] = task_id or '__repository__'",
                "devflow_notify",
            ),
            errors,
        )
        forbid_fragments(
            path,
            text,
            (
                "Codex Candidate Review",
                "Devflow Relay Health",
                "codex-task.yml/dispatches",
                "RETRY_CODEX",
            ),
            errors,
        )

    if path.name == "devflow-secret-audit.yml":
        if "workflow_run:" in text:
            errors.append(
                f"{path}: secret audit must not trigger automatically"
            )
        require_fragments(
            path,
            text,
            ("workflow_dispatch:", "secret_audit.py"),
            errors,
        )

    if path.name == "devflow-incident.yml":
        if "workflow_run:" in text:
            errors.append(
                f"{path}: incident workflow must receive classified dispatch only"
            )
        require_fragments(
            path,
            text,
            (
                "repository_dispatch:",
                "devflow_notify",
                "[DEVFLOW CONTROL] Repository automation",
                "control_issue_number",
                "devflow-root:",
            ),
            errors,
        )

    if path.name == "devflow-legacy-codex-rerun-audit.yml":
        require_fragments(
            path,
            text,
            (
                "schedule:",
                "create:",
                "fetch-depth: 0",
                "legacy_codex_branch_audit.py",
            ),
            errors,
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
