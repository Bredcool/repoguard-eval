"""Execute benchmark commands inside isolated Docker containers."""

from __future__ import annotations

import math
from dataclasses import dataclass

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.docker_runtime import (
    DockerRuntime,
    DockerRuntimeManager,
)
from repoguard_eval.grading.enums import ExecutionStatus
from repoguard_eval.grading.schemas import ExecutionCheckEvidence


@dataclass(frozen=True, slots=True)
class ContainerCommandResult:
    """Normalized result of a command executed inside a container."""

    command: str
    status: ExecutionStatus
    exit_code: int | None
    duration_seconds: float
    stdout: str
    stderr: str


class ContainerCommandRunner:
    """Run trusted benchmark commands through Docker exec."""

    WORKING_DIRECTORY = "/workspace/repository"

    def __init__(self, runtime_manager: DockerRuntimeManager) -> None:
        if not callable(getattr(runtime_manager, "_validate_runtime", None)):
            raise ExecutionError("Invalid Docker runtime manager.")

        if not callable(getattr(runtime_manager.process_manager, "run", None)):
            raise ExecutionError("Invalid Docker process manager.")

        self.runtime_manager = runtime_manager

    @staticmethod
    def _validate_command(command: str) -> None:
        if (
            not isinstance(command, str)
            or not command.strip()
            or "\x00" in command
        ):
            raise ExecutionError("Benchmark command must be a non-empty string.")

    @staticmethod
    def _validate_timeout(timeout: float) -> None:
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout <= 0
        ):
            raise ExecutionError("Command timeout must be a positive number.")

    def run(
        self,
        runtime: DockerRuntime,
        command: str,
        timeout: float = 300.0,
    ) -> ContainerCommandResult:
        """Execute one benchmark command inside the repository directory."""

        self.runtime_manager._validate_runtime(runtime)
        self._validate_command(command)
        self._validate_timeout(timeout)

        try:
            result = self.runtime_manager.process_manager.run(
                [
                    "exec",
                    "--workdir",
                    self.WORKING_DIRECTORY,
                    runtime.container_id,
                    "sh",
                    "-lc",
                    command,
                ],
                timeout=float(timeout),
            )
        except ExecutionError as exc:
            # Docker/process failures are infrastructure errors, not agent failures.
            return ContainerCommandResult(
                command=command,
                status=ExecutionStatus.ERROR,
                exit_code=None,
                duration_seconds=0.0,
                stdout="",
                stderr=str(exc),
            )
        except Exception as exc:
            return ContainerCommandResult(
                command=command,
                status=ExecutionStatus.ERROR,
                exit_code=None,
                duration_seconds=0.0,
                stdout="",
                stderr=f"Unexpected command execution error: {exc}",
            )

        status = (
            ExecutionStatus.PASSED
            if result.returncode == 0
            else ExecutionStatus.FAILED
        )

        return ContainerCommandResult(
            command=command,
            status=status,
            exit_code=result.returncode,
            duration_seconds=result.duration_seconds,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def run_check(
        self,
        runtime: DockerRuntime,
        name: str,
        command: str,
        timeout: float = 300.0,
    ) -> ExecutionCheckEvidence:
        """Execute a command and convert it into grading evidence."""

        result = self.run(runtime, command, timeout)

        return ExecutionCheckEvidence(
            name=name,
            status=result.status,
            command=result.command,
            exit_code=result.exit_code,
            duration_seconds=result.duration_seconds,
            stdout=result.stdout,
            stderr=result.stderr,
        )