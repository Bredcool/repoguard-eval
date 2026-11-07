"""Safe Docker CLI process execution."""

from __future__ import annotations

import math
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from repoguard_eval.exceptions import ExecutionError


@dataclass(frozen=True, slots=True)
class DockerCommandResult:
    """Result returned by a Docker CLI process."""

    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float


class DockerProcessManager:
    """Execute Docker CLI commands without invoking a shell."""

    def __init__(self, executable: str | Path = "docker") -> None:
        if isinstance(executable, Path):
            executable = str(executable)

        if (
            not isinstance(executable, str)
            or not executable.strip()
            or "\x00" in executable
        ):
            raise ExecutionError("Invalid Docker executable.")

        self.executable = executable

    def run(
        self,
        args: Sequence[str],
        timeout: float = 30.0,
    ) -> DockerCommandResult:
        """Run a Docker CLI command and return its process result."""

        if isinstance(args, (str, bytes)) or not isinstance(args, (list, tuple)):
            raise ExecutionError("Docker arguments must be a list or tuple.")

        if any(
            not isinstance(argument, str) or "\x00" in argument
            for argument in args
        ):
            raise ExecutionError("Docker arguments contain invalid values.")

        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout <= 0
        ):
            raise ExecutionError("Docker command timeout must be positive.")

        command = [self.executable, *args]
        started_at = time.monotonic()

        try:
            completed = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - started_at
            stdout = self._decode_output(exc.stdout)
            stderr = self._decode_output(exc.stderr)

            raise ExecutionError(
                f"Docker command timed out after {duration:.2f} seconds. "
                f"stdout={stdout[-1000:]!r}, stderr={stderr[-1000:]!r}"
            ) from exc
        except OSError as exc:
            raise ExecutionError(
                f"Unable to execute Docker CLI: {exc}"
            ) from exc
        except subprocess.SubprocessError as exc:
            raise ExecutionError(
                f"Docker CLI process failed: {exc}"
            ) from exc

        duration = time.monotonic() - started_at

        return DockerCommandResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=duration,
        )

    @staticmethod
    def _decode_output(value: str | bytes | None) -> str:
        """Normalize subprocess output for error reporting."""

        if value is None:
            return ""

        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")

        return value
