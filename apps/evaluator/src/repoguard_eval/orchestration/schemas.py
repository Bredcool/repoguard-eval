from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TaskRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    MODEL_FAILED = "model_failed"
    PATCH_REJECTED = "patch_rejected"
    EXECUTION_FAILED = "execution_failed"
    GRADING_FAILED = "grading_failed"
    INFRASTRUCTURE_FAILED = "infrastructure_failed"


class TaskRunResult(BaseModel):
    task_id: str
    status: TaskRunStatus = TaskRunStatus.PENDING
    error: str | None = None
    artifacts: dict[str, str] = Field(default_factory=dict)
    score: float | None = None


class ExperimentRunResult(BaseModel):
    experiment_id: UUID
    status: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    task_results: list[TaskRunResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    duration_seconds: float | None = Field(default=None, ge=0)