"""Pydantic schemas for experiment reports and aggregate analysis."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from repoguard_eval.grading.schemas import EvaluationResult


class ReportModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class ExperimentReportMetadata(ReportModel):
    experiment_id: UUID
    benchmark_name: str = Field(min_length=1)
    benchmark_version: str = Field(min_length=1)

    model: str = Field(min_length=1)
    task_ids: tuple[str, ...] = Field(min_length=1)

    generated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = Field(default=None, ge=0)

    provider: str | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_timestamps(self):
        if (
            self.started_at is not None
            and self.completed_at is not None
            and self.completed_at < self.started_at
        ):
            raise ValueError("completed_at cannot precede started_at.")

        return self


class TaskReportResult(ReportModel):
    experiment_id: UUID
    task_id: str = Field(min_length=1)

    status: str = Field(min_length=1)
    evaluation: EvaluationResult | None = None

    provider: str | None = None
    model: str | None = None
    language: str | None = None

    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)

    duration_seconds: float | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)

    artifact_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_evaluation_identity(self):
        if self.evaluation is not None:
            if self.evaluation.task_id != self.task_id:
                raise ValueError(
                    "Evaluation task_id does not match report task_id."
                )

            if self.evaluation.experiment_id != self.experiment_id:
                raise ValueError(
                    "Evaluation experiment_id does not match report."
                )

        if (
            self.total_tokens is not None
            and self.input_tokens is not None
            and self.output_tokens is not None
            and self.total_tokens < self.input_tokens + self.output_tokens
        ):
            raise ValueError(
                "total_tokens cannot be less than input plus output tokens."
            )

        return self


class MetricSummary(ReportModel):
    count: int = Field(ge=0)
    average: float | None = None
    median: float | None = None
    minimum: float | None = None
    maximum: float | None = None


class RateSummary(ReportModel):
    numerator: int = Field(ge=0)
    denominator: int = Field(ge=0)
    rate: float | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def validate_rate(self):
        if self.numerator > self.denominator:
            raise ValueError("Numerator cannot exceed denominator.")

        if self.denominator == 0 and self.rate is not None:
            raise ValueError("Rate must be None when denominator is zero.")

        if self.denominator > 0:
            expected = self.numerator / self.denominator

            if self.rate is None or abs(self.rate - expected) > 1e-9:
                raise ValueError("Rate does not match numerator/denominator.")

        return self


class CategorySummary(ReportModel):
    category: str
    count: int = Field(ge=0)


class AggregateReport(ReportModel):
    experiment_id: UUID
    generated_at: datetime

    total_tasks: int = Field(ge=0)
    completed_tasks: int = Field(ge=0)
    failed_tasks: int = Field(ge=0)

    score: MetricSummary
    functional_pass_rate: RateSummary
    build_success_rate: RateSummary
    regression_pass_rate: RateSummary

    total_duration_seconds: float | None = Field(default=None, ge=0)
    average_duration_seconds: float | None = Field(default=None, ge=0)
    total_cost_usd: float | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)

    language_breakdown: tuple[CategorySummary, ...] = ()
    failure_breakdown: tuple[CategorySummary, ...] = ()
    model_breakdown: tuple[CategorySummary, ...] = ()

    task_results: tuple[TaskReportResult, ...] = ()

    @model_validator(mode="after")
    def validate_aggregate(self):
        if self.completed_tasks + self.failed_tasks > self.total_tasks:
            raise ValueError(
                "Completed and failed tasks cannot exceed total_tasks."
            )

        for result in self.task_results:
            if result.experiment_id != self.experiment_id:
                raise ValueError(
                    "Task result belongs to another experiment."
                )

        if self.task_results and len(self.task_results) != self.total_tasks:
            raise ValueError(
                "task_results count must equal total_tasks."
            )

        return self