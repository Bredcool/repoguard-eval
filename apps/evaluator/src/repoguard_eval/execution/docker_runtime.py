"""Secure Docker container and volume lifecycle management."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from uuid import UUID

from repoguard_eval.exceptions import ExecutionError


@dataclass(frozen=True, slots=True)
class DockerRuntime:
    """References to Docker resources owned by one evaluation job."""

    job_id: str
    container_id: str
    container_name: str
    volume_name: str
    image: str


@dataclass(frozen=True, slots=True)
class DockerResourceLimits:
    """Resource limits applied to an evaluation container."""

    memory: str = "512m"
    cpus: float = 1.0
    pids_limit: int = 128
    tmpfs_size: str = "64m"


class DockerRuntimeManager:
    """Manage isolated Docker containers and job-specific volumes."""

    _CONTAINER_ID_PATTERN = re.compile(r"^[a-fA-F0-9]{12,64}$")
    _MEMORY_PATTERN = re.compile(r"^[1-9][0-9]*(?:k|m|g)$")
    _TMPFS_PATTERN = re.compile(r"^[1-9][0-9]*(?:k|m|g)$")

    def __init__(
        self,
        process_manager: DockerProcessManager,
        allowed_images: set[str] | frozenset[str],
        limits: DockerResourceLimits | None = None,
    ) -> None:
        if not callable(getattr(process_manager, "run", None)):
            raise ExecutionError("Invalid Docker process manager.")

        if (
            not isinstance(allowed_images, (set, frozenset))
            or not allowed_images
            or any(
                not isinstance(image, str)
                or not image.strip()
                or "\x00" in image
                for image in allowed_images
            )
        ):
            raise ExecutionError("Docker image allowlist is invalid.")

        if limits is None:
            limits = DockerResourceLimits()

        self._validate_limits(limits)

        self.process_manager = process_manager
        self.allowed_images = frozenset(allowed_images)
        self.limits = limits

    @classmethod
    def _validate_limits(cls, limits: DockerResourceLimits) -> None:
        if not isinstance(limits, DockerResourceLimits):
            raise ExecutionError("Invalid Docker resource limits.")

        if (
            not isinstance(limits.memory, str)
            or not cls._MEMORY_PATTERN.fullmatch(limits.memory)
        ):
            raise ExecutionError("Invalid Docker memory limit.")

        if (
            isinstance(limits.cpus, bool)
            or not isinstance(limits.cpus, (int, float))
            or not math.isfinite(limits.cpus)
            or limits.cpus <= 0
        ):
            raise ExecutionError("Invalid Docker CPU limit.")

        if (
            isinstance(limits.pids_limit, bool)
            or not isinstance(limits.pids_limit, int)
            or limits.pids_limit <= 0
        ):
            raise ExecutionError("Invalid Docker PID limit.")

        if (
            not isinstance(limits.tmpfs_size, str)
            or not cls._TMPFS_PATTERN.fullmatch(limits.tmpfs_size)
        ):
            raise ExecutionError("Invalid Docker tmpfs size.")

    @staticmethod
    def _normalize_job_id(job_id: str) -> str:
        if not isinstance(job_id, str):
            raise ExecutionError("Invalid Docker job ID.")

        try:
            parsed = UUID(job_id)
        except (ValueError, AttributeError) as exc:
            raise ExecutionError("Invalid Docker job ID.") from exc

        if str(parsed) != job_id:
            raise ExecutionError("Docker job ID must use canonical UUID format.")

        return job_id

    def _run_checked(
        self,
        args: list[str],
        operation: str,
        timeout: float = 30.0,
    ) -> str:
        result = self.process_manager.run(args, timeout=timeout)

        if result.returncode != 0:
            detail = result.stderr.strip()[-1000:]
            raise ExecutionError(
                f"Docker {operation} failed with exit code "
                f"{result.returncode}: {detail}"
            )

        return result.stdout.strip()

    def create(self, job_id: str, image: str) -> DockerRuntime:
        """Create a dedicated volume and restricted container for a job."""

        normalized_job_id = self._normalize_job_id(job_id)

        if not isinstance(image, str) or image not in self.allowed_images:
            raise ExecutionError("Docker image is not in the trusted image allowlist.")

        resource_id = normalized_job_id.replace("-", "")
        container_name = f"repoguard-{resource_id}"
        volume_name = f"repoguard-{resource_id}"

        self._run_checked(
            [
                "volume",
                "create",
                "--label",
                "repoguard.managed=true",
                "--label",
                f"repoguard.job_id={normalized_job_id}",
                volume_name,
            ],
            "volume creation",
        )

        limits = self.limits

        try:
            container_id = self._run_checked(
                [
                    "create",
                    "--name",
                    container_name,
                    "--label",
                    "repoguard.managed=true",
                    "--label",
                    f"repoguard.job_id={normalized_job_id}",
                    "--network",
                    "none",
                    "--read-only",
                    "--cap-drop",
                    "ALL",
                    "--security-opt",
                    "no-new-privileges",
                    "--pids-limit",
                    str(limits.pids_limit),
                    "--memory",
                    limits.memory,
                    "--cpus",
                    str(limits.cpus),
                    "--mount",
                    f"type=volume,source={volume_name},target=/workspace",
                    "--tmpfs",
                    f"/tmp:rw,noexec,nosuid,size={limits.tmpfs_size}",
                    "--workdir",
                    "/workspace",
                    "--entrypoint",
                    "sleep",
                    image,
                    "infinity",
                ],
                "container creation",
            )

            if not self._CONTAINER_ID_PATTERN.fullmatch(container_id):
                raise ExecutionError("Docker returned an invalid container ID.")

        except Exception as exc:
            try:
                self.process_manager.run(
                    ["volume", "rm", volume_name],
                    timeout=15.0,
                )
            except ExecutionError:
                pass

            if isinstance(exc, ExecutionError):
                raise

            raise ExecutionError(
                f"Unable to create Docker container: {exc}"
            ) from exc

        return DockerRuntime(
            job_id=normalized_job_id,
            container_id=container_id,
            container_name=container_name,
            volume_name=volume_name,
            image=image,
        )

    def _validate_runtime(self, runtime: DockerRuntime) -> None:
        if not isinstance(runtime, DockerRuntime):
            raise ExecutionError("Invalid Docker runtime reference.")

        job_id = self._normalize_job_id(runtime.job_id)
        resource_id = job_id.replace("-", "")

        if (
            runtime.container_name != f"repoguard-{resource_id}"
            or runtime.volume_name != f"repoguard-{resource_id}"
            or runtime.image not in self.allowed_images
            or not isinstance(runtime.container_id, str)
            or not self._CONTAINER_ID_PATTERN.fullmatch(runtime.container_id)
        ):
            raise ExecutionError("Docker runtime reference failed validation.")

    def start(self, runtime: DockerRuntime) -> None:
        """Start a previously created evaluation container."""

        self._validate_runtime(runtime)
        self._run_checked(["start", runtime.container_id], "container start")

    def inspect(self, runtime: DockerRuntime) -> str:
        """Return the current container state."""

        self._validate_runtime(runtime)

        status = self._run_checked(
            [
                "inspect",
                "--format",
                "{{.State.Status}}",
                runtime.container_id,
            ],
            "container inspection",
        )

        allowed_statuses = {
            "created",
            "running",
            "paused",
            "restarting",
            "removing",
            "exited",
            "dead",
        }

        if status not in allowed_statuses:
            raise ExecutionError("Docker returned an unknown container state.")

        return status

    def stop(
        self,
        runtime: DockerRuntime,
        timeout: int = 10,
    ) -> None:
        """Stop a running evaluation container."""

        self._validate_runtime(runtime)

        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, int)
            or timeout < 0
        ):
            raise ExecutionError("Invalid Docker stop timeout.")

        self._run_checked(
            ["stop", "--time", str(timeout), runtime.container_id],
            "container stop",
            timeout=float(timeout + 15),
        )

    def cleanup(self, runtime: DockerRuntime) -> None:
        """Force-remove the container and its dedicated volume."""

        self._validate_runtime(runtime)

        self._run_checked(
            ["rm", "--force", runtime.container_id],
            "container removal",
        )

        self._run_checked(
            ["volume", "rm", runtime.volume_name],
            "volume removal",
        )
