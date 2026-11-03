
"""Tests for task loading."""

import json
from pathlib import Path

import pytest

from repoguard_eval.tasks import TaskLoadError, load_task


def test_load_valid_task(tmp_path) -> None:
    task_file = tmp_path / "task.json"
    task_file.write_text(
        json.dumps({
            "id": "test-task",
            "title": "Test task",
            "difficulty": "easy",
            "repository": {},
            "requirements": {
                "description": "Test description",
                "objectives": ["Test objective"],
            },
            "evaluation": {
                "evaluation_type": "bug_fix",
            },
        }),
        encoding="utf-8",
    )

    task = load_task(task_file)

    assert task.id == "test-task"
    assert task.title == "Test task"


def test_missing_file() -> None:
    with pytest.raises(TaskLoadError, match="not found"):
        load_task("missing-task.json")


def test_directory_path_is_rejected(tmp_path) -> None:
    with pytest.raises(TaskLoadError, match="not a file"):
        load_task(tmp_path)


def test_unreadable_file(tmp_path, monkeypatch) -> None:
    task_file = tmp_path / "unreadable.json"
    task_file.write_text("{}", encoding="utf-8")

    def fail_open(self, *args, **kwargs):
        if self == task_file:
            raise PermissionError("access denied")

        return original_open(self, *args, **kwargs)

    original_open = Path.open
    monkeypatch.setattr(Path, "open", fail_open)

    with pytest.raises(TaskLoadError, match="Unable to read"):
        load_task(task_file)


def test_invalid_json(tmp_path) -> None:
    task_file = tmp_path / "invalid.json"
    task_file.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(TaskLoadError, match="Invalid JSON"):
        load_task(task_file)


def test_invalid_task_schema(tmp_path) -> None:
    task_file = tmp_path / "invalid-task.json"
    task_file.write_text(
        json.dumps({"id": "INVALID ID"}),
        encoding="utf-8",
    )

    with pytest.raises(TaskLoadError, match="validation failed"):
        load_task(task_file)


def test_non_object_json_root(tmp_path) -> None:
    task_file = tmp_path / "array.json"
    task_file.write_text('["not", "an", "object"]', encoding="utf-8")

    with pytest.raises(TaskLoadError, match="root must be an object"):
        load_task(task_file)
