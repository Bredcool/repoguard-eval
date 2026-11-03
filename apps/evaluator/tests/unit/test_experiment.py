"""Tests for experiment models."""

from datetime import timezone

from repoguard_eval.models import ExperimentDefinition, ExperimentStatus


def test_experiment_creation() -> None:
    experiment = ExperimentDefinition(
        task_id="example-task",
        name="Baseline evaluation",
    )

    assert experiment.task_id == "example-task"
    assert experiment.name == "Baseline evaluation"
    assert experiment.status == ExperimentStatus.PENDING


def test_experiment_default_id_is_unique() -> None:
    first = ExperimentDefinition(
        task_id="example-task",
        name="Experiment one",
    )
    second = ExperimentDefinition(
        task_id="example-task",
        name="Experiment two",
    )

    assert first.id != second.id


def test_experiment_timestamp_is_timezone_aware() -> None:
    experiment = ExperimentDefinition(
        task_id="example-task",
        name="Timestamp test",
    )

    assert experiment.created_at.tzinfo is not None
    assert experiment.created_at.tzinfo == timezone.utc


def test_experiment_metadata() -> None:
    experiment = ExperimentDefinition(
        task_id="example-task",
        name="Metadata test",
        metadata={"model": "baseline", "temperature": 0.0},
    )

    assert experiment.metadata["model"] == "baseline"
    assert experiment.metadata["temperature"] == 0.0


def test_experiment_serialization() -> None:
    experiment = ExperimentDefinition(
        task_id="example-task",
        name="Serialization test",
    )

    serialized = experiment.model_dump(mode="json")

    assert serialized["task_id"] == "example-task"
    assert serialized["status"] == "pending"
    assert isinstance(serialized["id"], str)