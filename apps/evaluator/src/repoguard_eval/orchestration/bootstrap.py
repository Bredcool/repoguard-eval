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
    provider: BaseProvider,
    task_loader: Callable[[str], TaskDefinition],
    request_builder: Callable[
        [TaskDefinition, UUID, str], ProviderRequest
    ],
    sandbox_factory: Callable,
    grader: Callable[
        [
            TaskDefinition,
            UUID,
            ProviderResponse,
            ExecutionEvidence,
        ],
        EvaluationResult,
    ],
    artifact_dir: Path,
    model: str,
    max_concurrency: int = 1,
) -> ExperimentOrchestrator:
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