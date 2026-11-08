"""Read-only access to persisted experiment artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID

from repoguard_eval.api.exceptions import (
    ArtifactAccessError,
    ArtifactNotFoundError,
    ArtifactReadError,
    ExperimentNotFoundError,
)


class ArtifactService:
    """Read persisted experiment data without executing repository code."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).expanduser().resolve()

    def _experiment_dir(self, experiment_id: UUID) -> Path:
        candidate = (self.root / str(experiment_id)).resolve()

        if not candidate.is_relative_to(self.root):
            raise ArtifactAccessError("Invalid experiment directory.")

        if not candidate.is_dir():
            raise ExperimentNotFoundError(
                f"Experiment '{experiment_id}' was not found."
            )

        return candidate

    def _read_json(self, path: Path, default: Any = None) -> Any:
        if not path.exists():
            return default

        try:
            resolved = path.resolve(strict=True)

            if not resolved.is_relative_to(self.root):
                raise ArtifactAccessError(
                    "Artifact path escapes experiment storage."
                )

            if not resolved.is_file():
                raise ArtifactNotFoundError("Artifact is not a file.")

            with resolved.open("r", encoding="utf-8") as source:
                return json.load(source)

        except (ArtifactAccessError, ArtifactNotFoundError):
            raise
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ArtifactReadError(
                f"Unable to read artifact: {path.name}"
            ) from exc

    def _read_text(self, path: Path) -> str | None:
        if not path.exists():
            return None

        try:
            resolved = path.resolve(strict=True)

            if not resolved.is_relative_to(self.root):
                raise ArtifactAccessError(
                    "Artifact path escapes experiment storage."
                )

            if not resolved.is_file():
                raise ArtifactNotFoundError("Artifact is not a file.")

            return resolved.read_text(encoding="utf-8")

        except (ArtifactAccessError, ArtifactNotFoundError):
            raise
        except (OSError, UnicodeDecodeError) as exc:
            raise ArtifactReadError(
                f"Unable to read artifact: {path.name}"
            ) from exc

    def _load_experiment(self, experiment_id: UUID) -> dict[str, Any]:
        definition_path = self.root / f"{experiment_id}.json"

        definition = self._read_json(definition_path, {})

        directory = self.root / str(experiment_id)

        if directory.exists():
            directory = self._experiment_dir(experiment_id)

            orchestration = self._read_json(
                directory / "metadata.json",
                {},
            )

            result = self._read_json(
                directory / "result.json",
                {},
            )
        else:
            orchestration = {}
            result = {}

        if not definition and not orchestration and not result:
            raise ExperimentNotFoundError(
                f"Experiment '{experiment_id}' was not found."
            )

        return {
            "experiment": self._summary(
                experiment_id,
                definition,
                orchestration,
                result,
            ),
            "definition": definition,
            "orchestration": orchestration,
            "result": result,
        }

    @staticmethod
    def _summary(
        experiment_id: UUID,
        definition: dict[str, Any],
        metadata: dict[str, Any],
        result: dict[str, Any],
    ) -> dict[str, Any]:
        custom_metadata = definition.get("metadata") or {}

        return {
            "experiment_id": str(experiment_id),
            "status": (
                result.get("status")
                or metadata.get("status")
                or definition.get("status")
            ),
            "model": (
                metadata.get("model")
                or custom_metadata.get("model")
            ),
            "provider": metadata.get("provider"),
            "benchmark": (
                metadata.get("benchmark")
                or custom_metadata.get("benchmark_name")
            ),
            "total_tasks": (
                result.get("total_tasks")
                or metadata.get("task_count")
            ),
            "completed_tasks": result.get("completed_tasks"),
            "failed_tasks": result.get("failed_tasks"),
            "metadata": metadata,
        }

    def list_experiments(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        benchmark: str | None = None,
    ) -> dict[str, Any]:
        experiments = {}

        if not self.root.exists():
            return {
                "items": [],
                "total": 0,
            }

        for path in self.root.iterdir():
            try:
                if path.is_dir():
                    experiment_id = UUID(path.name)
                    item = self._load_experiment(experiment_id)
                    experiments[str(experiment_id)] = item["experiment"]

                elif path.is_file() and path.suffix == ".json":
                    experiment_id = UUID(path.stem)

                    if str(experiment_id) not in experiments:
                        definition = self._read_json(path, {})
                        experiments[str(experiment_id)] = self._summary(
                            experiment_id,
                            definition,
                            {},
                            {},
                        )

            except ValueError:
                continue

        items = list(experiments.values())

        filters = {
            "status": status,
            "model": model,
            "provider": provider,
            "benchmark": benchmark,
        }

        for field, expected in filters.items():
            if expected is not None:
                items = [
                    item for item in items
                    if str(item.get(field) or "").lower()
                    == expected.lower()
                ]

        items.sort(
            key=lambda item: item["experiment_id"],
            reverse=True,
        )

        total = len(items)

        return {
            "items": items[offset:offset + limit],
            "total": total,
        }

    def get_experiment(self, experiment_id: UUID) -> dict[str, Any]:
        return self._load_experiment(experiment_id)

    def list_tasks(
        self,
        experiment_id: UUID,
        *,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
    ) -> dict[str, Any]:
        directory = self._experiment_dir(experiment_id)

        tasks = self._read_json(
            directory / "results" / "task_results.json",
            None,
        )

        if tasks is None:
            result = self._read_json(directory / "result.json", {})
            tasks = result.get("task_results", [])

        if not isinstance(tasks, list):
            raise ArtifactReadError("Task results must be a JSON array.")

        if status:
            tasks = [
                task for task in tasks
                if str(task.get("status", "")).lower()
                == status.lower()
            ]

        total = len(tasks)

        return {
            "items": tasks[offset:offset + limit],
            "total": total,
        }

    def get_report(self, experiment_id: UUID) -> dict[str, Any]:
        directory = self._experiment_dir(experiment_id)

        metadata = self._read_json(
            directory / "reports" / "metadata.json",
            {},
        )

        aggregate = self._read_json(
            directory / "results" / "aggregate.json",
            {},
        )

        markdown = self._read_text(
            directory / "reports" / "report.md"
        )

        if not metadata and not aggregate and markdown is None:
            raise ArtifactNotFoundError("Experiment report not found.")

        return {
            "experiment_id": str(experiment_id),
            "metadata": metadata,
            "aggregate": aggregate,
            "report_markdown": markdown,
        }

    def get_failures(self, experiment_id: UUID) -> dict[str, Any]:
        directory = self._experiment_dir(experiment_id)

        analysis = self._read_json(
            directory / "reports" / "failure_analysis.json",
            None,
        )

        if analysis is None:
            raise ArtifactNotFoundError(
                "Failure analysis artifact not found."
            )

        return {
            "experiment_id": str(experiment_id),
            "failure_analysis": analysis,
        }

    def compare_models(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        benchmark: str | None = None,
    ) -> dict[str, Any]:
        comparisons = []

        if not self.root.exists():
            return {"items": [], "total": 0}

        for path in self.root.iterdir():
            if not path.is_dir():
                continue

            try:
                experiment_id = UUID(path.name)
                aggregate = self._read_json(
                    path / "results" / "aggregate.json",
                    None,
                )
                metadata = self._read_json(
                    path / "reports" / "metadata.json",
                    {},
                )

                if not aggregate:
                    continue

                benchmark_name = (
                    metadata.get("benchmark_name")
                    or metadata.get("benchmark")
                )

                if (
                    benchmark
                    and str(benchmark_name or "").lower() != benchmark.lower()
                ):
                    continue

                comparisons.append({
                    "experiment_id": str(experiment_id),
                    "model": metadata.get("model"),
                    "provider": metadata.get("provider"),
                    "benchmark": benchmark_name,
                    "score": aggregate.get("score"),
                    "functional_pass_rate": aggregate.get(
                        "functional_pass_rate"
                    ),
                    "build_success_rate": aggregate.get(
                        "build_success_rate"
                    ),
                    "regression_pass_rate": aggregate.get(
                        "regression_pass_rate"
                    ),
                    "total_tasks": aggregate.get("total_tasks"),
                    "generated_at": aggregate.get("generated_at"),
                })

            except ValueError:
                continue

        comparisons.sort(
            key=lambda item: item["generated_at"] or "",
            reverse=True,
        )

        total = len(comparisons)

        return {
            "items": comparisons[offset:offset + limit],
            "total": total,
        }

    def read_artifact(self, artifact_id: str) -> Path:
        parts = Path(artifact_id).parts

        if len(parts) < 2:
            raise ArtifactAccessError(
                "Artifact ID must be '{experiment_id}/{relative_path}'."
            )

        try:
            experiment_id = UUID(parts[0])
        except ValueError as exc:
            raise ArtifactAccessError(
                "Invalid experiment ID in artifact path."
            ) from exc

        directory = self._experiment_dir(experiment_id)

        relative_path = Path(*parts[1:])

        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ArtifactAccessError("Invalid artifact path.")

        candidate = directory / relative_path

        try:
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError as exc:
            raise ArtifactNotFoundError("Artifact not found.") from exc

        if not resolved.is_relative_to(directory):
            raise ArtifactAccessError(
                "Artifact path escapes experiment directory."
            )

        if not resolved.is_file():
            raise ArtifactNotFoundError("Artifact is not a file.")

        return resolved