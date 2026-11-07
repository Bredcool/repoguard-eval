"""Repository fixture validation and preparation."""

from __future__ import annotations

import os
import re
import shutil
import stat
from pathlib import Path

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.workspace import (
    Workspace,
    WorkspaceManager,
)


class FixtureManager:
    """Validate and copy repository fixtures into job workspaces."""

    _DESTINATION_PATTERN = re.compile(
        r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}"
    )

    def __init__(self, workspace_manager: WorkspaceManager) -> None:
        """Initialize the fixture manager with a workspace manager."""

        self.workspace_manager = workspace_manager

    def copy_fixture(
        self,
        source: Path,
        workspace: Workspace,
        destination_name: str = "repository",
    ) -> Path:
        """Copy a repository fixture into a workspace."""

        if (
            not isinstance(destination_name, str)
            or not self._DESTINATION_PATTERN.fullmatch(destination_name)
        ):
            raise ExecutionError("Invalid fixture destination name.")

        try:
            source_path = Path(source).expanduser()

            workspace_path = (
                self.workspace_manager.validate_workspace(workspace)
            )

            if (
                source_path.is_symlink()
                or source_path.is_junction()
            ):
                raise ExecutionError(
                    "Fixture source must not be a symbolic link or junction."
                )

            source_path = source_path.resolve(strict=True)

            if not source_path.is_dir():
                raise ExecutionError(
                    "Fixture source must be an existing directory."
                )

            if not workspace_path.is_dir():
                raise ExecutionError(
                    "Workspace path must be an existing directory."
                )

            destination = workspace_path / destination_name

            if (
                source_path == destination
                or source_path in destination.parents
                or destination in source_path.parents
            ):
                raise ExecutionError(
                    "Fixture source and destination must not overlap."
                )

            if (
                destination.exists()
                or destination.is_symlink()
                or destination.is_junction()
            ):
                raise ExecutionError(
                    "Fixture destination already exists."
                )

            self._copy_directory(
                source=source_path,
                destination=destination,
            )

            return destination

        except ExecutionError:
            raise
        except OSError as exc:
            raise ExecutionError(
                f"Unable to prepare repository fixture: {exc}"
            ) from exc
        except (TypeError, ValueError) as exc:
            raise ExecutionError(
                f"Invalid fixture source: {exc}"
            ) from exc

    def _copy_directory(
        self,
        source: Path,
        destination: Path,
    ) -> None:
        """Copy a directory while rejecting links and special files."""

        destination.mkdir(parents=False, exist_ok=False)

        try:
            with os.scandir(source) as entries:
                for entry in entries:
                    source_entry = Path(entry.path)
                    destination_entry = destination / entry.name

                    if (
                        entry.is_symlink()
                        or source_entry.is_junction()
                    ):
                        raise ExecutionError(
                            "Symbolic links and junctions are not allowed: "
                            f"{source_entry}"
                        )

                    entry_stat = entry.stat(follow_symlinks=False)

                    if stat.S_ISDIR(entry_stat.st_mode):
                        self._copy_directory(
                            source=source_entry,
                            destination=destination_entry,
                        )

                    elif stat.S_ISREG(entry_stat.st_mode):
                        shutil.copyfile(
                            source_entry,
                            destination_entry,
                            follow_symlinks=False,
                        )

                    else:
                        raise ExecutionError(
                            f"Unsupported special file: {source_entry}"
                        )

        except Exception:
            shutil.rmtree(destination, ignore_errors=True)
            raise