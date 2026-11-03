"""Tests for task validation utilities."""

import pytest
from pydantic import ValidationError

from repoguard_eval.tasks import (
    validate_task_data,
    validate_task_file,
)


def valid_task_data() -> dict:
    return {
        "id": "validator-task",
        "title": "Validator test",
        "difficulty": "easy",
        "repository": {},
        "requirements": {
            "description": "Validate task data.",
            "objectives": ["Check schema"],
        },
        "evaluation": {
            "evaluation_type": "code_analysis",
        },
    }


def test_validate_task_data() -> None:
    task = validate_task_data(valid_task_data())

    assert task.id == "validator-task"


def test_validate_invalid_task_data() -> None:
    with pytest.raises(ValidationError):
        validate_task_data({"id": "INVALID ID"})


def test_validate_task_file(tmp_path) -> None:
    import json

    task_file = tmp_path / "task.json"
    task_file.write_text(
        json.dumps(valid_task_data()),
        encoding="utf-8",
    )

    task = validate_task_file(task_file)

    assert task.id == "validator-task"