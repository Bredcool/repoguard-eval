"""Task validation utilities."""

from pathlib import Path

from repoguard_eval.models import TaskDefinition
from repoguard_eval.tasks.loader import load_task


def validate_task_file(path: str | Path) -> TaskDefinition:
    """Validate a task file and return its parsed definition."""

    return load_task(path)


def validate_task_data(data: dict) -> TaskDefinition:
    """Validate task data supplied as a dictionary."""

    return TaskDefinition.model_validate(data)