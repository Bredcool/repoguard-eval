import pytest

from repoguard_eval.grading.enums import ScoreDimension
from repoguard_eval.grading.root_cause import (
    RootCauseAssessor,
    RootCauseReference,
)


@pytest.fixture
def reference():
    return RootCauseReference(
        defect_identification=[
            "pagination off by one",
            "incorrect pagination boundary",
        ],
        underlying_mechanism=[
            "page offset calculated incorrectly",
        ],
        affected_component=[
            "pagination service",
        ],
        expected_behavior=[
            "return the correct page of results",
        ],
    )


@pytest.fixture
def assessor():
    return RootCauseAssessor()


def test_perfect_root_cause_score(assessor, reference):
    result = assessor.assess(
        reference,
        (
            "The pagination off by one defect occurs because "
            "page offset calculated incorrectly in the pagination service. "
            "The fix should return the correct page of results."
        ),
    )

    assert result.dimension == ScoreDimension.ROOT_CAUSE
    assert result.score == 20
    assert result.maximum_score == 20


def test_partial_root_cause_score(assessor, reference):
    result = assessor.assess(
        reference,
        "The pagination boundary is incorrect because its offset is wrong.",
    )

    assert 0 < result.score < 20


def test_incorrect_root_cause_scores_zero(assessor, reference):
    result = assessor.assess(
        reference,
        "The database connection pool is leaking resources.",
    )

    assert result.score == 0
    assert result.maximum_score == 20


def test_empty_diagnosis_scores_zero(assessor, reference):
    result = assessor.assess(reference, "")

    assert result.score == 0


def test_criteria_weights_sum_to_twenty(assessor, reference):
    result = assessor.assess(reference, "pagination off by one")

    assert sum(item.maximum_points for item in result.criteria) == 20
    assert result.maximum_score == 20


def test_evidence_references_are_preserved(assessor, reference):
    evidence = ["src/service/pagination.go:42"]

    result = assessor.assess(
        reference,
        "pagination off by one",
        evidence_refs=evidence,
    )

    assert all(list(item.evidence_refs) == evidence for item in result.criteria)


def test_criterion_scores_respect_their_boundaries(assessor, reference):
    result = assessor.assess(reference, "pagination off by one")

    for criterion in result.criteria:
        assert 0 <= criterion.awarded_points <= criterion.maximum_points