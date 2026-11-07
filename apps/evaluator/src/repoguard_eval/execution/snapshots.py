"""Repository snapshot creation and integrity verification."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.workspace import (
    Workspace,
    WorkspaceManager,
)


@dataclass(frozen=True, slots=True)
class SnapshotEntry:
    """Represent one file or directory in a repository snapshot."""

    path: str
    kind: str
    size: int
    sha256: str | None = None


@dataclass(frozen=True, slots=True)
class RepositorySnapshot:
    """Represent an immutable repository baseline manifest."""

    snapshot_id: str
    job_id: str
    repository_path: Path
    created_at: datetime
    entries: tuple[SnapshotEntry, ...]


class SnapshotManager:
    """Create repository snapshots and verify their integrity."""

    _REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
    _CHUNK_SIZE = 1024 * 1024

    def __init__(self, workspace_manager: WorkspaceManager) -> None:
        """Initialize the manager with a workspace manager."""

        if not isinstance(workspace_manager, WorkspaceManager):
            raise ExecutionError("Invalid workspace manager.")

        self.workspace_manager = workspace_manager

    def create_snapshot(
        self,
        workspace: Workspace,
        repository_name: str = "repository",
    ) -> RepositorySnapshot:
        """Create a baseline manifest for a repository in a workspace."""

        repository_path = self._resolve_repository(
            workspace=workspace,
            repository_name=repository_name,
        )

        try:
            entries = self._collect_entries(repository_path)

            return RepositorySnapshot(
                snapshot_id=str(uuid.uuid4()),
                job_id=workspace.job_id,
                repository_path=repository_path,
                created_at=datetime.now(timezone.utc),
                entries=tuple(entries),
            )

        except ExecutionError:
            raise
        except OSError as exc:
            raise ExecutionError(
                f"Unable to create repository snapshot: {exc}"
            ) from exc

    def verify_snapshot(
        self,
        workspace: Workspace,
        snapshot: RepositorySnapshot,
    ) -> bool:
        """Check whether the repository still matches its baseline snapshot."""

        self.workspace_manager.validate_workspace(workspace)

        if not isinstance(snapshot, RepositorySnapshot):
            raise ExecutionError("Invalid repository snapshot.")

        if snapshot.job_id != workspace.job_id:
            raise ExecutionError(
                "Snapshot does not belong to the supplied workspace."
            )

        if not isinstance(snapshot.repository_path, Path):
            raise ExecutionError("Invalid snapshot repository path.")

        if (
            not isinstance(snapshot.entries, tuple)
            or any(
                not isinstance(entry, SnapshotEntry)
                for entry in snapshot.entries
            )
        ):
            raise ExecutionError("Invalid snapshot entries.")

        repository_path = self._resolve_repository(
            workspace=workspace,
            repository_name=snapshot.repository_path.name,
        )

        if repository_path != snapshot.repository_path:
            raise ExecutionError(
                "Snapshot repository path does not match the workspace."
            )

        try:
            current_entries = tuple(
                self._collect_entries(repository_path)
            )

            return current_entries == snapshot.entries

        except ExecutionError:
            raise
        except OSError as exc:
            raise ExecutionError(
                f"Unable to verify repository snapshot: {exc}"
            ) from exc

    def _resolve_repository(
        self,
        workspace: Workspace,
        repository_name: str,
    ) -> Path:
        """Resolve and validate a repository directory inside a workspace."""

        if (
            not isinstance(repository_name, str)
            or not self._REPOSITORY_PATTERN.fullmatch(repository_name)
        ):
            raise ExecutionError("Invalid repository directory name.")

        workspace_path = self.workspace_manager.validate_workspace(workspace)
        repository_path = workspace_path / repository_name

        try:
            if (
                repository_path.is_symlink()
                or repository_path.is_junction()
            ):
                raise ExecutionError(
                    "Repository directory must not be a symbolic link or junction."
                )

            resolved_path = repository_path.resolve(strict=True)

            if resolved_path.parent != workspace_path:
                raise ExecutionError(
                    "Repository directory is outside the workspace."
                )

            if not resolved_path.is_dir():
                raise ExecutionError(
                    "Repository path must be an existing directory."
                )

            return resolved_path

        except ExecutionError:
            raise
        except OSError as exc:
            raise ExecutionError(
                f"Unable to resolve repository directory: {exc}"
            ) from exc

    def _collect_entries(self, root: Path) -> list[SnapshotEntry]:
        """Collect deterministic metadata and hashes for repository entries."""

        entries: list[SnapshotEntry] = []

        def walk(directory: Path, relative_directory: Path) -> None:
            with os.scandir(directory) as children:
                for child in children:
                    child_path = Path(child.path)
                    relative_path = relative_directory / child.name

                    if (
                        child.is_symlink()
                        or child_path.is_junction()
                    ):
                        raise ExecutionError(
                            "Symbolic links and junctions are not allowed: "
                            f"{relative_path.as_posix()}"
                        )

                    child_stat = child.stat(follow_symlinks=False)

                    if stat.S_ISDIR(child_stat.st_mode):
                        entries.append(
                            SnapshotEntry(
                                path=relative_path.as_posix(),
                                kind="directory",
                                size=0,
                            )
                        )

                        walk(child_path, relative_path)

                    elif stat.S_ISREG(child_stat.st_mode):
                        size, digest = self._hash_file(child_path)

                        entries.append(
                            SnapshotEntry(
                                path=relative_path.as_posix(),
                                kind="file",
                                size=size,
                                sha256=digest,
                            )
                        )

                    else:
                        raise ExecutionError(
                            "Unsupported special file in repository: "
                            f"{relative_path.as_posix()}"
                        )

        walk(root, Path())

        return sorted(entries, key=lambda entry: entry.path)

    def _hash_file(self, path: Path) -> tuple[int, str]:
        """Calculate a file's SHA-256 digest and byte size."""

        digest = hashlib.sha256()
        size = 0

        with path.open("rb") as file:
            while chunk := file.read(self._CHUNK_SIZE):
                digest.update(chunk)
                size += len(chunk)

        return size, digest.hexdigest()
