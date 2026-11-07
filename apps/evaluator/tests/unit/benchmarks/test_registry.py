import json

import pytest

from repoguard_eval.benchmarks.registry import BenchmarkRegistry
from repoguard_eval.exceptions import TaskLoadError


def create_registry(root, tasks=None):
    root.mkdir(parents=True, exist_ok=True)
    (root / "manifest.json").write_text(
        json.dumps({
            "name": "Test Suite",
            "version": "1.0.0",
            "description": "Test benchmark registry",
            "tasks": tasks if tasks is not None else [{
                "id": "rg-test-001",
                "pack": "go/test",
                "language": "go",
                "category": "testing",
                "difficulty": "medium",
                "version": "1.0.0",
                "status": "development",
                "validation": {
                    "reference": "passed",
                    "baseline": "failed_as_expected",
                    "test_count": 3,
                },
            }],
        }),
        encoding="utf-8",
    )
    return BenchmarkRegistry(root)


def test_load_manifest_and_get_task(tmp_path):
    registry = create_registry(tmp_path / "benchmarks")

    entry = registry.get("rg-test-001")

    assert entry.id == "rg-test-001"
    assert entry.language == "go"
    assert entry.validation.test_count == 3


def test_get_unknown_task_raises_error(tmp_path):
    registry = create_registry(tmp_path / "benchmarks")

    with pytest.raises(TaskLoadError, match="not found"):
        registry.get("rg-missing")


def test_duplicate_task_ids_are_rejected(tmp_path):
    task = {
        "id": "rg-test-001",
        "pack": "go/test",
        "language": "go",
        "category": "testing",
        "difficulty": "medium",
        "version": "1.0.0",
        "status": "development",
    }

    registry = create_registry(
        tmp_path / "benchmarks",
        tasks=[task, task],
    )

    with pytest.raises(TaskLoadError, match="Duplicate"):
        registry.load()


def test_pack_path_traversal_is_rejected(tmp_path):
    task = {
        "id": "rg-test-001",
        "pack": "../outside",
        "language": "go",
        "category": "testing",
        "difficulty": "medium",
        "version": "1.0.0",
        "status": "development",
    }

    registry = create_registry(tmp_path / "benchmarks", [task])

    with pytest.raises(TaskLoadError, match="Invalid benchmark pack path"):
        registry.load()


def test_task_directory_resolves_existing_task(tmp_path):
    root = tmp_path / "benchmarks"
    task_dir = root / "packs" / "go" / "test" / "rg-test-001"
    task_dir.mkdir(parents=True)

    registry = create_registry(root)
    entry = registry.get("rg-test-001")

    assert registry.task_directory(entry) == task_dir.resolve()


def test_task_directory_rejects_missing_directory(tmp_path):
    registry = create_registry(tmp_path / "benchmarks")
    entry = registry.get("rg-test-001")

    with pytest.raises(TaskLoadError, match="Invalid benchmark task directory"):
        registry.task_directory(entry)
