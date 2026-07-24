from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from config import load_project_config

TERMINAL_INFRA_CONCLUSIONS = {
    "cancelled",
    "timed_out",
    "stale",
    "startup_failure",
}
INFRA_MARKERS = (
    "set up job",
    "checkout",
    "setup-python",
    "install development dependencies",
    "install trusted devflow dependencies",
    "install exact-merge development dependencies",
    "upload bounded diagnostics",
    "download artifact",
)
SECURITY_MARKERS = (
    "secret audit",
    "changed-path scope",
    "candidate scope",
    "scope guard",
    "manifest",
)
MODEL_MARKERS = (
    "codex",
    "model session",
    "agent thin worker",
)
MERGE_MARKERS = (
    "merge low-risk candidate",
    "merge exact reviewed candidate",
    "merge boundary",
)


@dataclass(frozen=True)
class RecoveryDecision:
    action: str
    reason_code: str
    reason: str
    minimum_action: str
    notification_type: str | None
    fingerprint: str
    source_workflow: str
    source_run_id: int
    run_attempt: int
    failure_steps: tuple[str, ...]


def failure_steps(
    payload: dict[str, Any],
) -> tuple[str, ...]:
    names = []
    for job in payload.get("jobs", []):
        if not isinstance(job, dict):
            continue
        for step in job.get("steps", []):
            if not isinstance(step, dict):
                continue
            if step.get("conclusion") in {
                "failure",
                "cancelled",
                "timed_out",
            }:
                name = step.get("name")
                if (
                    isinstance(name, str)
                    and name not in names
                ):
                    names.append(name)
    return tuple(names)


def contains(
    steps: tuple[str, ...],
    markers: tuple[str, ...],
) -> bool:
    lowered = tuple(
        item.lower()
        for item in steps
    )
    return any(
        marker in step
        for step in lowered
        for marker in markers
    )


def decision(
    *,
    action: str,
    reason_code: str,
    reason: str,
    minimum_action: str,
    notification_type: str | None,
    source_workflow: str,
    source_run_id: int,
    run_attempt: int,
    steps: tuple[str, ...],
) -> RecoveryDecision:
    normalized = "|".join(
        (
            source_workflow,
            reason_code,
            *sorted(
                item.lower()
                for item in steps
            ),
        )
    )
    fingerprint = hashlib.sha256(
        normalized.encode()
    ).hexdigest()[:20]
    return RecoveryDecision(
        action=action,
        reason_code=reason_code,
        reason=reason,
        minimum_action=minimum_action,
        notification_type=notification_type,
        fingerprint=fingerprint,
        source_workflow=source_workflow,
        source_run_id=source_run_id,
        run_attempt=run_attempt,
        failure_steps=steps,
    )


