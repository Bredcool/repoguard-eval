"""Experiment creation and metadata persistence."""

import json
from pathlib import Path
from uuid import UUID

from repoguard_eval.exceptions import ExperimentError
from repoguard_eval.models import ExperimentDefinition


def create_experiment(
    task_id: str,
    name: str,
    metadata: dict | None = None,
) -> ExperimentDefinition:
    """Create a new experiment definition."""

    return ExperimentDefinition(
        task_id=task_id,
        name=name,
        metadata=metadata or {},
    )


def save_experiment(
    experiment: ExperimentDefinition,
    directory: str | Path,
) -> Path:
    """Save experiment metadata as a JSON file."""

    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{experiment.id}.json"

    try:
        output_path.write_text(
            experiment.model_dump_json(indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise ExperimentError(
            f"Unable to save experiment: {exc}"
        ) from exc

    return output_path


def load_experiment(path: str | Path) -> ExperimentDefinition:
    """Load experiment metadata from a JSON file."""

    experiment_path = Path(path)

    if not experiment_path.is_file():
        raise ExperimentError(
            f"Experiment file not found: {experiment_path}"
        )

    try:
        data = json.loads(experiment_path.read_text(encoding="utf-8"))
        return ExperimentDefinition.model_validate(data)
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        raise ExperimentError(
            f"Unable to load experiment: {exc}"
        ) from exc


def get_experiment(
    experiment_id: UUID,
    directory: str | Path,
) -> ExperimentDefinition:
    """Retrieve an experiment by its UUID."""

    path = Path(directory) / f"{experiment_id}.json"
    return load_experiment(path)