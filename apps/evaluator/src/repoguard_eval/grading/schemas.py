"""Structured schemas for deterministic grading."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from repoguard_eval.grading.enums import (
    ExecutionStatus,
    FailureCategory,
    ScoreDimension,
)


class GradingModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ExecutionCheckEvidence(GradingModel):
    """Observed result from one build or test execution."""

    name: str = Field(min_length=1)
    status: ExecutionStatus
    command: str | None = None
    exit_code: int | None = None
    total_tests: int = Field(default=0, ge=0)
    passed_tests: int = Field(default=0, ge=0)
    failed_tests: int = Field(default=0, ge=0)
    skipped_tests: int = Field(default=0, ge=0)
    duration_seconds: float = Field(default=0.0, ge=0)
    stdout: str = ""
    stderr: str = ""
    evidence_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_test_counts(self):
        counts = (
            self.passed_tests
            + self.failed_tests
            + self.skipped_tests
        )

        if counts > self.total_tests:
            raise ValueError(
                "Test result counts cannot exceed total_tests."
            )

        if self.status == ExecutionStatus.PASSED and self.failed_tests:
            raise ValueError(
                "A passed execution cannot contain failed tests."
            )

        return self


class ExecutionEvidence(GradingModel):
    """Execution evidence collected during patch evaluation."""

    build: ExecutionCheckEvidence | None = None
    functional: ExecutionCheckEvidence | None = None
    hidden: ExecutionCheckEvidence | None = None
    regression: ExecutionCheckEvidence | None = None
    language_checks: tuple[ExecutionCheckEvidence, ...] = ()


class CriterionScore(GradingModel):
    """Score awarded for one independently assessable criterion."""

    criterion_id: str = Field(min_length=1)
    awarded_points: float = Field(ge=0)
    maximum_points: float = Field(gt=0)
    rationale: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_awarded_points(self):
        if self.awarded_points > self.maximum_points:
            raise ValueError(
                "Awarded points cannot exceed maximum points."
            )
        return self


class DimensionScore(GradingModel):
    """Aggregated score for one rubric dimension."""

    dimension: ScoreDimension
    score: float = Field(ge=0)
    maximum_score: float = Field(gt=0)
    criteria: tuple[CriterionScore, ...] = ()

    @model_validator(mode="after")
    def validate_dimension_score(self):
        if self.score > self.maximum_score:
            raise ValueError("Dimension score exceeds its maximum.")

        if self.criteria:
            criteria_score = sum(
                item.awarded_points for item in self.criteria
            )
            criteria_maximum = sum(
                item.maximum_points for item in self.criteria
            )

            if criteria_score != self.score:
                raise ValueError(
                    "Dimension score must equal the sum of criterion scores."
                )

            if criteria_maximum != self.maximum_score:
                raise ValueError(
                    "Criterion maximums must equal dimension maximum."
                )

        return self


class FailureClassification(GradingModel):
    category: FailureCategory
    description: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = ()


class EvaluationResult(GradingModel):
    """Complete structured result produced by the grading engine."""

    task_id: str = Field(min_length=1)
    experiment_id: UUID
    total_score: float = Field(ge=0, le=100)
    maximum_score: float = Field(default=100, gt=0, le=100)
    dimensions: tuple[DimensionScore, ...]
    execution_evidence: ExecutionEvidence
    failure_classifications: tuple[FailureClassification, ...] = ()

    @model_validator(mode="after")
    def validate_result(self):
        dimension_ids = [
            item.dimension for item in self.dimensions
        ]

        if len(dimension_ids) != len(set(dimension_ids)):
            raise ValueError("Duplicate scoring dimensions are not allowed.")

        calculated_score = sum(
            item.score for item in self.dimensions
        )
        calculated_maximum = sum(
            item.maximum_score for item in self.dimensions
        )

        if calculated_score != self.total_score:
            raise ValueError(
                "Total score must equal the sum of dimension scores."
            )

        if calculated_maximum != self.maximum_score:
            raise ValueError(
                "Dimension maximums must equal maximum_score."
            )

        return self