"""Response schemas for the read-only dashboard API."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class HealthResponse(APIModel):
    status: str = "ok"
    service: str = "repoguard-eval"


class PaginationResponse(APIModel):
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


class ExperimentSummary(APIModel):
    experiment_id: str
    status: str | None = None
    model: str | None = None
    provider: str | None = None
    benchmark: str | None = None
    total_tasks: int | None = None
    completed_tasks: int | None = None
    failed_tasks: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExperimentListResponse(APIModel):
    items: list[ExperimentSummary]
    pagination: PaginationResponse


class ExperimentDetailResponse(APIModel):
    experiment: ExperimentSummary
    definition: dict[str, Any] = Field(default_factory=dict)
    orchestration: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)


class TaskListResponse(APIModel):
    experiment_id: str
    items: list[dict[str, Any]]
    pagination: PaginationResponse


class ReportResponse(APIModel):
    experiment_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    aggregate: dict[str, Any] = Field(default_factory=dict)
    report_markdown: str | None = None


class FailureResponse(APIModel):
    experiment_id: str
    failure_analysis: dict[str, Any] = Field(default_factory=dict)


class ModelComparisonResponse(APIModel):
    items: list[dict[str, Any]]
    pagination: PaginationResponse


class ErrorResponse(APIModel):
    error: str
    detail: str