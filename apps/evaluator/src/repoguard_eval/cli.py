"""Command-line interface for RepoGuard-Eval."""

from pathlib import Path

import typer

from repoguard_eval.config import get_settings
from repoguard_eval.experiments import create_experiment, save_experiment
from repoguard_eval.tasks import load_task

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from repoguard_eval.orchestration.bootstrap import build_orchestrator
from repoguard_eval.models.experiment import ExperimentStatus

app = typer.Typer(
    name="repoguard",
    help="RepoGuard-Eval evaluation framework.",
    no_args_is_help=True,
)

task_app = typer.Typer(
    help="Manage and validate evaluation tasks.",
    no_args_is_help=True,
)

experiment_app = typer.Typer(
    help="Manage evaluation experiments.",
    no_args_is_help=True,
)

app.add_typer(task_app, name="task")
app.add_typer(experiment_app, name="experiment")


@task_app.command("validate")
def validate_task(
    task_file: Path = typer.Argument(
        ...,
        help="Path to the task JSON file.",
        dir_okay=False,
    ),
) -> None:
    """Validate a task definition."""

    try:
        task = load_task(task_file)
    except Exception as exc:
        typer.echo(f"Task validation failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("Task validation successful.")
    typer.echo(f"Task ID: {task.id}")
    typer.echo(f"Title: {task.title}")
    typer.echo(f"Difficulty: {task.difficulty.value}")
    typer.echo(f"Status: {task.status.value}")


@experiment_app.command("create")
def create_experiment_command(
    task_id: str = typer.Option(
        ...,
        "--task-id",
        help="ID of the task associated with this experiment.",
    ),
    name: str | None = typer.Option(
        None,
        "--name",
        help="Experiment name.",
    ),
) -> None:
    """Create and save a new experiment."""

    experiment_name = name or f"Experiment for {task_id}"

    try:
        experiment = create_experiment(
            task_id=task_id,
            name=experiment_name,
        )

        settings = get_settings()
        save_experiment(
            experiment=experiment,
            directory=settings.experiments_dir,
        )

    except Exception as exc:
        typer.echo(f"Experiment creation failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    experiment_path = (
        settings.experiments_dir / f"{experiment.id}.json"
    )

    typer.echo("Experiment created successfully.")
    typer.echo(f"Experiment ID: {experiment.id}")
    typer.echo(f"Task ID: {experiment.task_id}")
    typer.echo(f"Name: {experiment.name}")
    typer.echo(f"Status: {experiment.status}")
    typer.echo(f"Saved to: {experiment_path}")


@experiment_app.command("run")
def run_experiment(
    task_ids: list[str] = typer.Option(
        ...,
        "--task-id",
        help="Task ID. Repeat this option to evaluate multiple tasks.",
    ),
    model: str = typer.Option(..., "--model"),
    benchmark_name: str = typer.Option("repoguard", "--benchmark-name"),
    benchmark_version: str = typer.Option(
        "1.0.0",
        "--benchmark-version",
    ),
    max_concurrency: int = typer.Option(1, "--max-concurrency", min=1),
) -> None:
    """Run an evaluation experiment."""

    if len(task_ids) != len(set(task_ids)):
        raise typer.BadParameter("Duplicate task IDs are not allowed.")

    settings = get_settings()
    experiment_id = uuid4()
    now = datetime.now(timezone.utc)

    definition = create_experiment(
        task_id=task_ids[0],
        name=f"{benchmark_name}-{experiment_id.hex[:8]}",
        metadata={
            "model": model,
            "benchmark_name": benchmark_name,
            "benchmark_version": benchmark_version,
            "task_count": len(task_ids),
            "max_concurrency": max_concurrency,
        },
    )

    definition = definition.model_copy(
        update={
            "id": experiment_id,
            "status": ExperimentStatus.RUNNING,
            "started_at": now,
        }
    )

    save_experiment(definition, settings.experiments_dir)

    try:
        orchestrator = build_orchestrator(
            model=model,
            artifact_dir=settings.experiments_dir,
            max_concurrency=max_concurrency,
        )

        result = asyncio.run(
            orchestrator.run(
                experiment_id=experiment_id,
                task_ids=task_ids,
                benchmark_name=benchmark_name,
                benchmark_version=benchmark_version,
            )
        )

        completed_at = datetime.now(timezone.utc)

        definition = definition.model_copy(
            update={
                "status": result.status,
                "completed_at": completed_at,
            }
        )

        save_experiment(definition, settings.experiments_dir)

        typer.echo(result.model_dump_json(indent=2))

        if result.failed_tasks:
            raise typer.Exit(code=1)

    except NotImplementedError as exc:
        definition = definition.model_copy(
            update={"status": ExperimentStatus.FAILED}
        )
        save_experiment(definition, settings.experiments_dir)
        typer.echo(f"Orchestrator configuration incomplete: {exc}", err=True)
        raise typer.Exit(code=2)

    except Exception as exc:
        definition = definition.model_copy(
            update={
                "status": ExperimentStatus.FAILED,
                "completed_at": datetime.now(timezone.utc),
            }
        )
        save_experiment(definition, settings.experiments_dir)
        typer.echo(f"Experiment failed: {exc}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()