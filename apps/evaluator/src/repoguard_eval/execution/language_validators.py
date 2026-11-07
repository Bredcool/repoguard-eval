"""Language-specific repository validation."""

from __future__ import annotations

from dataclasses import dataclass

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.docker_runtime import DockerRuntime
from repoguard_eval.execution.evaluator import ExecutionEvaluator
from repoguard_eval.grading.schemas import ExecutionCheckEvidence


@dataclass(frozen=True, slots=True)
class LanguageValidationConfig:
    """Commands required to validate a language repository."""

    name: str
    build_commands: tuple[str, ...]
    test_commands: tuple[str, ...]
    static_commands: tuple[str, ...] = ()
    timeout_seconds: float = 300.0


class LanguageValidator:
    """Base validator for language-specific repository checks."""

    CONFIG: LanguageValidationConfig

    def __init__(self, evaluator: ExecutionEvaluator) -> None:
        if not callable(getattr(evaluator, "evaluate", None)):
            raise ExecutionError("Invalid execution evaluator.")

        self.evaluator = evaluator

    def validate(
        self,
        runtime: DockerRuntime,
    ) -> tuple[ExecutionCheckEvidence, ...]:
        """Run static, build, and test checks in order."""

        config = self.CONFIG
        results: list[ExecutionCheckEvidence] = []

        stages = (
            ("static", config.static_commands),
            ("build", config.build_commands),
            ("test", config.test_commands),
        )

        blocked = False

        for stage_name, commands in stages:
            if not commands:
                continue

            if blocked:
                results.extend(
                    self._skipped(stage_name, commands)
                )
                continue

            stage_results = self.evaluator.evaluate(
                runtime=runtime,
                name=f"{config.name}_{stage_name}",
                commands=commands,
                timeout=config.timeout_seconds,
            )
            results.extend(stage_results)

            if any(
                item.status.value != "passed"
                for item in stage_results
            ):
                blocked = True

        return tuple(results)

    @staticmethod
    def _skipped(
        stage_name: str,
        commands: tuple[str, ...],
    ) -> list[ExecutionCheckEvidence]:
        from repoguard_eval.grading.enums import ExecutionStatus

        return [
            ExecutionCheckEvidence(
                name=f"{stage_name}_{index + 1}",
                status=ExecutionStatus.SKIPPED,
                command=command,
                exit_code=None,
                duration_seconds=0.0,
                stdout="",
                stderr="Not executed because a previous validation stage did not pass.",
            )
            for index, command in enumerate(commands)
        ]


class GoValidator(LanguageValidator):
    """Validate Go repositories."""

    CONFIG = LanguageValidationConfig(
        name="go",
        static_commands=("go vet ./...",),
        build_commands=("go build ./...",),
        test_commands=("go test ./...",),
    )


class PythonValidator(LanguageValidator):
    """Validate Python repositories."""

    CONFIG = LanguageValidationConfig(
        name="python",
        static_commands=("python -m compileall -q .",),
        build_commands=(),
        test_commands=("python -m pytest -q",),
    )


class CppValidator(LanguageValidator):
    """Validate C++ repositories using CMake and GoogleTest."""

    CONFIG = LanguageValidationConfig(
        name="cpp",
        static_commands=(),
        build_commands=(
            "cmake -S . -B build",
            "cmake --build build --parallel 2",
        ),
        test_commands=("ctest --test-dir build --output-on-failure",),
    )