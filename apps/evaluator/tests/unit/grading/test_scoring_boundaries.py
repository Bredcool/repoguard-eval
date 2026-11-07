
from uuid import uuid4

import pytest

from repoguard_eval.grading.enums import (
    ExecutionStatus,
    ScoreDimension,
)
from repoguard_eval.grading.schemas import (
    DimensionScore,
    ExecutionCheckEvidence,
    ExecutionEvidence,
)
from repoguard_eval.grading.scoring_boundaries import (
    InfrastructureEvaluationError,
    validate_execution_boundaries,
)
from repoguard_eval.grading.scoring_engine import WeightedScoringEngine


def make_check(status: ExecutionStatus) -> ExecutionCheckEvidence:
    return ExecutionCheckEvidence(
        name="test command",
        status=status,
    )


def make_dimensions():
    weights = {
        ScoreDimension.ROOT_CAUSE: 20,
        ScoreDimension.TECHNICAL_CORRECTNESS: 30,
        ScoreDimension.EVIDENCE: 20,
        ScoreDimension.REGRESSION: 20,
        ScoreDimension.PATCH_SCOPE: 10,
    }

    return tuple(
        DimensionScore(
            dimension=dimension,
            score=0,
            maximum_score=maximum,
        )
        for dimension, maximum in weights.items()
    )


@pytest.mark.parametrize(
    "status",
    [ExecutionStatus.SKIPPED, ExecutionStatus.BLOCKED],
)
def test_skipped_and_blocked_checks_are_neutral(status):
    evidence = ExecutionEvidence(
        functional=make_check(status),
    )

    validate_execution_boundaries(evidence)


def test_failed_check_does_not_trigger_infrastructure_abort():
    evidence = ExecutionEvidence(
        functional=make_check(ExecutionStatus.FAILED),
    )

    validate_execution_boundaries(evidence)


def test_error_check_aborts_scoring():
    evidence = ExecutionEvidence(
        build=make_check(ExecutionStatus.ERROR),
    )

    with pytest.raises(
        InfrastructureEvaluationError,
        match="Scoring aborted",
    ):
        validate_execution_boundaries(evidence)


def test_language_check_error_aborts_scoring():
    evidence = ExecutionEvidence(
        language_checks=(
            make_check(ExecutionStatus.PASSED),
            make_check(ExecutionStatus.ERROR),
        ),
    )

    with pytest.raises(InfrastructureEvaluationError):
        validate_execution_boundaries(evidence)


def test_multiple_errors_are_reported():
    evidence = ExecutionEvidence(
        build=make_check(ExecutionStatus.ERROR),
        hidden=make_check(ExecutionStatus.ERROR),
    )

    with pytest.raises(InfrastructureEvaluationError) as exc_info:
        validate_execution_boundaries(evidence)

    assert "build" in str(exc_info.value)
    assert "hidden" in str(exc_info.value)


def test_scoring_engine_aborts_before_creating_result():
    engine = WeightedScoringEngine()
    evidence = ExecutionEvidence(
        build=make_check(ExecutionStatus.ERROR),
    )

    with pytest.raises(InfrastructureEvaluationError):
        engine.evaluate(
            task_id="boundary-test",
            experiment_id=uuid4(),
            dimensions=make_dimensions(),
            execution_evidence=evidence,
        )


def test_scoring_engine_accepts_neutral_skipped_checks():
    engine = WeightedScoringEngine()
    evidence = ExecutionEvidence(
        functional=make_check(ExecutionStatus.SKIPPED),
        hidden=make_check(ExecutionStatus.BLOCKED),
    )

    result = engine.evaluate(
        task_id="boundary-test",
        experiment_id=uuid4(),
        dimensions=make_dimensions(),
        execution_evidence=evidence,
    )

    assert result.total_score == 0
    assert result.maximum_score == 100
