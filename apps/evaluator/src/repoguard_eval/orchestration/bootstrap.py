from pathlib import Path

from repoguard_eval.orchestration.runner import ExperimentOrchestrator
from repoguard_eval.orchestration.runtime import build_runtime


def build_orchestrator(
    *,
    artifact_dir: Path,
    model: str,
    max_concurrency: int = 1,
    provider=None,
    task_loader=None,
    request_builder=None,
    sandbox_factory=None,
    grader=None,
):
    dependencies = {
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
            "Runtime adapters are not configured: "
            + ", ".join(missing)
        )

    if provider is not None:
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

    return build_runtime(
        model=model,
        artifact_dir=artifact_dir,
        task_loader=task_loader,
        request_builder=request_builder,
        sandbox_factory=sandbox_factory,
        grader=grader,
        max_concurrency=max_concurrency,
    )