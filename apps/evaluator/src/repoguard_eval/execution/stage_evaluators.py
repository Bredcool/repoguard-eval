"""Stage-specific benchmark execution evaluators."""

from __future__ import annotations

from collections.abc import Sequence

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.docker_runtime import DockerRuntime
from repoguard_eval.execution.evaluator import ExecutionEvaluator
from repoguard_eval.grading.schemas import ExecutionCheckEvidence


class StageEvaluator:
    """Base evaluator for one benchmark execution stage."""

    stage_name = "stage"

    def __init__(self, evaluator: ExecutionEvaluator) -> None:
        if not callable(getattr(evaluator, "evaluate", None)):
            raise ExecutionError("Invalid execution evaluator.")

        self.evaluator = evaluator

    def evaluate(
        self,
        runtime: DockerRuntime,
        commands: Sequence[str],
        timeout: float = 300.0,
    ) -> tuple[ExecutionCheckEvidence, ...]:
        return self.evaluator.evaluate(
            runtime=runtime,
            name=self.stage_name,
            commands=commands,
            timeout=timeout,
        )


class BuildEvaluator(StageEvaluator):
    """Evaluate repository build and compilation."""

    stage_name = "build"


class FunctionalTestEvaluator(StageEvaluator):
    """Evaluate public functional tests."""

    stage_name = "functional"


class HiddenTestEvaluator(StageEvaluator):
    """Evaluate private tests without exposing their commands to the agent."""

    stage_name = "hidden"


class RegressionTestEvaluator(StageEvaluator):
    """Evaluate regression tests against previously working behavior."""

    stage_name = "regression"