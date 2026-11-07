
"""Validate untrusted unified diff patches before application."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath, PureWindowsPath

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.patches import (
    Patch,
    PatchFile,
    ValidatedPatch,
)
from repoguard_eval.execution.workspace import (
    Workspace,
    WorkspaceManager,
)


class PatchValidator:
    """Validate patch structure, size, and target paths."""

    _MAX_PATCH_BYTES = 1024 * 1024
    _MAX_FILES = 100
    _HUNK_PATTERN = re.compile(
        r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?$"
    )
    _PATH_PATTERN = re.compile(r"^[A-Za-z0-9._/-]+$")

    def __init__(self, workspace_manager: WorkspaceManager) -> None:
        if not isinstance(workspace_manager, WorkspaceManager):
            raise ExecutionError("Invalid workspace manager.")

        self.workspace_manager = workspace_manager

    def validate(
        self,
        workspace: Workspace,
        patch: Patch,
        repository_name: str = "repository",
    ) -> ValidatedPatch:
        """Validate a unified diff without modifying the repository."""

        workspace_path = self.workspace_manager.validate_workspace(workspace)

        if not isinstance(patch, Patch):
            raise ExecutionError("Invalid patch.")

        if not isinstance(patch.content, str) or not patch.content:
            raise ExecutionError("Patch content must be a non-empty string.")

        try:
            content_bytes = patch.content.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ExecutionError("Patch content must be valid UTF-8.") from exc

        total_bytes = len(content_bytes)

        if total_bytes > self._MAX_PATCH_BYTES:
            raise ExecutionError("Patch exceeds the maximum allowed size.")

        repository = self._resolve_repository(
            workspace_path,
            repository_name,
        )

        files = self._parse_patch(patch.content)

        if len(files) > self._MAX_FILES:
            raise ExecutionError("Patch modifies too many files.")

        for patch_file in files:
            for target in (patch_file.old_path, patch_file.new_path):
                if target is not None:
                    self._validate_target(repository, target)

        return ValidatedPatch(
            content=patch.content,
            files=tuple(files),
            total_bytes=total_bytes,
        )

    def _resolve_repository(
        self,
        workspace_path: Path,
        repository_name: str,
    ) -> Path:
        if (
            not isinstance(repository_name, str)
            or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}",
                repository_name,
            )
        ):
            raise ExecutionError("Invalid repository directory name.")

        repository = workspace_path / repository_name

        try:
            if repository.is_symlink() or repository.is_junction():
                raise ExecutionError("Repository cannot be a symlink or junction.")

            resolved = repository.resolve(strict=True)

            if resolved.parent != workspace_path or not resolved.is_dir():
                raise ExecutionError("Invalid repository directory.")

            return resolved

        except ExecutionError:
            raise
        except OSError as exc:
            raise ExecutionError(
                f"Unable to resolve repository directory: {exc}"
            ) from exc

    def _parse_patch(self, content: str) -> list[PatchFile]:
        lines = content.splitlines()
        files: list[PatchFile] = []
        seen_targets: set[str] = set()
        index = 0

        while index < len(lines):
            line = lines[index]

            if line.startswith("diff --git "):
                raise ExecutionError("Git extended diff headers are not supported.")

            if line.startswith("GIT binary patch") or line.startswith("Binary files "):
                raise ExecutionError("Binary patches are not supported.")

            if line.startswith(("old mode ", "new mode ", "new file mode ", "deleted file mode ")):
                raise ExecutionError("File mode changes are not supported.")

            if not line.startswith("--- "):
                raise ExecutionError("Expected unified diff file header.")

            if index + 1 >= len(lines) or not lines[index + 1].startswith("+++ "):
                raise ExecutionError("Missing unified diff destination header.")

            old_path = self._parse_header_path(line[4:], "a")
            new_path = self._parse_header_path(lines[index + 1][4:], "b")

            if old_path is None and new_path is None:
                raise ExecutionError("Patch must target at least one file.")

            targets = {path for path in (old_path, new_path) if path is not None}

            if seen_targets.intersection(targets):
                raise ExecutionError("Patch contains duplicate file targets.")

            seen_targets.update(targets)

            index += 2
            hunk_count = 0

            while index < len(lines) and lines[index].startswith("@@ "):
                match = self._HUNK_PATTERN.fullmatch(lines[index])

                if match is None:
                    raise ExecutionError("Malformed unified diff hunk header.")

                old_expected = int(match.group(2) or "1")
                new_expected = int(match.group(4) or "1")

                old_count = 0
                new_count = 0
                index += 1

                while index < len(lines):
                    hunk_line = lines[index]

                    if hunk_line.startswith("@@ ") or (
                        hunk_line.startswith("--- ")
                        and old_count == old_expected
                        and new_count == new_expected
                    ):
                        break

                    if hunk_line == r"\ No newline at end of file":
                        index += 1
                        continue

                    if hunk_line.startswith(" "):
                        old_count += 1
                        new_count += 1
                    elif hunk_line.startswith("-"):
                        old_count += 1
                    elif hunk_line.startswith("+"):
                        new_count += 1
                    else:
                        raise ExecutionError("Invalid unified diff hunk line.")

                    if old_count > old_expected or new_count > new_expected:
                        raise ExecutionError("Unified diff hunk contains excess lines.")

                    index += 1

                if old_count != old_expected or new_count != new_expected:
                    raise ExecutionError("Unified diff hunk line counts do not match.")

                hunk_count += 1

            if hunk_count == 0:
                raise ExecutionError("Each patched file must contain at least one hunk.")

            files.append(
                PatchFile(
                    old_path=old_path,
                    new_path=new_path,
                )
            )

            if len(files) > self._MAX_FILES:
                raise ExecutionError("Patch modifies too many files.")

        if not files:
            raise ExecutionError("Patch contains no file changes.")

        return files


    def _parse_header_path(
        self,
        value: str,
        expected_prefix: str,
    ) -> str | None:
        """Parse and normalize a unified diff file header path."""

        path = value.split("\\t", 1)[0]

        if path == "/dev/null":
            return None

        if not path or not self._PATH_PATTERN.fullmatch(path):
            raise ExecutionError("Invalid patch target path.")

        if "\\" in path:
            raise ExecutionError("Backslashes are not allowed in patch paths.")

        prefix = f"{expected_prefix}/"
        if path.startswith(prefix):
            path = path[len(prefix):]

        if not path:
            raise ExecutionError("Invalid patch target path.")

        posix_path = PurePosixPath(path)
        windows_path = PureWindowsPath(path)

        if (
            posix_path.is_absolute()
            or windows_path.is_absolute()
            or windows_path.drive
            or any(part in ("", ".", "..") for part in path.split("/"))
        ):
            raise ExecutionError("Unsafe patch target path.")

        return path

    def _validate_target(self, repository: Path, target: str) -> None:
        """Ensure a patch target remains inside the repository."""

        relative_path = PurePosixPath(target)

        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ExecutionError("Patch target escapes the repository.")

        current = repository

        try:
            for part in relative_path.parts:
                current = current / part

                if current.is_symlink() or current.is_junction():
                    raise ExecutionError(
                        "Patch target cannot traverse a symlink or junction."
                    )

                if current.exists():
                    resolved = current.resolve(strict=True)

                    if not resolved.is_relative_to(repository):
                        raise ExecutionError(
                            "Patch target escapes the repository."
                        )

        except ExecutionError:
            raise
        except OSError as exc:
            raise ExecutionError(
                f"Unable to validate patch target: {exc}"
            ) from exc
