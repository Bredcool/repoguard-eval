from pathlib import Path
from typing import Callable
from uuid import UUID

from repoguard_eval.models.task import TaskDefinition
from repoguard_eval.orchestration.runner import ExperimentOrchestrator
from repoguard_eval.providers.base import BaseProvider
from repoguard_eval.providers.schemas.response import (
    ProviderRequest,
    ProviderResponse,
)
from repoguard_eval.grading.schemas import (
    EvaluationResult,
    ExecutionEvidence,
)


def build_orchestrator(
    *,
    artifact_dir: Path,
    model: str,
    max_concurrency: int = 1,
    provider: BaseProvider | None = None,
    task_loader: Callable[[str], TaskDefinition] | None = None,
    request_builder: Callable[
        [TaskDefinition, UUID, str], ProviderRequest
    ] | None = None,
    sandbox_factory: Callable | None = None,
    grader: Callable[
        [
            TaskDefinition,
            UUID,
            ProviderResponse,
            ExecutionEvidence,
        ],
        EvaluationResult,
    ] | None = None,
) -> ExperimentOrchestrator:
    dependencies = {
        "provider": provider,
        "task_loader": task_loader,
        "request_builder": request_builder,
        "sandbox_factory": sandbox_factory,
        "grader": grader,
    }

    missing = [
        name for name, value in dependencies.items()
        if value is None
    ]

    if missing:
        raise RuntimeError(
            "Experiment runtime is not configured. Missing adapters: "
            + ", ".join(missing)
        )

    return ExperimentOrchestrator(
        provider=provider,
        task_loader=task_loader,
        request_builder=request_builder,
        sandbox_factory=sandbox_factory,
        grader=grader,
        artifact_dir=artifact_dir,
        model=model,
        max_concurrency=max_concurrency,
    )