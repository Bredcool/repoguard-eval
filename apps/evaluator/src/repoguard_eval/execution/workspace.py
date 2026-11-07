"""Workspace lifecycle management for execution jobs."""

from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from repoguard_eval.exceptions import ExecutionError


@dataclass(frozen=True, slots=True)
class Workspace:
    """Represents an isolated workspace assigned to one execution job."""

    job_id: str
    path: Path


class WorkspaceManager:
    """Create and manage isolated execution workspaces."""

    def __init__(self, root: Path) -> None:
        """Initialize the manager with a dedicated workspace root."""

        try:
            requested_root = Path(root).expanduser().absolute()

            if (
                requested_root.is_symlink()
                or requested_root.is_junction()
            ):
                raise ExecutionError(
                    "Workspace root must not be a symbolic link or junction."
                )

            requested_root.mkdir(parents=True, exist_ok=True)

            if (
                requested_root.is_symlink()
                or requested_root.is_junction()
            ):
                raise ExecutionError(
                    "Workspace root must not be a symbolic link or junction."
                )

            if not requested_root.is_dir():
                raise ExecutionError(
                    "Workspace root must be a directory."
                )

            self.root = requested_root.resolve(strict=True)

        except ExecutionError:
            raise
        except OSError as exc:
            raise ExecutionError(
                f"Unable to initialize workspace root: {exc}"
            ) from exc
        except (TypeError, ValueError) as exc:
            raise ExecutionError(
                f"Invalid workspace root: {exc}"
            ) from exc

    def create(self) -> Workspace:
        """Create a unique workspace for an execution job."""

        job_id = str(uuid.uuid4())
        workspace_path = self.root / f"job-{job_id}"

        try:
            workspace_path.mkdir(
                parents=False,
                exist_ok=False,
            )

            return Workspace(
                job_id=job_id,
                path=workspace_path,
            )

        except OSError as exc:
            raise ExecutionError(
                f"Unable to create execution workspace: {exc}"
            ) from exc

    def validate_workspace(self, workspace: Workspace) -> Path:
        """Validate workspace identity and managed-root containment."""

        if not isinstance(workspace, Workspace):
            raise ExecutionError("Invalid workspace object.")

        if not isinstance(workspace.job_id, str):
            raise ExecutionError(
                "Workspace job identifier must be a string."
            )

        if not isinstance(workspace.path, Path):
            raise ExecutionError(
                "Workspace path must be a pathlib Path object."
            )

        try:
            job_uuid = uuid.UUID(workspace.job_id)

            if str(job_uuid) != workspace.job_id:
                raise ExecutionError(
                    "Workspace job identifier is not canonical."
                )

            workspace_path = workspace.path

            if workspace_path.name != f"job-{workspace.job_id}":
                raise ExecutionError(
                    "Workspace path does not match its job identifier."
                )

            if (
                workspace_path.is_symlink()
                or workspace_path.is_junction()
            ):
                raise ExecutionError(
                    "Workspace path must not be a symbolic link or junction."
                )

            if workspace_path.parent.resolve(strict=True) != self.root:
                raise ExecutionError(
                    "Workspace is outside the managed workspace root."
                )

            resolved_path = workspace_path.resolve(strict=False)

            if resolved_path.parent != self.root:
                raise ExecutionError(
                    "Resolved workspace is outside the managed workspace root."
                )

            if resolved_path.name != f"job-{workspace.job_id}":
                raise ExecutionError(
                    "Resolved workspace path does not match its job identifier."
                )

            return resolved_path

        except ExecutionError:
            raise
        except OSError as exc:
            raise ExecutionError(
                f"Unable to validate execution workspace: {exc}"
            ) from exc
        except (TypeError, ValueError) as exc:
            raise ExecutionError(
                f"Invalid workspace data: {exc}"
            ) from exc

    def cleanup(self, workspace: Workspace) -> None:
        """Remove a workspace without affecting other job directories."""

        workspace_path = self.validate_workspace(workspace)

        try:
            if not workspace_path.exists():
                return

            if not workspace_path.is_dir():
                raise ExecutionError(
                    "Workspace path is not a directory."
                )

            shutil.rmtree(workspace_path)

        except ExecutionError:
            raise
        except OSError as exc:
            raise ExecutionError(
                f"Unable to clean execution workspace: {exc}"
            ) from exc