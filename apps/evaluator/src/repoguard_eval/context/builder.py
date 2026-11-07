"""Build safe, deterministic context from an agent workspace."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.workspace import (
    Workspace,
    WorkspaceManager,
)
from repoguard_eval.context.schemas import (
    RepositoryContext,
    RepositoryFile,
)


@dataclass(frozen=True, slots=True)
class ContextLimits:
    """Resource limits applied during repository scanning."""

    max_files: int = 100
    max_file_bytes: int = 64 * 1024
    max_total_bytes: int = 512 * 1024

    def __post_init__(self) -> None:
        if self.max_files <= 0:
            raise ValueError("max_files must be greater than zero.")

        if self.max_file_bytes <= 0:
            raise ValueError(
                "max_file_bytes must be greater than zero."
            )

        if self.max_total_bytes <= 0:
            raise ValueError(
                "max_total_bytes must be greater than zero."
            )


class RepositoryContextBuilder:
    """Read selected text files from an isolated agent workspace."""

    _ALLOWED_EXTENSIONS = {
        ".c",
        ".cc",
        ".cpp",
        ".cs",
        ".css",
        ".go",
        ".h",
        ".hpp",
        ".html",
        ".java",
        ".js",
        ".jsx",
        ".json",
        ".kt",
        ".md",
        ".mod",
        ".php",
        ".py",
        ".rb",
        ".rs",
        ".sh",
        ".sql",
        ".sum",
        ".swift",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".xml",
        ".yaml",
        ".yml",
    }

    _ALLOWED_FILENAMES = {
        ".dockerignore",
        ".editorconfig",
        ".gitignore",
        "dockerfile",
        "makefile",
    }

    _IGNORED_DIRECTORIES = {
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "vendor",
    }

    _IGNORED_FILENAMES = {
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        ".env.test",
        ".env.staging",
        ".envrc",
        ".netrc",
        ".npmrc",
        ".pypirc",
        "id_rsa",
        "id_ed25519",
        "id_ecdsa",
        "id_dsa",
        "known_hosts",
        "credentials",
        "credentials.json",
        "secrets.json",
        "service-account.json",
        "serviceaccount.json",
        "token.json",
    }

    _SENSITIVE_EXTENSIONS = {
        ".pem",
        ".key",
        ".p12",
        ".pfx",
        ".keystore",
        ".jks",
    }

    def __init__(
        self,
        workspace_manager: WorkspaceManager,
        limits: ContextLimits | None = None,
    ) -> None:
        self.workspace_manager = workspace_manager
        self.limits = limits or ContextLimits()

    @classmethod
    def _is_allowed_file(cls, path: Path) -> bool:
        if path.suffix.casefold() in cls._SENSITIVE_EXTENSIONS:
            return False

        """Check whether a filename is eligible for context."""

        filename = path.name.casefold()

        if filename in cls._IGNORED_FILENAMES:
            return False

        if filename.startswith(".env."):
            return False

        if filename in cls._ALLOWED_FILENAMES:
            return True

        return path.suffix.casefold() in cls._ALLOWED_EXTENSIONS

    @classmethod
    def _is_ignored_directory(cls, name: str) -> bool:
        """Check whether a directory should be excluded."""

        return name.casefold() in cls._IGNORED_DIRECTORIES

    @staticmethod
    def _is_inside_root(path: Path, root: Path) -> bool:
        """Check that a resolved path remains inside repository root."""

        try:
            path.resolve(strict=True).relative_to(root)
            return True
        except (OSError, ValueError):
            return False

    def _collect_files(self, root: Path) -> list[Path]:
        """Collect eligible regular files in deterministic order."""

        collected: list[Path] = []
        directories = [root]

        while directories:
            current = directories.pop()

            try:
                with os.scandir(current) as entries:
                    ordered_entries = sorted(
                        entries,
                        key=lambda entry: (entry.name.casefold(), entry.name),
                    )

                child_directories: list[Path] = []

                for entry in ordered_entries:
                    path = Path(entry.path)

                    if entry.is_symlink() or path.is_junction():
                        continue

                    try:
                        entry_stat = entry.stat(
                            follow_symlinks=False
                        )
                    except OSError:
                        continue

                    if stat.S_ISDIR(entry_stat.st_mode):
                        if not self._is_ignored_directory(entry.name):
                            child_directories.append(path)

                    elif stat.S_ISREG(entry_stat.st_mode):
                        if self._is_allowed_file(path):
                            collected.append(path)

            except OSError:
                continue

            directories.extend(reversed(child_directories))

        return sorted(
            collected,
            key=lambda path: (
                path.relative_to(root).as_posix().casefold(),
                path.relative_to(root).as_posix(),
            ),
        )

    def build(self, workspace: Workspace) -> RepositoryContext:
        """Build repository context from a validated agent workspace."""

        try:
            workspace_path = self.workspace_manager.validate_workspace(
                workspace
            )

            repository_root = workspace_path / "repository"

            if (
                repository_root.is_symlink()
                or repository_root.is_junction()
                or not repository_root.is_dir()
            ):
                raise ExecutionError(
                    "Agent repository directory is invalid."
                )

            repository_root = repository_root.resolve(strict=True)
            repository_root.relative_to(workspace_path)

            candidate_files = self._collect_files(repository_root)

            included_files: list[RepositoryFile] = []
            total_bytes = 0
            skipped_files = 0

            for path in candidate_files:
                if len(included_files) >= self.limits.max_files:
                    skipped_files += 1
                    continue

                try:
                    if (
                        path.is_symlink()
                        or path.is_junction()
                        or not self._is_inside_root(
                            path,
                            repository_root,
                        )
                    ):
                        skipped_files += 1
                        continue

                    file_stat = path.stat()

                    if not stat.S_ISREG(file_stat.st_mode):
                        skipped_files += 1
                        continue

                    if file_stat.st_size > self.limits.max_file_bytes:
                        skipped_files += 1
                        continue

                    if (
                        total_bytes + file_stat.st_size
                        > self.limits.max_total_bytes
                    ):
                        skipped_files += 1
                        continue

                    content_bytes = path.read_bytes()

                    if len(content_bytes) > self.limits.max_file_bytes:
                        skipped_files += 1
                        continue

                    if b"\x00" in content_bytes:
                        skipped_files += 1
                        continue

                    try:
                        content = content_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        skipped_files += 1
                        continue

                    relative_path = path.relative_to(
                        repository_root
                    ).as_posix()

                    included_files.append(
                        RepositoryFile(
                            path=relative_path,
                            content=content,
                            size_bytes=len(content_bytes),
                        )
                    )

                    total_bytes += len(content_bytes)

                except OSError:
                    skipped_files += 1

            return RepositoryContext(
                files=tuple(included_files),
                total_bytes=total_bytes,
                skipped_files=skipped_files,
            )

        except ExecutionError:
            raise
        except (OSError, ValueError) as exc:
            raise ExecutionError(
                f"Unable to build repository context: {exc}"
            ) from exc