def classify(
    *,
    source_workflow: str,
    source_run_id: int,
    conclusion: str,
    run_attempt: int,
    jobs_payload: dict[str, Any],
) -> RecoveryDecision:
    config = load_project_config()
    steps = failure_steps(jobs_payload)
    common = {
        "source_workflow": source_workflow,
        "source_run_id": source_run_id,
        "run_attempt": run_attempt,
        "steps": steps,
    }
    if conclusion == "success":
        return decision(
            action="NOOP",
            reason_code="SOURCE_PASS",
            reason="The source workflow passed.",
            minimum_action="No action is required.",
            notification_type=None,
            **common,
        )
    if (
        source_workflow
        == config.workflows["secret_audit"]
        or contains(steps, SECURITY_MARKERS)
    ):
        return decision(
            action="SECURITY_BLOCKED",
            reason_code="SECURITY_CONTROL_FAILED",
            reason=(
                "A secret, scope or manifest "
                "control failed."
            ),
            minimum_action=(
                "Review the bounded safe summary "
                "before further execution."
            ),
            notification_type="SECURITY_BLOCKED",
            **common,
        )
    if (
        source_workflow
        == config.workflows["agent_task"]
        or contains(steps, MODEL_MARKERS)
    ):
        return decision(
            action="INTERRUPTED",
            reason_code=(
                "MODEL_JOB_NO_AUTOMATIC_RETRY"
            ),
            reason=(
                "A model-bearing job is single-use "
                "and cannot be rerun automatically."
            ),
            minimum_action=(
                "Return to ChatGPT Web and create a "
                "new reviewed task only if justified."
            ),
            notification_type="INTERRUPTED",
            **common,
        )
    if (
        source_workflow
        == config.workflows["relay_health"]
    ):
        return decision(
            action="HUMAN_REQUIRED",
            reason_code="RELAY_HEALTH_UNAVAILABLE",
            reason=(
                "Relay health requires a user-owned "
                "configuration decision."
            ),
            minimum_action=(
                "Review the private runtime configuration "
                "outside Issues and logs."
            ),
            notification_type="HUMAN_REQUIRED",
            **common,
        )
    if (
        source_workflow
        == config.workflows["product_gate"]
        and contains(steps, MERGE_MARKERS)
    ):
        return decision(
            action="HUMAN_REQUIRED",
            reason_code="MERGE_BOUNDARY_BLOCKED",
            reason=(
                "A conflict, branch protection rule "
                "or permission blocked the merge boundary."
            ),
            minimum_action=(
                "Review the merge boundary without "
                "bypassing protection."
            ),
            notification_type="HUMAN_REQUIRED",
            **common,
        )
    if (
        conclusion in TERMINAL_INFRA_CONCLUSIONS
        or contains(steps, INFRA_MARKERS)
    ):
        if (
            run_attempt
            < config.infrastructure_retry_limit
        ):
            return decision(
                action="RETRY",
                reason_code=(
                    "RETRYABLE_INFRASTRUCTURE"
                ),
                reason=(
                    "A verified ordinary infrastructure "
                    "operation may be transient."
                ),
                minimum_action=(
                    "No user action; rerun only failed "
                    "infrastructure jobs."
                ),
                notification_type=None,
                **common,
            )
        return decision(
            action="INTERRUPTED",
            reason_code=(
                "INFRASTRUCTURE_RETRY_EXHAUSTED"
            ),
            reason=(
                "The bounded infrastructure retry "
                "budget is exhausted."
            ),
            minimum_action=(
                "Review GitHub service, dependency "
                "and permission state."
            ),
            notification_type="INTERRUPTED",
            **common,
        )
    if source_workflow in {
        config.workflows["state_consistency"],
        config.workflows["product_gate"],
        config.workflows["post_merge"],
    }:
        code = {
            config.workflows[
                "state_consistency"
            ]: (
                "STATE_CONSISTENCY_"
                "WEB_REPAIR_REQUIRED"
            ),
            config.workflows[
                "product_gate"
            ]: "PRODUCT_GATE_WEB_REPAIR_REQUIRED",
            config.workflows[
                "post_merge"
            ]: "POST_MERGE_WEB_REPAIR_REQUIRED",
        }[source_workflow]
        return decision(
            action="INTERRUPTED",
            reason_code=code,
            reason=(
                "Framework, product gate and post-merge "
                "failures are repaired in ChatGPT Web."
            ),
            minimum_action=(
                "Inspect bounded evidence, repair the "
                "actual paths, then rerun deterministic gates."
            ),
            notification_type="INTERRUPTED",
            **common,
        )
    return decision(
        action="INTERRUPTED",
        reason_code="UNCLASSIFIED_FAILURE",
        reason=(
            "The failure could not be safely classified."
        ),
        minimum_action=(
            "Review bounded metadata in ChatGPT Web; "
            "do not blindly retry."
        ),
        notification_type="INTERRUPTED",
        **common,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-workflow",
        required=True,
    )
    parser.add_argument(
        "--source-run-id",
        required=True,
        type=int,
    )
    parser.add_argument(
        "--conclusion",
        required=True,
    )
    parser.add_argument(
        "--run-attempt",
        required=True,
        type=int,
    )
    parser.add_argument(
        "--jobs-json",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "devflow-recovery-decision.json"
        ),
    )
    args = parser.parse_args()
    payload = json.loads(
        args.jobs_json.read_text(
            encoding="utf-8"
        )
    )
    result = classify(
        source_workflow=args.source_workflow,
        source_run_id=args.source_run_id,
        conclusion=args.conclusion,
        run_attempt=args.run_attempt,
        jobs_payload=payload,
    )
    args.output.write_text(
        json.dumps(
            asdict(result),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            asdict(result),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
