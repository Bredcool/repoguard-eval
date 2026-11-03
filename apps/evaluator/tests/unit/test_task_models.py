"""Tests for benchmark task models."""

import pytest
from pydantic import ValidationError

from repoguard_eval.models import (
    EvaluationType,
    TaskDefinition,
    TaskDifficulty,
    TaskStatus,
)


@pytest.fixture
def valid_task_data() -> dict:
    return {
        "id": "example-task",
        "title": "Fix authentication bug",
        "version": "1.0.0",
        "difficulty": "medium",
        "status": "ready",
        "repository": {
            "url": "https://github.com/example/repository",
            "branch": "main",
            "commit": "abc123",
        },
        "requirements": {
            "description": "Fix the authentication validation bug.",
            "objectives": [
                "Identify the root cause",
                "Implement a minimal fix",
                "Add regression tests",
            ],
            "constraints": [
                "Preserve existing API behavior",
            ],
        },
        "evaluation": {
            "evaluation_type": "bug_fix",
            "test_commands": ["go test ./..."],
            "timeout_seconds": 300,
            "expected_files": ["internal/auth/auth.go"],
        },
        "metadata": {
            "author": "RepoGuard-Eval",
            "tags": ["go", "authentication"],
        },
    }


def test_valid_task_creation(valid_task_data: dict) -> None:
    task = TaskDefinition.model_validate(valid_task_data)

    assert task.id == "example-task"
    assert task.difficulty == TaskDifficulty.MEDIUM
    assert task.status == TaskStatus.READY
    assert task.evaluation.evaluation_type == EvaluationType.BUG_FIX


def test_task_default_values(valid_task_data: dict) -> None:
    valid_task_data.pop("status")
    valid_task_data.pop("metadata")

    task = TaskDefinition.model_validate(valid_task_data)

    assert task.status == TaskStatus.DRAFT
    assert task.metadata.tags == []


def test_invalid_task_id(valid_task_data: dict) -> None:
    valid_task_data["id"] = "Invalid Task ID"

    with pytest.raises(ValidationError):
        TaskDefinition.model_validate(valid_task_data)


def test_missing_required_field(valid_task_data: dict) -> None:
    del valid_task_data["title"]

    with pytest.raises(ValidationError):
        TaskDefinition.model_validate(valid_task_data)


def test_invalid_difficulty(valid_task_data: dict) -> None:
    valid_task_data["difficulty"] = "extreme"

    with pytest.raises(ValidationError):
        TaskDefinition.model_validate(valid_task_data)


def test_empty_objectives(valid_task_data: dict) -> None:
    valid_task_data["requirements"]["objectives"] = []

    with pytest.raises(ValidationError):
        TaskDefinition.model_validate(valid_task_data)


def test_invalid_timeout(valid_task_data: dict) -> None:
    valid_task_data["evaluation"]["timeout_seconds"] = 0

    with pytest.raises(ValidationError):
        TaskDefinition.model_validate(valid_task_data)


def test_unknown_field_rejected(valid_task_data: dict) -> None:
    valid_task_data["unknown_field"] = "unexpected"

    with pytest.raises(ValidationError):
        TaskDefinition.model_validate(valid_task_data)


def test_task_serialization(valid_task_data: dict) -> None:
    task = TaskDefinition.model_validate(valid_task_data)

    serialized = task.model_dump(mode="json")

    assert serialized["id"] == "example-task"
    assert serialized["difficulty"] == "medium"
    assert serialized["evaluation"]["evaluation_type"] == "bug_fix"


def test_task_json_schema() -> None:
    schema = TaskDefinition.model_json_schema()

    assert schema["title"] == "TaskDefinition"
    assert "repository" in schema["properties"]
    assert "requirements" in schema["properties"]
    assert "evaluation" in schema["properties"]