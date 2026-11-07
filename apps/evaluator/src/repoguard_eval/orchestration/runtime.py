from pathlib import Path
from typing import Any, Callable
from uuid import UUID

from repoguard_eval.config.provider import get_provider_settings
from repoguard_eval.providers.openai import OpenAIProvider
from repoguard_eval.prompts.builder import build_agent_prompt
from repoguard_eval.context.builder import RepositoryContextBuilder
from repoguard_eval.benchmarks.registry import BenchmarkRegistry
from repoguard_eval.orchestration.runner import ExperimentOrchestrator


class RuntimeConfigurationError(RuntimeError):
    pass


def build_runtime(
    *,
    model: str,
    artifact_dir: Path,
    task_loader: Callable,
    sandbox_factory: Callable,
    grader: Callable,
    request_builder: Callable,
    max_concurrency: int = 1,
) -> ExperimentOrchestrator:
    settings = get_provider_settings()

    if not settings.is_ready():
        raise RuntimeConfigurationError(
            "Provider configuration is incomplete. "
            "Configure OPENAI_API_KEY and model settings."
        )

    provider = OpenAIProvider(settings=settings)

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