"""Orchestrate benchmark execution checks."""

from __future__ import annotations

from collections.abc import Sequence

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.command_runner import ContainerCommandRunner
from repoguard_eval.execution.docker_runtime import DockerRuntime
from repoguard_eval.grading.enums import ExecutionStatus
from repoguard_eval.grading.schemas import ExecutionCheckEvidence


class ExecutionEvaluator:
    """Run ordered execution checks and preserve individual evidence."""

    def __init__(self, command_runner: ContainerCommandRunner) -> None:
        if not callable(getattr(command_runner, "run_check", None)):
            raise ExecutionError("Invalid container command runner.")

        self.command_runner = command_runner

    def evaluate(
        self,
        runtime: DockerRuntime,
        name: str,
        commands: Sequence[str],
        timeout: float = 300.0,
    ) -> tuple[ExecutionCheckEvidence, ...]:
        """Execute commands until a failure or infrastructure error occurs."""

        if not isinstance(name, str) or not name.strip():
            raise ExecutionError("Execution check name cannot be empty.")

        if isinstance(commands, (str, bytes)) or not isinstance(
            commands, (list, tuple)
        ):
            raise ExecutionError("Execution commands must be a list or tuple.")

        if any(not isinstance(command, str) or not command.strip() for command in commands):
            raise ExecutionError("Execution commands contain an invalid command.")

        evidence: list[ExecutionCheckEvidence] = []

        for index, command in enumerate(commands):
            check_name = f"{name}_{index + 1}"

            result = self.command_runner.run_check(
                runtime=runtime,
                name=check_name,
                command=command,
                timeout=timeout,
            )
            evidence.append(result)

            if result.status != ExecutionStatus.PASSED:
                for skipped_index in range(index + 1, len(commands)):
                    evidence.append(
                        ExecutionCheckEvidence(
                            name=f"{name}_{skipped_index + 1}",
                            status=ExecutionStatus.SKIPPED,
                            command=commands[skipped_index],
                            exit_code=None,
                            duration_seconds=0.0,
                            stdout="",
                            stderr="Not executed because a previous check did not pass.",
                        )
                    )
                break

        return tuple(evidence)