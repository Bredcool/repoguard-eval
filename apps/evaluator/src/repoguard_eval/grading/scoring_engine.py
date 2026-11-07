
"""Weighted aggregation of deterministic grading dimensions."""

from collections.abc import Sequence
from uuid import UUID

from repoguard_eval.grading.rubric import RUBRIC_WEIGHTS, validate_rubric
from repoguard_eval.grading.schemas import (
    DimensionScore,
    EvaluationResult,
    ExecutionEvidence,
    FailureClassification,
)
from repoguard_eval.grading.scoring_boundaries import (
    validate_execution_boundaries,
)


class WeightedScoringEngine:
    """Validates and aggregates assessor results into one evaluation."""

    def __init__(self) -> None:
        validate_rubric()

    def evaluate(
        self,
        *,
        task_id: str,
        experiment_id: UUID,
        dimensions: Sequence[DimensionScore],
        execution_evidence: ExecutionEvidence,
        failure_classifications: Sequence[FailureClassification] = (),
    ) -> EvaluationResult:
        """Build a complete result from all required scoring dimensions."""

        if not task_id.strip():
            raise ValueError("task_id cannot be empty.")

        validate_execution_boundaries(execution_evidence)

        dimension_map: dict = {}

        for dimension in dimensions:
            dimension_id = dimension.dimension

            if dimension_id in dimension_map:
                raise ValueError(
                    f"Duplicate scoring dimension: {dimension_id.value}."
                )

            dimension_map[dimension_id] = dimension

        expected_dimensions = set(RUBRIC_WEIGHTS)
        received_dimensions = set(dimension_map)

        missing = expected_dimensions - received_dimensions
        unexpected = received_dimensions - expected_dimensions

        if missing:
            names = sorted(item.value for item in missing)
            raise ValueError(f"Missing scoring dimensions: {names}.")

        if unexpected:
            names = sorted(item.value for item in unexpected)
            raise ValueError(f"Unexpected scoring dimensions: {names}.")

        ordered_dimensions = tuple(
            dimension_map[dimension_id]
            for dimension_id in RUBRIC_WEIGHTS
        )

        for dimension in ordered_dimensions:
            expected_maximum = RUBRIC_WEIGHTS[dimension.dimension]

            if dimension.maximum_score != expected_maximum:
                raise ValueError(
                    f"{dimension.dimension.value} maximum must be "
                    f"{expected_maximum}, got {dimension.maximum_score}."
                )

        total_score = sum(
            dimension.score for dimension in ordered_dimensions
        )

        return EvaluationResult(
            task_id=task_id,
            experiment_id=experiment_id,
            total_score=total_score,
            maximum_score=100,
            dimensions=ordered_dimensions,
            execution_evidence=execution_evidence,
            failure_classifications=tuple(failure_classifications),
        )
