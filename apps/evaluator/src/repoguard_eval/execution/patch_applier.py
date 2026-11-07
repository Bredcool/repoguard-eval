"""Safely apply validated patches to repository workspaces."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import uuid
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.patches import Patch, ValidatedPatch
from repoguard_eval.execution.patch_validator import PatchValidator
from repoguard_eval.execution.snapshots import (
    RepositorySnapshot,
    SnapshotManager,
)
from repoguard_eval.execution.workspace import (
    Workspace,
    WorkspaceManager,
)


@dataclass(frozen=True, slots=True)
class PatchApplicationResult:
    """Describe a successfully applied repository patch."""

    repository_path: Path
    changed_files: tuple[str, ...]
    snapshot: RepositorySnapshot
    backup_cleanup_pending: bool = False


class PatchApplier:
    """Apply validated patches through an isolated staging directory."""

    _DEFAULT_TIMEOUT = 10
    _MAX_ERROR_OUTPUT = 1000
    _HUNK_PATTERN = re.compile(
        r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@"
    )

    def __init__(
        self,
        workspace_manager: WorkspaceManager,
        patch_validator: PatchValidator,
        snapshot_manager: SnapshotManager | None = None,
    ) -> None:
        if not isinstance(workspace_manager, WorkspaceManager):
            raise ExecutionError("Invalid workspace manager.")

        if not isinstance(patch_validator, PatchValidator):
            raise ExecutionError("Invalid patch validator.")

        if snapshot_manager is not None and not isinstance(
            snapshot_manager,
            SnapshotManager,
        ):
            raise ExecutionError("Invalid snapshot manager.")

        self.workspace_manager = workspace_manager
        self.patch_validator = patch_validator
        self.snapshot_manager = snapshot_manager or SnapshotManager(
            workspace_manager
        )

    def apply(
        self,
        workspace: Workspace,
        patch: ValidatedPatch,
        repository_name: str = "repository",
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> PatchApplicationResult:
        """Apply a patch and promote the verified staging repository."""

        workspace_path = self.workspace_manager.validate_workspace(workspace)

        if not isinstance(patch, ValidatedPatch):
            raise ExecutionError("Invalid validated patch.")

        if (
            not isinstance(timeout, int)
            or isinstance(timeout, bool)
            or timeout <= 0
        ):
            raise ExecutionError("Patch application timeout must be positive.")

        validated_patch = self.patch_validator.validate(
            workspace,
            Patch(patch.content),
            repository_name,
        )
        normalized_content = self._normalize_patch_paths(validated_patch)

        baseline = self.snapshot_manager.create_snapshot(
            workspace,
            repository_name,
        )
        repository = baseline.repository_path

        token = uuid.uuid4().hex
        staging = workspace_path / f"repoguard-stage-{token}"
        backup = workspace_path / f"repoguard-backup-{token}"

        try:
            shutil.copytree(repository, staging)

            self._run_git_apply(
                staging,
                normalized_content,
                timeout,
                check_only=True,
            )
            self._run_git_apply(
                staging,
                normalized_content,
                timeout,
                check_only=False,
            )

            staged_snapshot = self.snapshot_manager.create_snapshot(
                workspace,
                staging.name,
            )

            changed_files = self._verify_allowed_changes(
                baseline,
                staged_snapshot,
                validated_patch,
            )

            if not self.snapshot_manager.verify_snapshot(
                workspace,
                baseline,
            ):
                raise ExecutionError(
                    "Original repository changed during patch application."
                )

            self._promote(staging, repository, backup)

            try:
                shutil.rmtree(backup, ignore_errors=True)
            except OSError:
                pass

            backup_cleanup_pending = backup.exists()

            result_snapshot = replace(
                staged_snapshot,
                repository_path=repository,
            )

            return PatchApplicationResult(
                repository_path=repository,
                changed_files=changed_files,
                snapshot=result_snapshot,
                backup_cleanup_pending=backup_cleanup_pending,
            )

        except ExecutionError:
            raise
        except (OSError, shutil.Error) as exc:
            raise ExecutionError(
                f"Unable to apply repository patch: {exc}"
            ) from exc
        finally:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)

    def _normalize_patch_paths(
        self,
        patch: ValidatedPatch,
    ) -> str:
        """Normalize file headers to Git's standard a/ and b/ prefixes."""

        lines = patch.content.splitlines(keepends=True)
        normalized = []
        file_index = 0
        index = 0
        remaining_old = 0
        remaining_new = 0

        while index < len(lines):
            line = lines[index]
            stripped = line.rstrip("\r\n")

            if remaining_old == 0 and remaining_new == 0:
                if (
                    stripped.startswith("--- ")
                    and index + 1 < len(lines)
                    and lines[index + 1].startswith("+++ ")
                ):
                    if file_index >= len(patch.files):
                        raise ExecutionError(
                            "Patch file headers do not match validated files."
                        )

                    patch_file = patch.files[file_index]
                    old_path = (
                        "/dev/null"
                        if patch_file.old_path is None
                        else f"a/{patch_file.old_path}"
                    )
                    new_path = (
                        "/dev/null"
                        if patch_file.new_path is None
                        else f"b/{patch_file.new_path}"
                    )

                    newline = "\r\n" if line.endswith("\r\n") else "\n"
                    next_line = lines[index + 1]
                    next_newline = (
                        "\r\n"
                        if next_line.endswith("\r\n")
                        else "\n"
                    )

                    normalized.append(f"--- {old_path}{newline}")
                    normalized.append(f"+++ {new_path}{next_newline}")

                    file_index += 1
                    index += 2
                    continue

                match = self._HUNK_PATTERN.match(stripped)

                if match:
                    remaining_old = (
                        int(match.group(1))
                        if match.group(1) is not None
                        else 1
                    )
                    remaining_new = (
                        int(match.group(2))
                        if match.group(2) is not None
                        else 1
                    )
                    normalized.append(line)
                    index += 1
                    continue

            if remaining_old or remaining_new:
                if stripped.startswith(" ") and remaining_old and remaining_new:
                    remaining_old -= 1
                    remaining_new -= 1
                elif stripped.startswith("-") and remaining_old:
                    remaining_old -= 1
                elif stripped.startswith("+") and remaining_new:
                    remaining_new -= 1
                elif stripped.startswith("\\"):
                    pass
                elif stripped:
                    raise ExecutionError(
                        "Malformed patch hunk during path normalization."
                    )

            normalized.append(line)
            index += 1

        if file_index != len(patch.files):
            raise ExecutionError(
                "Patch file headers do not match validated files."
            )

        return "".join(normalized)

    def _run_git_apply(
        self,
        repository: Path,
        patch_content: str,
        timeout: int,
        check_only: bool,
    ) -> None:
        command = ["git", "apply"]

        if check_only:
            command.append("--check")

        command.append("--")

        try:
            result = subprocess.run(
                command,
                input=patch_content.encode("utf-8"),
                cwd=repository,
                capture_output=True,
                timeout=timeout,
                check=False,
            )

        except subprocess.TimeoutExpired as exc:
            raise ExecutionError(
                "Git patch application exceeded its timeout."
            ) from exc
        except OSError as exc:
            raise ExecutionError(
                f"Unable to execute Git patch engine: {exc}"
            ) from exc

        if result.returncode != 0:
            error = result.stderr.decode(
                "utf-8",
                errors="replace",
            )[: self._MAX_ERROR_OUTPUT]

            action = "check" if check_only else "application"
            raise ExecutionError(
                f"Git patch {action} failed: {error.strip()}"
            )

    def _verify_allowed_changes(
        self,
        baseline: RepositorySnapshot,
        staged: RepositorySnapshot,
        patch: ValidatedPatch,
    ) -> tuple[str, ...]:
        baseline_entries = {
            entry.path: entry
            for entry in baseline.entries
        }
        staged_entries = {
            entry.path: entry
            for entry in staged.entries
        }

        changed_paths = {
            path
            for path in baseline_entries.keys() | staged_entries.keys()
            if baseline_entries.get(path) != staged_entries.get(path)
        }

        allowed_files = {
            path
            for patch_file in patch.files
            for path in (patch_file.old_path, patch_file.new_path)
            if path is not None
        }

        allowed_directories = {
            parent.as_posix()
            for path in allowed_files
            for parent in PurePosixPath(path).parents
            if parent.as_posix() != "."
        }

        changed_files = []
        unexpected_paths = []

        for path in changed_paths:
            baseline_entry = baseline_entries.get(path)
            staged_entry = staged_entries.get(path)
            entry = staged_entry or baseline_entry

            if entry is None:
                unexpected_paths.append(path)
                continue

            if entry.kind == "file":
                if path not in allowed_files:
                    unexpected_paths.append(path)
                else:
                    changed_files.append(path)
            elif (
                entry.kind == "directory"
                and path not in allowed_directories
            ):
                unexpected_paths.append(path)

        if unexpected_paths:
            raise ExecutionError(
                "Patch modified paths outside its declared targets: "
                + ", ".join(sorted(unexpected_paths))
            )

        return tuple(sorted(changed_files))

    def _promote(
        self,
        staging: Path,
        repository: Path,
        backup: Path,
    ) -> None:
        """Replace the repository and restore its backup on failure."""

        try:
            os.replace(repository, backup)
            os.replace(staging, repository)

        except OSError as exc:
            if backup.exists() and not repository.exists():
                try:
                    os.replace(backup, repository)
                except OSError as rollback_error:
                    raise ExecutionError(
                        "Patch promotion failed and repository rollback "
                        f"also failed: {rollback_error}"
                    ) from rollback_error

            raise ExecutionError(
                f"Unable to promote patched repository: {exc}"
            ) from exc
