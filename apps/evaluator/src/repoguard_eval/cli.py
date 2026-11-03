"""Command-line interface for RepoGuard-Eval."""

from pathlib import Path

import typer

from repoguard_eval.config import get_settings
from repoguard_eval.experiments import create_experiment, save_experiment
from repoguard_eval.tasks import load_task

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


if __name__ == "__main__":
    app()