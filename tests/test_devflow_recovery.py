import sys
from pathlib import Path

DEVFLOW = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "devflow"
)
sys.path.insert(0, str(DEVFLOW))

from recovery_policy import classify  # noqa: E402


def jobs(step: str) -> dict[str, object]:
    return {
        "jobs": [
            {
                "steps": [
                    {
                        "name": step,
                        "conclusion": "failure",
                    }
                ]
            }
        ]
    }


def test_checkout_failure_retries() -> None:
    result = classify(
        source_workflow=(
            "Devflow State Consistency"
        ),
        source_run_id=1,
        conclusion="failure",
        run_attempt=1,
        jobs_payload=jobs("Checkout"),
    )
    assert result.action == "RETRY"
    assert result.notification_type is None


def test_secret_failure_is_blocked() -> None:
    result = classify(
        source_workflow="Devflow Secret Audit",
        source_run_id=2,
        conclusion="failure",
        run_attempt=1,
        jobs_payload=jobs("Secret audit"),
    )
    assert result.action == "SECURITY_BLOCKED"


def test_model_failure_never_retries() -> None:
    result = classify(
        source_workflow="Codex Candidate Review",
        source_run_id=3,
        conclusion="failure",
        run_attempt=1,
        jobs_payload=jobs(
            "Codex candidate review"
        ),
    )
    assert result.action == "INTERRUPTED"
    assert (
        "NO_AUTOMATIC_RETRY"
        in result.reason_code
    )
