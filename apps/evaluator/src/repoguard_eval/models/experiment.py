"""Pydantic models for evaluation experiments."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from repoguard_eval.models.enums import TaskStatus


class ExperimentStatus(str):
    """Experiment lifecycle status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExperimentDefinition(BaseModel):
    """Metadata describing an evaluation experiment."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    id: UUID = Field(default_factory=uuid4)
    task_id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9-]*$")
    name: str = Field(min_length=1)
    status: str = ExperimentStatus.PENDING
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)