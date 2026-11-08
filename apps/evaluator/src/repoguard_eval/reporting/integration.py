"""Integration between experiment orchestration and reporting."""

from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import UUID

from repoguard_eval.grading.schemas import EvaluationResult
from repoguard_eval.reporting.aggregator import ExperimentAggregator
from repoguard_eval.reporting.artifacts import ReportArtifactWriter
from repoguard_eval.reporting.raw_outputs import RawOutputStore
from repoguard_eval.reporting.schemas import (
    ExperimentReportMetadata,
    TaskReportResult,
)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}

    with path.open("r", encoding="utf-8") as source:
        return json.load(source)


def _value(data: dict[str, Any], key: str, default=None):
    value = data.get(key, default)

    if hasattr(value, "value"):
        return value.value

    return value


def _integer(value):
    if value is None:
        return None

    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return None


def build_task_reports(
    *,
    experiment_id: UUID,
    task_results,
    experiment_dir: Path,
    task_loader: Callable | None = None,
) -> tuple[TaskReportResult, ...]:
    reports = []

    raw_output_path = (
        experiment_dir / "raw" / "model_outputs.jsonl"
    )

    for result in task_results:
        task_dir = experiment_dir / "tasks" / result.task_id

        grading_data = _read_json(
            task_dir / "grading.json"
        )

        response_data = _read_json(
            task_dir / "response.json"
        )

        evaluation = (
            EvaluationResult.model_validate(grading_data)
            if grading_data
            else None
        )

        usage = response_data.get("usage") or {}

        language = None

        if task_loader is not None:
            try:
                task = task_loader(result.task_id)
                language = _value(
                    {"language": getattr(task, "language", None)},
                    "language",
                )
            except Exception:
                language = None

        artifact_refs = tuple(
            str(Path(path).resolve())
            for path in result.artifacts.values()
            if Path(path).is_file()
        )

        if raw_output_path.is_file():
            artifact_refs += (str(raw_output_path.resolve()),)

        reports.append(
            TaskReportResult(
                experiment_id=experiment_id,
                task_id=result.task_id,
                status=_value(
                    {"status": result.status},
                    "status",
                ),
                evaluation=evaluation,
                provider=response_data.get("provider"),
                model=response_data.get("model"),
                language=language,
                input_tokens=_integer(
                    usage.get("input_tokens")
                ),
                output_tokens=_integer(
                    usage.get("output_tokens")
                ),
                total_tokens=_integer(
                    usage.get("total_tokens")
                ),
                duration_seconds=result.duration_seconds,
                cost_usd=(
                    float(usage["cost_usd"])
                    if usage.get("cost_usd") is not None
                    else None
                ),
                artifact_refs=artifact_refs,
            )
        )

    return tuple(reports)


def generate_experiment_report(
    *,
    artifact_dir: Path,
    summary: ExperimentRunResult,
    benchmark_name: str,
    benchmark_version: str,
    model: str,
    provider: str,
    task_loader: Callable | None = None,
) -> dict[str, Path]:
    experiment_id = summary.experiment_id
    experiment_dir = Path(artifact_dir) / str(experiment_id)

    metadata_data = summary.metadata

    started_at = metadata_data.get("started_at")
    completed_at = metadata_data.get("completed_at")

    if isinstance(started_at, str):
        started_at = datetime.fromisoformat(started_at)

    if isinstance(completed_at, str):
        completed_at = datetime.fromisoformat(completed_at)

    metadata = ExperimentReportMetadata(
        experiment_id=experiment_id,
        benchmark_name=benchmark_name,
        benchmark_version=benchmark_version,
        model=model,
        provider=provider,
        task_ids=tuple(
            result.task_id
            for result in summary.task_results
        ),
        generated_at=datetime.now(timezone.utc),
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=metadata_data.get(
            "duration_seconds"
        ),
        configuration={
            "max_concurrency": metadata_data.get(
                "max_concurrency"
            ),
            "python_version": metadata_data.get(
                "python_version"
            ),
            "platform": metadata_data.get("platform"),
        },
    )

    task_reports = build_task_reports(
        experiment_id=experiment_id,
        task_results=summary.task_results,
        experiment_dir=experiment_dir,
        task_loader=task_loader,
    )

    aggregate = ExperimentAggregator().aggregate(
        experiment_id=experiment_id,
        task_results=task_reports,
    )

    paths = ReportArtifactWriter(
        Path(artifact_dir)
    ).write(
        metadata=metadata,
        aggregate=aggregate,
    )

    raw_path = (
        experiment_dir / "raw" / "model_outputs.jsonl"
    )

    if raw_path.is_file():
        paths["raw_outputs"] = raw_path

    return paths