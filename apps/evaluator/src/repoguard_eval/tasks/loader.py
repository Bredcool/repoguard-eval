"""Load benchmark task definitions from JSON files."""

import json
from pathlib import Path

from pydantic import ValidationError

from repoguard_eval.exceptions import TaskLoadError
from repoguard_eval.models import TaskDefinition


def load_task(path: str | Path) -> TaskDefinition:
    """Load and validate a task definition from a JSON file."""

    task_path = Path(path)

    if not task_path.exists():
        raise TaskLoadError(f"Task file not found: {task_path}")

    if not task_path.is_file():
        raise TaskLoadError(f"Task path is not a file: {task_path}")

    try:
        with task_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise TaskLoadError(
            f"Invalid JSON in {task_path}: {exc}"
        ) from exc
    except OSError as exc:
        raise TaskLoadError(
            f"Unable to read task file {task_path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise TaskLoadError("Task JSON root must be an object.")

    try:
        return TaskDefinition.model_validate(data)
    except ValidationError as exc:
        raise TaskLoadError(
            f"Task validation failed for {task_path}:\n{exc}"
        ) from exc