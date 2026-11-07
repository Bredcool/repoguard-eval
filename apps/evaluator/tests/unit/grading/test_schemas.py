"""Tests for grading schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from repoguard_eval.grading.enums import (
    ExecutionStatus,
    FailureCategory,
    ScoreDimension,
)
from repoguard_eval.grading.schemas import (
    CriterionScore,
    DimensionScore,
    EvaluationResult,
    ExecutionCheckEvidence,
    ExecutionEvidence,
    FailureClassification,
)


def test_execution_evidence_accepts_passed_tests():
    evidence = ExecutionCheckEvidence(
        name="functional",
        status=ExecutionStatus.PASSED,
        exit_code=0,
        total_tests=5,
        passed_tests=5,
    )

    assert evidence.status == ExecutionStatus.PASSED
    assert evidence.passed_tests == 5


def test_execution_evidence_rejects_invalid_test_counts():
    with pytest.raises(ValidationError):
        ExecutionCheckEvidence(
            name="functional",
            status=ExecutionStatus.PASSED,
            total_tests=2,
            passed_tests=3,
        )


def test_execution_evidence_rejects_failed_tests_when_passed():
    with pytest.raises(ValidationError):
        ExecutionCheckEvidence(
            name="functional",
            status=ExecutionStatus.PASSED,
            total_tests=2,
            passed_tests=1,
            failed_tests=1,
        )


def test_dimension_score_validates_criterion_totals():
    score = DimensionScore(
        dimension=ScoreDimension.ROOT_CAUSE,
        score=14,
        maximum_score=20,
        criteria=(
            CriterionScore(
                criterion_id="defect_identification",
                awarded_points=8,
                maximum_points=8,
                rationale="Correct defect identified.",
            ),
            CriterionScore(
                criterion_id="underlying_mechanism",
                awarded_points=6,
                maximum_points=12,
                rationale="Mechanism partially explained.",
            ),
        ),
    )

    assert score.score == 14


def test_dimension_score_rejects_inconsistent_criteria():
    with pytest.raises(ValidationError):
        DimensionScore(
            dimension=ScoreDimension.ROOT_CAUSE,
            score=15,
            maximum_score=20,
            criteria=(
                CriterionScore(
                    criterion_id="defect_identification",
                    awarded_points=8,
                    maximum_points=8,
                    rationale="Correct defect identified.",
                ),
            ),
        )


def test_evaluation_result_accepts_valid_result():
    dimensions = (
        DimensionScore(
            dimension=ScoreDimension.ROOT_CAUSE,
            score=20,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.TECHNICAL_CORRECTNESS,
            score=30,
            maximum_score=30,
        ),
        DimensionScore(
            dimension=ScoreDimension.EVIDENCE,
            score=20,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.REGRESSION,
            score=20,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.PATCH_SCOPE,
            score=10,
            maximum_score=10,
        ),
    )

    result = EvaluationResult(
        task_id="case-01",
        experiment_id=uuid4(),
        total_score=100,
        dimensions=dimensions,
        execution_evidence=ExecutionEvidence(),
    )

    assert result.total_score == 100
    assert len(result.dimensions) == 5


def test_evaluation_result_rejects_inconsistent_total():
    dimensions = (
        DimensionScore(
            dimension=ScoreDimension.ROOT_CAUSE,
            score=10,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.TECHNICAL_CORRECTNESS,
            score=30,
            maximum_score=30,
        ),
        DimensionScore(
            dimension=ScoreDimension.EVIDENCE,
            score=20,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.REGRESSION,
            score=20,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.PATCH_SCOPE,
            score=10,
            maximum_score=10,
        ),
    )

    with pytest.raises(ValidationError):
        EvaluationResult(
            task_id="case-01",
            experiment_id=uuid4(),
            total_score=100,
            dimensions=dimensions,
            execution_evidence=ExecutionEvidence(),
        )


def test_evaluation_result_rejects_duplicate_dimensions():
    dimensions = (
        DimensionScore(
            dimension=ScoreDimension.ROOT_CAUSE,
            score=10,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.ROOT_CAUSE,
            score=10,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.TECHNICAL_CORRECTNESS,
            score=30,
            maximum_score=30,
        ),
        DimensionScore(
            dimension=ScoreDimension.EVIDENCE,
            score=20,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.REGRESSION,
            score=20,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.PATCH_SCOPE,
            score=10,
            maximum_score=10,
        ),
    )

    with pytest.raises(ValidationError):
        EvaluationResult(
            task_id="case-01",
            experiment_id=uuid4(),
            total_score=100,
            dimensions=dimensions,
            execution_evidence=ExecutionEvidence(),
        )


def test_failure_classification_accepts_infrastructure_error():
    classification = FailureClassification(
        category=FailureCategory.INFRASTRUCTURE_ERROR,
        description="Docker execution environment unavailable.",
    )

    assert classification.category == FailureCategory.INFRASTRUCTURE_ERROR