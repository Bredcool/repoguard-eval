"""Tests for centralized application exceptions."""

from repoguard_eval.exceptions import (
    ConfigurationError,
    ExperimentError,
    RepoGuardError,
    TaskLoadError,
)


def test_task_load_error_inherits_base_exception() -> None:
    error = TaskLoadError("Task not found")

    assert isinstance(error, RepoGuardError)
    assert str(error) == "Task not found"


def test_experiment_error_inherits_base_exception() -> None:
    error = ExperimentError("Experiment failed")

    assert isinstance(error, RepoGuardError)
    assert str(error) == "Experiment failed"


def test_configuration_error_inherits_base_exception() -> None:
    error = ConfigurationError("Invalid configuration")

    assert isinstance(error, RepoGuardError)


def test_base_exception_can_catch_specific_errors() -> None:
    try:
        raise TaskLoadError("Invalid task")
    except RepoGuardError as exc:
        assert str(exc) == "Invalid task"
    else:
        raise AssertionError("RepoGuardError did not catch TaskLoadError")