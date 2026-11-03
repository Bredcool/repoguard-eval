
"""Tests for the RepoGuard-Eval CLI."""

import runpy
from types import SimpleNamespace

import typer
from typer.testing import CliRunner

from repoguard_eval import cli

runner = CliRunner()


def test_root_help() -> None:
    result = runner.invoke(cli.app, ["--help"])

    assert result.exit_code == 0
    assert "task" in result.output
    assert "experiment" in result.output


def test_task_validate_success() -> None:
    result = runner.invoke(
        cli.app,
        [
            "task",
            "validate",
            "examples/tasks/example_task.json",
        ],
    )

    assert result.exit_code == 0
    assert "Task validation successful." in result.output
    assert "example-task" in result.output


def test_task_validate_missing_file() -> None:
    result = runner.invoke(
        cli.app,
        [
            "task",
            "validate",
            "examples/tasks/nonexistent.json",
        ],
    )

    assert result.exit_code == 1
    assert "Task validation failed:" in result.output


def test_experiment_create_success(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "get_settings",
        lambda: SimpleNamespace(experiments_dir=tmp_path),
    )

    result = runner.invoke(
        cli.app,
        [
            "experiment",
            "create",
            "--task-id",
            "example-task",
            "--name",
            "CLI Test Experiment",
        ],
    )

    assert result.exit_code == 0
    assert "Experiment created successfully." in result.output
    assert "example-task" in result.output
    assert "CLI Test Experiment" in result.output

    experiment_files = list(tmp_path.glob("*.json"))
    assert len(experiment_files) == 1


def test_experiment_create_with_default_name(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "get_settings",
        lambda: SimpleNamespace(experiments_dir=tmp_path),
    )

    result = runner.invoke(
        cli.app,
        [
            "experiment",
            "create",
            "--task-id",
            "example-task",
        ],
    )

    assert result.exit_code == 0
    assert "Experiment for example-task" in result.output


def test_experiment_create_missing_task_id() -> None:
    result = runner.invoke(
        cli.app,
        ["experiment", "create"],
    )

    assert result.exit_code != 0


def test_experiment_create_handles_save_failure(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "get_settings",
        lambda: SimpleNamespace(experiments_dir=tmp_path),
    )

    def fail_save(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(cli, "save_experiment", fail_save)

    result = runner.invoke(
        cli.app,
        [
            "experiment",
            "create",
            "--task-id",
            "example-task",
        ],
    )

    assert result.exit_code == 1
    assert "Experiment creation failed:" in result.output
    assert "disk full" in result.output


def test_cli_module_entry_point(monkeypatch) -> None:
    called = []

    def fake_call(self, *args, **kwargs):
        called.append(self)

    monkeypatch.setattr(typer.Typer, "__call__", fake_call)

    runpy.run_path(
        cli.__file__,
        run_name="__main__",
    )

    assert len(called) == 1


def test_package_module_entry_point(monkeypatch) -> None:
    called = []

    def fake_app():
        called.append(True)

    monkeypatch.setattr(cli, "app", fake_app)

    runpy.run_module(
        "repoguard_eval",
        run_name="__main__",
    )

    assert called == [True]
