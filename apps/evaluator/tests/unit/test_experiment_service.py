
"""Tests for experiment management service."""

import json
from pathlib import Path

import pytest

from repoguard_eval.experiments import (
    ExperimentError,
    create_experiment,
    get_experiment,
    load_experiment,
    save_experiment,
)


def test_create_experiment() -> None:
    experiment = create_experiment(
        task_id="example-task",
        name="Baseline evaluation",
    )

    assert experiment.task_id == "example-task"
    assert experiment.name == "Baseline evaluation"
    assert experiment.status == "pending"


def test_create_experiment_with_metadata() -> None:
    experiment = create_experiment(
        task_id="example-task",
        name="Model evaluation",
        metadata={"model": "gpt", "temperature": 0.2},
    )

    assert experiment.metadata["model"] == "gpt"
    assert experiment.metadata["temperature"] == 0.2


def test_save_experiment(tmp_path) -> None:
    experiment = create_experiment(
        task_id="example-task",
        name="Save test",
    )

    path = save_experiment(experiment, tmp_path)

    assert path.exists()
    assert path.name == f"{experiment.id}.json"


def test_save_experiment_handles_write_failure(
    tmp_path,
    monkeypatch,
) -> None:
    experiment = create_experiment(
        task_id="example-task",
        name="Write failure test",
    )

    def fail_write(self, *args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", fail_write)

    with pytest.raises(ExperimentError, match="Unable to save"):
        save_experiment(experiment, tmp_path)


def test_load_experiment(tmp_path) -> None:
    experiment = create_experiment(
        task_id="example-task",
        name="Load test",
    )
    path = save_experiment(experiment, tmp_path)

    loaded = load_experiment(path)

    assert loaded.id == experiment.id
    assert loaded.task_id == experiment.task_id
    assert loaded.name == experiment.name


def test_get_experiment(tmp_path) -> None:
    experiment = create_experiment(
        task_id="example-task",
        name="Retrieve test",
    )
    save_experiment(experiment, tmp_path)

    loaded = get_experiment(experiment.id, tmp_path)

    assert loaded.id == experiment.id


def test_load_missing_experiment() -> None:
    with pytest.raises(ExperimentError, match="not found"):
        load_experiment("missing-experiment.json")


def test_load_invalid_json(tmp_path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ExperimentError, match="Unable to load"):
        load_experiment(path)


def test_load_invalid_schema(tmp_path) -> None:
    path = tmp_path / "invalid-schema.json"
    path.write_text(
        json.dumps({"task_id": "INVALID ID"}),
        encoding="utf-8",
    )

    with pytest.raises(ExperimentError, match="Unable to load"):
        load_experiment(path)
