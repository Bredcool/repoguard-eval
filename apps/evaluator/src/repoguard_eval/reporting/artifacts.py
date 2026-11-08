"""Persistence and consistency validation for experiment reports."""

import json
import os
from pathlib import Path
from typing import Any

from repoguard_eval.reporting.markdown import render_experiment_report
from repoguard_eval.reporting.schemas import (
    AggregateReport,
    ExperimentReportMetadata,
)


class ReportArtifactWriter:
    """Write structured experiment reports and validate their consistency."""

    def __init__(self, artifact_dir: Path):
        self.artifact_dir = Path(artifact_dir)

    @staticmethod
    def _write_json(path: Path, payload: Any) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)

        temporary = path.with_name(path.name + ".tmp")
        content = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

        with temporary.open("w", encoding="utf-8", newline="\n") as output:
            output.write(content)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())

        os.replace(temporary, path)
        return path

    @staticmethod
    def _write_text(path: Path, content: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)

        temporary = path.with_name(path.name + ".tmp")

        with temporary.open("w", encoding="utf-8", newline="\n") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())

        os.replace(temporary, path)
        return path

    def write(
        self,
        metadata: ExperimentReportMetadata,
        aggregate: AggregateReport,
    ) -> dict[str, Path]:
        if metadata.experiment_id != aggregate.experiment_id:
            raise ValueError("Experiment IDs do not match.")

        experiment_dir = self.artifact_dir / str(metadata.experiment_id)
        results_dir = experiment_dir / "results"
        reports_dir = experiment_dir / "reports"

        task_results = [
            result.model_dump(mode="json")
            for result in aggregate.task_results
        ]

        failure_analysis = {
            "experiment_id": str(aggregate.experiment_id),
            "failure_breakdown": [
                item.model_dump(mode="json")
                for item in aggregate.failure_breakdown
            ],
            "task_failures": [
                {
                    "task_id": result.task_id,
                    "failures": [
                        item.model_dump(mode="json")
                        for item in result.evaluation.failure_classifications
                    ],
                }
                for result in aggregate.task_results
                if result.evaluation is not None
                and result.evaluation.failure_classifications
            ],
        }

        paths = {
            "metadata": self._write_json(
                reports_dir / "metadata.json",
                metadata.model_dump(mode="json"),
            ),
            "task_results": self._write_json(
                results_dir / "task_results.json",
                task_results,
            ),
            "aggregate": self._write_json(
                results_dir / "aggregate.json",
                aggregate.model_dump(mode="json"),
            ),
            "report": self._write_text(
                reports_dir / "report.md",
                render_experiment_report(metadata, aggregate),
            ),
            "failure_analysis": self._write_json(
                reports_dir / "failure_analysis.json",
                failure_analysis,
            ),
        }

        self.validate(
            metadata=metadata,
            aggregate=aggregate,
            paths=paths,
        )

        return paths

    @staticmethod
    def validate(
        *,
        metadata: ExperimentReportMetadata,
        aggregate: AggregateReport,
        paths: dict[str, Path],
    ) -> None:
        if metadata.experiment_id != aggregate.experiment_id:
            raise ValueError("Metadata and aggregate IDs differ.")

        expected_task_ids = set(metadata.task_ids)
        actual_task_ids = {
            result.task_id for result in aggregate.task_results
        }

        if expected_task_ids != actual_task_ids:
            raise ValueError(
                "Metadata task IDs do not match aggregate task results."
            )

        if len(actual_task_ids) != len(aggregate.task_results):
            raise ValueError("Duplicate task results detected.")

        for name, path in paths.items():
            if not path.is_file():
                raise ValueError(f"Missing artifact '{name}': {path}")

            if path.stat().st_size == 0:
                raise ValueError(f"Artifact '{name}' is empty: {path}")

        with paths["task_results"].open(
            "r",
            encoding="utf-8",
        ) as source:
            persisted_tasks = json.load(source)

        if len(persisted_tasks) != aggregate.total_tasks:
            raise ValueError(
                "Persisted task result count does not match aggregate."
            )

        with paths["aggregate"].open(
            "r",
            encoding="utf-8",
        ) as source:
            persisted_aggregate = json.load(source)

        if persisted_aggregate["experiment_id"] != str(
            metadata.experiment_id
        ):
            raise ValueError("Persisted aggregate experiment ID is invalid.")