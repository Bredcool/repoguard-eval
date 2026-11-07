
"""Scoring boundary validation and infrastructure safeguards."""

from repoguard_eval.grading.enums import ExecutionStatus
from repoguard_eval.grading.schemas import ExecutionEvidence


class InfrastructureEvaluationError(RuntimeError):
    """Raised when infrastructure failures make scoring unreliable."""


def validate_execution_boundaries(
    evidence: ExecutionEvidence,
) -> None:
    """Reject final scoring when any execution check has an infrastructure error."""

    checks = (
        ("build", evidence.build),
        ("functional", evidence.functional),
        ("hidden", evidence.hidden),
        ("regression", evidence.regression),
    ) + tuple(
        (f"language_check[{index}]", check)
        for index, check in enumerate(evidence.language_checks)
    )

    errors = [
        (name, check)
        for name, check in checks
        if check is not None and check.status == ExecutionStatus.ERROR
    ]

    if errors:
        details = ", ".join(
            f"{name} ({check.name})"
            for name, check in errors
        )
        raise InfrastructureEvaluationError(
            "Scoring aborted because execution infrastructure failed: "
            f"{details}. Retry evaluation after infrastructure recovery."
        )
