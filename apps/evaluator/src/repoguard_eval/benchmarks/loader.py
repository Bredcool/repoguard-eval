"""Prepare agent-visible benchmark workspaces."""

import shutil
import stat
from pathlib import Path

from repoguard_eval.benchmarks.registry import BenchmarkRegistry
from repoguard_eval.exceptions import TaskLoadError
from repoguard_eval.execution.fixtures import FixtureManager
from repoguard_eval.execution.workspace import Workspace, WorkspaceManager
from repoguard_eval.tasks.loader import load_task


class BenchmarkLoader:
    """Load benchmark tasks and prepare isolated public workspaces."""

    _PRIVATE_DIRECTORIES = {"hidden", "regression", "reference"}

    def __init__(
        self,
        registry: BenchmarkRegistry,
        workspace_manager: WorkspaceManager,
        fixture_manager: FixtureManager,
    ) -> None:
        self.registry = registry
        self.workspace_manager = workspace_manager
        self.fixture_manager = fixture_manager

    @staticmethod
    def _validate_public_file(task_dir: Path, filename: str) -> Path:
        path = task_dir / filename

        try:
            if path.is_symlink() or path.is_junction():
                raise TaskLoadError(
                    f"Benchmark metadata must not be a link: {filename}"
                )

            file_stat = path.lstat()

            if not stat.S_ISREG(file_stat.st_mode):
                raise TaskLoadError(
                    f"Benchmark metadata must be a regular file: {filename}"
                )

            resolved = path.resolve(strict=True)
            resolved.relative_to(task_dir)

            return resolved

        except TaskLoadError:
            raise
        except (OSError, ValueError) as exc:
            raise TaskLoadError(
                f"Invalid benchmark metadata file: {filename}"
            ) from exc

    def load(self, task_id: str):
        entry = self.registry.get(task_id)
        task_dir = self.registry.task_directory(entry)

        task_file = self._validate_public_file(task_dir, "task.json")
        self._validate_public_file(task_dir, "README.md")

        task = load_task(task_file)

        if task.id != entry.id:
            raise TaskLoadError(
                "Manifest task ID does not match task definition."
            )

        return task

    def prepare_agent_workspace(
        self,
        task_id: str,
        workspace: Workspace,
    ) -> Path:
        entry = self.registry.get(task_id)
        task_dir = self.registry.task_directory(entry)
        task = self.load(task_id)

        task_dir = task_dir.resolve(strict=True)
        repository_relative = Path(task.repository.path)

        if (
            repository_relative.is_absolute()
            or ".." in repository_relative.parts
            or not repository_relative.parts
            or any(
                part.casefold() in self._PRIVATE_DIRECTORIES
                for part in repository_relative.parts
            )
        ):
            raise TaskLoadError("Invalid repository fixture path.")

        repository_source = task_dir / repository_relative

        try:
            repository_source = repository_source.resolve(strict=True)
            repository_source.relative_to(task_dir)
        except (OSError, ValueError) as exc:
            raise TaskLoadError(
                "Repository fixture is outside task directory."
            ) from exc

        if not repository_source.is_dir():
            raise TaskLoadError("Repository fixture is not a directory.")

        workspace_path = self.workspace_manager.validate_workspace(workspace)

        metadata_files = {
            "task.json": self._validate_public_file(task_dir, "task.json"),
            "README.md": self._validate_public_file(task_dir, "README.md"),
        }

        for filename in metadata_files:
            target = workspace_path / filename
            if target.exists() or target.is_symlink() or target.is_junction():
                raise TaskLoadError(
                    f"Workspace metadata destination already exists: {filename}"
                )

        destination = self.fixture_manager.copy_fixture(
            source=repository_source,
            workspace=workspace,
        )

        copied_files: list[Path] = []

        try:
            for filename, source in metadata_files.items():
                target = workspace_path / filename
                copied_files.append(target)
                shutil.copyfile(source, target)

            return destination

        except OSError as exc:
            for copied_file in copied_files:
                copied_file.unlink(missing_ok=True)

            shutil.rmtree(destination, ignore_errors=True)

            raise TaskLoadError(
                f"Unable to prepare benchmark workspace: {exc}"
            ) from exc
