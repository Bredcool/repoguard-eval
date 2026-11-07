"""Deterministic scoring rubric and dimension weights."""

from repoguard_eval.grading.enums import ScoreDimension


RUBRIC_WEIGHTS: dict[ScoreDimension, int] = {
    ScoreDimension.ROOT_CAUSE: 20,
    ScoreDimension.TECHNICAL_CORRECTNESS: 30,
    ScoreDimension.EVIDENCE: 20,
    ScoreDimension.REGRESSION: 20,
    ScoreDimension.PATCH_SCOPE: 10,
}


ROOT_CAUSE_CRITERIA = {
    "defect_identification": 8,
    "underlying_mechanism": 6,
    "affected_component": 4,
    "expected_behavior": 2,
}

TECHNICAL_CORRECTNESS_CRITERIA = {
    "build": 5,
    "functional_tests": 10,
    "hidden_tests": 15,
}

EVIDENCE_CRITERIA = {
    "relevant_evidence": 6,
    "evidence_provenance": 6,
    "claim_traceability": 5,
    "reproducibility": 3,
}

REGRESSION_CRITERIA = {
    "existing_tests": 8,
    "regression_tests": 6,
    "boundary_cases": 4,
    "behavioral_regression": 2,
}

PATCH_SCOPE_CRITERIA = {
    "relevant_changes": 4,
    "no_unrelated_changes": 2,
    "safety": 3,
    "patch_integrity": 1,
}


def validate_rubric() -> None:
    """Raise an error if rubric weights do not total 100."""

    if sum(RUBRIC_WEIGHTS.values()) != 100:
        raise ValueError("Rubric weights must total exactly 100.")

    criteria_groups = (
        (ROOT_CAUSE_CRITERIA, 20),
        (TECHNICAL_CORRECTNESS_CRITERIA, 30),
        (EVIDENCE_CRITERIA, 20),
        (REGRESSION_CRITERIA, 20),
        (PATCH_SCOPE_CRITERIA, 10),
    )

    for criteria, expected_total in criteria_groups:
        if sum(criteria.values()) != expected_total:
            raise ValueError(
                f"Criterion weights must total {expected_total}."
            )


validate_rubric()