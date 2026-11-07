
from __future__ import annotations

import asyncio
import json
import logging
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence
from uuid import UUID

from repoguard_eval.grading.schemas import (
    EvaluationResult,
    ExecutionEvidence,
)
from repoguard_eval.models.task import TaskDefinition
from repoguard_eval.providers.base import BaseProvider
from repoguard_eval.providers.schemas.response import ProviderRequest, ProviderResponse

from .schemas import (
    ExperimentRunResult,
    TaskRunResult,
    TaskRunStatus,
)

logger = logging.getLogger(__name__)


class Sandbox(Protocol):
    def apply_patch(self, patch: str) -> None:
        ...

    def execute(self, task: TaskDefinition) -> ExecutionEvidence:
        ...

    def cleanup(self) -> None:
        ...


class ExperimentOrchestrator:
    def __init__(
        self,
        *,
        provider: BaseProvider,
        task_loader: Callable[[str], TaskDefinition],
        request_builder: Callable[
            [TaskDefinition, UUID, str], ProviderRequest
        ],
        sandbox_factory: Callable[[TaskDefinition, UUID], Sandbox],
        grader: Callable[
            [TaskDefinition, UUID, ProviderResponse, ExecutionEvidence],
            EvaluationResult,
        ],
        artifact_dir: Path,
        model: str,
        max_concurrency: int = 1,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")

        if not model.strip():
            raise ValueError("Model ID cannot be empty")

        self.provider = provider
        self.task_loader = task_loader
        self.request_builder = request_builder
        self.sandbox_factory = sandbox_factory
        self.grader = grader
        self.artifact_dir = Path(artifact_dir)
        self.model = model
        self.max_concurrency = max_concurrency

    async def run(
        self,
        *,
        experiment_id: UUID,
        task_ids: Sequence[str],
        benchmark_name: str,
        benchmark_version: str,
    ) -> ExperimentRunResult:
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("Duplicate task IDs are not allowed")

        if not task_ids:
            raise ValueError("At least one task ID is required")

        root = self.artifact_dir / str(experiment_id)
        root.mkdir(parents=True, exist_ok=True)

        started_at = datetime.now(timezone.utc)

        metadata = {
            "experiment_id": str(experiment_id),
            "provider": self.provider.name,
            "model": self.model,
            "benchmark": benchmark_name,
            "benchmark_version": benchmark_version,
            "python_version": sys.version,
            "platform": platform.platform(),
            "started_at": started_at.isoformat(),
            "task_ids": list(task_ids),
            "max_concurrency": self.max_concurrency,
        }

        self._write_json(root / "metadata.json", metadata)
        self._log(root, "experiment_started", "Experiment started")

        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def execute_task(task_id: str) -> TaskRunResult:
            async with semaphore:
                try:
                    return await self._run_task(
                        task_id=task_id,
                        experiment_id=experiment_id,
                        root=root,
                    )
                except Exception as exc:
                    logger.exception("Unexpected task failure: %s", task_id)
                    return TaskRunResult(
                        task_id=task_id,
                        status=TaskRunStatus.INFRASTRUCTURE_FAILED,
                        error=str(exc),
                    )

        results = await asyncio.gather(
            *(execute_task(task_id) for task_id in task_ids)
        )

        completed = sum(
            result.status == TaskRunStatus.COMPLETED
            for result in results
        )
        failed = len(results) - completed

        status = (
            "completed"
            if failed == 0
            else "failed"
            if completed == 0
            else "partial"
        )

        finished_at = datetime.now(timezone.utc)

        metadata["completed_at"] = finished_at.isoformat()
        metadata["duration_seconds"] = (
            finished_at - started_at
        ).total_seconds()

        summary = ExperimentRunResult(
            experiment_id=experiment_id,
            status=status,
            total_tasks=len(results),
            completed_tasks=completed,
            failed_tasks=failed,
            task_results=results,
            metadata=metadata,
        )

        self._write_json(root / "metadata.json", metadata)
        self._write_json(
            root / "result.json",
            summary.model_dump(mode="json"),
        )

        self._log(
            root,
            "experiment_finished",
            f"Status: {status}; completed: {completed}; failed: {failed}",
        )

        return summary

    async def _run_task(
        self,
        *,
        task_id: str,
        experiment_id: UUID,
        root: Path,
    ) -> TaskRunResult:
        task_dir = root / "tasks" / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        result = TaskRunResult(
            task_id=task_id,
            status=TaskRunStatus.RUNNING,
        )

        sandbox: Sandbox | None = None

        self._log(
            task_dir,
            "task_started",
            f"Starting task {task_id}",
        )

        try:
            task = self.task_loader(task_id)

            request = self.request_builder(
                task,
                experiment_id,
                self.model,
            )

            self._write_json(
                task_dir / "request.json",
                request.model_dump(mode="json"),
            )

            try:
                response = await self.provider.generate(request)
            except Exception as exc:
                result.status = TaskRunStatus.MODEL_FAILED
                result.error = str(exc)
                self._log(task_dir, "model_failed", str(exc))
                return result

            self._write_json(
                task_dir / "raw_response.json",
                response.raw_response,
            )

            self._write_json(
                task_dir / "response.json",
                response.model_dump(
                    mode="json",
                    exclude={"raw_response"},
                ),
            )

            if response.patch is None:
                result.status = TaskRunStatus.PATCH_REJECTED
                result.error = "Model response did not contain a patch."
                self._log(
                    task_dir,
                    "patch_missing",
                    result.error,
                )
                return result

            if response.diagnosis is not None:
                self._write_json(
                    task_dir / "diagnosis.json",
                    response.diagnosis.model_dump(mode="json"),
                )

            self._write_text(
                task_dir / "patch.diff",
                response.patch.content,
            )

            sandbox = self.sandbox_factory(task, experiment_id)

            sandbox.apply_patch(response.patch.content)

            self._log(
                task_dir,
                "patch_applied",
                "Patch applied to sandbox",
            )

            evidence = await asyncio.to_thread(
                sandbox.execute,
                task,
            )

            self._write_json(
                task_dir / "execution.json",
                evidence.model_dump(mode="json"),
            )

            evaluation = self.grader(
                task,
                experiment_id,
                response,
                evidence,
            )

            self._write_json(
                task_dir / "grading.json",
                evaluation.model_dump(mode="json"),
            )

            result.status = TaskRunStatus.COMPLETED
            result.score = evaluation.total_score

            result.artifacts = {
                "request": str(task_dir / "request.json"),
                "response": str(task_dir / "response.json"),
                "raw_response": str(task_dir / "raw_response.json"),
                "patch": str(task_dir / "patch.diff"),
                "execution": str(task_dir / "execution.json"),
                "grading": str(task_dir / "grading.json"),
            }

            self._log(
                task_dir,
                "task_completed",
                f"Score: {evaluation.total_score}",
            )

        except Exception as exc:
            result.status = TaskRunStatus.EXECUTION_FAILED
            result.error = str(exc)

            self._log(
                task_dir,
                "task_failed",
                str(exc),
            )

            logger.exception("Task failed: %s", task_id)

        finally:
            if sandbox is not None:
                try:
                    await asyncio.to_thread(sandbox.cleanup)
                except Exception as exc:
                    self._log(
                        task_dir,
                        "cleanup_failed",
                        str(exc),
                    )
                    logger.exception(
                        "Sandbox cleanup failed: %s",
                        task_id,
                    )

        return result

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        temporary = path.with_name(path.name + ".tmp")

        try:
            temporary.write_text(
                json.dumps(
                    data,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                ),
                encoding="utf-8",
            )
            temporary.replace(path)
        finally:
            if temporary.exists():
                temporary.unlink()

    @staticmethod
    def _write_text(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def _log(
        directory: Path,
        event: str,
        message: str,
    ) -> None:
        directory.mkdir(parents=True, exist_ok=True)

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "message": message,
        }

        with (directory / "logs.jsonl").open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(entry, ensure_ascii=False) + "\n"
            )
