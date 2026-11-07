"""Safe repository transfer between host workspaces and Docker volumes."""

from __future__ import annotations

import os
import re
import shutil
import stat
from pathlib import Path

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.docker_runtime import (
    DockerRuntime,
    DockerRuntimeManager,
)
from repoguard_eval.execution.workspace import (
    Workspace,
    WorkspaceManager,
)


class DockerVolumeTransfer:
    """Transfer repository directories through the Docker CLI."""

    _NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

    def __init__(
        self,
        runtime_manager: DockerRuntimeManager,
        workspace_manager: WorkspaceManager,
    ) -> None:
        if not callable(getattr(runtime_manager, "_validate_runtime", None)):
            raise ExecutionError("Invalid Docker runtime manager.")

        if not callable(getattr(workspace_manager, "validate_workspace", None)):
            raise ExecutionError("Invalid workspace manager.")

        self.runtime_manager = runtime_manager
        self.workspace_manager = workspace_manager

    @classmethod
    def _validate_name(cls, name: str) -> None:
        if not isinstance(name, str) or not cls._NAME_PATTERN.fullmatch(name):
            raise ExecutionError("Invalid Docker transfer directory name.")

    def _validate_runtime(self, runtime: DockerRuntime) -> None:
        self.runtime_manager._validate_runtime(runtime)

    @staticmethod
    def _validate_directory_tree(path: Path) -> None:
        try:
            if path.is_symlink() or path.is_junction() or not path.is_dir():
                raise ExecutionError("Transfer source must be a regular directory.")

            with os.scandir(path) as entries:
                for entry in entries:
                    entry_path = Path(entry.path)

                    if entry.is_symlink() or entry_path.is_junction():
                        raise ExecutionError(
                            f"Symbolic links and junctions are not allowed: {entry_path}"
                        )

                    entry_stat = entry.stat(follow_symlinks=False)

                    if stat.S_ISDIR(entry_stat.st_mode):
                        DockerVolumeTransfer._validate_directory_tree(entry_path)
                    elif not stat.S_ISREG(entry_stat.st_mode):
                        raise ExecutionError(
                            f"Unsupported special file: {entry_path}"
                        )
        except ExecutionError:
            raise
        except OSError as exc:
            raise ExecutionError(
                f"Unable to validate transfer directory: {exc}"
            ) from exc

    def _run_copy(self, args: list[str], operation: str) -> None:
        try:
            result = self.runtime_manager.process_manager.run(
                args,
                timeout=120.0,
            )
        except ExecutionError:
            raise
        except Exception as exc:
            raise ExecutionError(
                f"Docker {operation} failed: {exc}"
            ) from exc

        if result.returncode != 0:
            detail = result.stderr.strip()[-1000:]
            raise ExecutionError(
                f"Docker {operation} failed with exit code "
                f"{result.returncode}: {detail}"
            )

    def copy_to_container(
        self,
        runtime: DockerRuntime,
        workspace: Workspace,
        source_name: str = "repository",
    ) -> None:
        """Copy a workspace repository into the container's mounted volume."""

        self._validate_runtime(runtime)
        self._validate_name(source_name)

        workspace_path = self.workspace_manager.validate_workspace(workspace)
        source = workspace_path / source_name

        if source.is_symlink() or source.is_junction():
            raise ExecutionError("Transfer source must not be a link.")

        try:
            resolved_source = source.resolve(strict=True)
        except OSError as exc:
            raise ExecutionError(
                f"Unable to resolve transfer source: {exc}"
            ) from exc

        if resolved_source.parent != workspace_path:
            raise ExecutionError("Transfer source must be a direct workspace child.")

        self._validate_directory_tree(resolved_source)

        self._run_copy(
            [
                "cp",
                str(resolved_source),
                f"{runtime.container_id}:/workspace/",
            ],
            "copy to container",
        )

    def copy_from_container(
        self,
        runtime: DockerRuntime,
        workspace: Workspace,
        source_name: str = "repository",
        destination_name: str = "repository-output",
    ) -> Path:
        """Copy a container directory into the workspace and validate it."""

        self._validate_runtime(runtime)
        self._validate_name(source_name)
        self._validate_name(destination_name)

        workspace_path = self.workspace_manager.validate_workspace(workspace)
        destination = workspace_path / destination_name

        if (
            destination.exists()
            or destination.is_symlink()
            or destination.is_junction()
        ):
            raise ExecutionError("Transfer destination already exists.")

        try:
            self._run_copy(
                [
                    "cp",
                    f"{runtime.container_id}:/workspace/{source_name}",
                    str(destination),
                ],
                "copy from container",
            )

            self._validate_directory_tree(destination)
            return destination

        except Exception:
            if destination.exists() or destination.is_symlink():
                shutil.rmtree(destination, ignore_errors=True)
            raise
