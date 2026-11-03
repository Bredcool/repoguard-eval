"""Pydantic models for benchmark tasks."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from repoguard_eval.models.enums import (
    EvaluationType,
    TaskDifficulty,
    TaskStatus,
)


class TaskMetadata(BaseModel):
    """Metadata describing a benchmark task."""

    model_config = ConfigDict(extra="forbid")

    author: str | None = None
    created_at: str | None = None
    tags: list[str] = Field(default_factory=list)


class RepositoryConfig(BaseModel):
    """Source repository configuration."""

    model_config = ConfigDict(extra="forbid")

    url: HttpUrl | None = None
    path: Path | None = None
    branch: str = "main"
    commit: str | None = None


class TaskRequirements(BaseModel):
    """Requirements and expected outcomes."""

    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1)
    objectives: list[str] = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)


class TaskEvaluation(BaseModel):
    """Evaluation configuration for a benchmark task."""

    model_config = ConfigDict(extra="forbid")

    evaluation_type: EvaluationType
    test_commands: list[str] = Field(default_factory=list)
    timeout_seconds: int = Field(default=300, gt=0)
    expected_files: list[str] = Field(default_factory=list)


class TaskDefinition(BaseModel):
    """Complete benchmark task definition."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9-]*$")
    title: str = Field(min_length=1)
    version: str = "1.0.0"

    difficulty: TaskDifficulty
    status: TaskStatus = TaskStatus.DRAFT

    repository: RepositoryConfig
    requirements: TaskRequirements
    evaluation: TaskEvaluation

    metadata: TaskMetadata = Field(default_factory=TaskMetadata)