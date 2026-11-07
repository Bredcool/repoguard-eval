from pathlib import Path
from unittest.mock import MagicMock

from repoguard_eval.orchestration.bootstrap import build_orchestrator
from repoguard_eval.orchestration.runner import ExperimentOrchestrator


def test_build_orchestrator_returns_orchestrator():
    provider = MagicMock()
    provider.name = "test-provider"

    orchestrator = build_orchestrator(
        provider=provider,
        task_loader=MagicMock(),
        request_builder=MagicMock(),
        sandbox_factory=MagicMock(),
        grader=MagicMock(),
        artifact_dir=Path("artifacts"),
        model="test-model",
        max_concurrency=2,
    )

    assert isinstance(orchestrator, ExperimentOrchestrator)
    assert orchestrator.model == "test-model"
    assert orchestrator.max_concurrency == 2