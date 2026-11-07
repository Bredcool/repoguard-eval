"""Tests for weighted scoring integration."""

from uuid import uuid4

import pytest

from repoguard_eval.grading.enums import ScoreDimension
from repoguard_eval.grading.schemas import (
    DimensionScore,
    ExecutionEvidence,
)
from repoguard_eval.grading.scoring_engine import WeightedScoringEngine


@pytest.fixture
def engine():
    return WeightedScoringEngine()


@pytest.fixture
def dimensions():
    return (
        DimensionScore(
            dimension=ScoreDimension.ROOT_CAUSE,
            score=18,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.TECHNICAL_CORRECTNESS,
            score=25,
            maximum_score=30,
        ),
        DimensionScore(
            dimension=ScoreDimension.EVIDENCE,
            score=16,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.REGRESSION,
            score=17,
            maximum_score=20,
        ),
        DimensionScore(
            dimension=ScoreDimension.PATCH_SCOPE,
            score=9,
            maximum_score=10,
        ),
    )


def evaluate(engine, dimensions, **overrides):
    arguments = {
        "task_id": "task-001",
        "experiment_id": uuid4(),
        "dimensions": dimensions,
        "execution_evidence": ExecutionEvidence(),
    }
    arguments.update(overrides)
    return engine.evaluate(**arguments)


def test_evaluate_combines_all_dimension_scores(engine, dimensions):
    result = evaluate(engine, dimensions)

    assert result.total_score == 85
    assert result.maximum_score == 100
    assert len(result.dimensions) == 5


def test_evaluate_returns_dimensions_in_rubric_order(engine, dimensions):
    result = evaluate(engine, tuple(reversed(dimensions)))

    assert tuple(item.dimension for item in result.dimensions) == (
        ScoreDimension.ROOT_CAUSE,
        ScoreDimension.TECHNICAL_CORRECTNESS,
        ScoreDimension.EVIDENCE,
        ScoreDimension.REGRESSION,
        ScoreDimension.PATCH_SCOPE,
    )


def test_evaluate_rejects_missing_dimension(engine, dimensions):
    with pytest.raises(ValueError, match="Missing scoring dimensions"):
        evaluate(engine, dimensions[:-1])


def test_evaluate_rejects_duplicate_dimensions(engine, dimensions):
    duplicated = dimensions + (dimensions[0],)

    with pytest.raises(ValueError, match="Duplicate scoring dimension"):
        evaluate(engine, duplicated)


def test_evaluate_rejects_incorrect_dimension_maximum(engine, dimensions):
    invalid = list(dimensions)
    invalid[0] = DimensionScore(
        dimension=ScoreDimension.ROOT_CAUSE,
        score=18,
        maximum_score=25,
    )

    with pytest.raises(ValueError, match="maximum must be 20"):
        evaluate(engine, tuple(invalid))


def test_evaluate_rejects_score_above_dimension_maximum():
    with pytest.raises(ValueError, match="Dimension score exceeds its maximum"):
        DimensionScore(
            dimension=ScoreDimension.ROOT_CAUSE,
            score=21,
            maximum_score=20,
        )


def test_evaluate_preserves_task_and_experiment_metadata(engine, dimensions):
    experiment_id = uuid4()

    result = evaluate(
        engine,
        dimensions,
        task_id="task-custom",
        experiment_id=experiment_id,
    )

    assert result.task_id == "task-custom"
    assert result.experiment_id == experiment_id


def test_evaluate_preserves_execution_evidence(engine, dimensions):
    evidence = ExecutionEvidence()

    result = evaluate(
        engine,
        dimensions,
        execution_evidence=evidence,
    )

    assert result.execution_evidence == evidence


def test_evaluate_supports_zero_score(engine, dimensions):
    zero_dimensions = tuple(
        DimensionScore(
            dimension=item.dimension,
            score=0,
            maximum_score=item.maximum_score,
        )
        for item in dimensions
    )

    result = evaluate(engine, zero_dimensions)

    assert result.total_score == 0
    assert result.maximum_score == 100


def test_evaluate_supports_perfect_score(engine, dimensions):
    perfect_dimensions = tuple(
        DimensionScore(
            dimension=item.dimension,
            score=item.maximum_score,
            maximum_score=item.maximum_score,
        )
        for item in dimensions
    )

    result = evaluate(engine, perfect_dimensions)

    assert result.total_score == 100
    assert result.maximum_score == 100