import json
from types import SimpleNamespace
from pathlib import Path
from repoguard_eval.context import RepositoryContextBuilder

import pytest

from repoguard_eval.benchmarks.registry import BenchmarkRegistry
from repoguard_eval.benchmarks.loader import BenchmarkLoader
from repoguard_eval.exceptions import TaskLoadError
from repoguard_eval.execution.fixtures import FixtureManager
from repoguard_eval.execution.workspace import WorkspaceManager
import repoguard_eval.benchmarks.loader as loader_module


@pytest.fixture
def benchmark_environment(tmp_path, monkeypatch):
    root = tmp_path / "benchmarks"
    task_dir = root / "packs" / "go" / "test" / "rg-test-001"
    repository = task_dir / "repository"

    (repository / "order").mkdir(parents=True)
    (repository / "order" / "service.go").write_text(
        "package order\n",
        encoding="utf-8",
    )

    (task_dir / "task.json").write_text(
        json.dumps({"id": "rg-test-001"}),
        encoding="utf-8",
    )
    (task_dir / "README.md").write_text(
        "# Test Task",
        encoding="utf-8",
    )

    for name in ("hidden", "regression", "reference"):
        private_dir = task_dir / name
        private_dir.mkdir()
        (private_dir / "secret.txt").write_text(
            "private data",
            encoding="utf-8",
        )

    (root / "manifest.json").write_text(
        json.dumps({
            "name": "Test Suite",
            "version": "1.0.0",
            "description": "Test benchmark",
            "tasks": [{
                "id": "rg-test-001",
                "pack": "go/test",
                "language": "go",
                "category": "testing",
                "difficulty": "medium",
                "version": "1.0.0",
                "status": "development",
            }],
        }),
        encoding="utf-8",
    )

    registry = BenchmarkRegistry(root)
    workspace_manager = WorkspaceManager(tmp_path / "workspaces")
    fixture_manager = FixtureManager(workspace_manager)
    loader = BenchmarkLoader(
        registry,
        workspace_manager,
        fixture_manager,
    )

    monkeypatch.setattr(
        loader_module,
        "load_task",
        lambda path: SimpleNamespace(
            id="rg-test-001",
            repository=SimpleNamespace(path="repository"),
        ),
    )

    return loader, workspace_manager, task_dir


def test_load_task(benchmark_environment):
    loader, _, _ = benchmark_environment

    task = loader.load("rg-test-001")

    assert task.id == "rg-test-001"
    assert task.repository.path == "repository"


def test_load_rejects_task_id_mismatch(
    benchmark_environment,
    monkeypatch,
):
    loader, _, _ = benchmark_environment

    monkeypatch.setattr(
        loader_module,
        "load_task",
        lambda path: SimpleNamespace(
            id="rg-other-001",
            repository=SimpleNamespace(path="repository"),
        ),
    )

    with pytest.raises(TaskLoadError, match="does not match"):
        loader.load("rg-test-001")


def test_prepare_agent_workspace_copies_only_public_files(
    benchmark_environment,
):
    loader, workspace_manager, _ = benchmark_environment
    workspace = workspace_manager.create()

    destination = loader.prepare_agent_workspace(
        "rg-test-001",
        workspace,
    )

    assert destination.is_dir()
    assert (destination / "order" / "service.go").is_file()
    assert (workspace.path / "task.json").is_file()
    assert (workspace.path / "README.md").is_file()

    for name in ("hidden", "regression", "reference"):
        assert not (workspace.path / name).exists()
        assert not (destination / name).exists()


def test_prepare_rejects_repository_path_traversal(
    benchmark_environment,
    monkeypatch,
):
    loader, workspace_manager, _ = benchmark_environment
    workspace = workspace_manager.create()

    monkeypatch.setattr(
        loader_module,
        "load_task",
        lambda path: SimpleNamespace(
            id="rg-test-001",
            repository=SimpleNamespace(path="../outside"),
        ),
    )

    with pytest.raises(TaskLoadError, match="Invalid repository fixture path"):
        loader.prepare_agent_workspace("rg-test-001", workspace)


def test_prepare_rejects_missing_repository(
    benchmark_environment,
    monkeypatch,
):
    loader, workspace_manager, task_dir = benchmark_environment
    workspace = workspace_manager.create()

    (task_dir / "repository").rename(task_dir / "repository-backup")

    with pytest.raises(TaskLoadError, match="Repository fixture"):
        loader.prepare_agent_workspace("rg-test-001", workspace)


def test_prepare_rejects_private_repository_directory(
    benchmark_environment,
    monkeypatch,
):
    loader, workspace_manager, task_dir = benchmark_environment
    workspace = workspace_manager.create()

    monkeypatch.setattr(
        loader_module,
        "load_task",
        lambda path: SimpleNamespace(
            id="rg-test-001",
            repository=SimpleNamespace(path="hidden"),
        ),
    )

    with pytest.raises(TaskLoadError, match="Invalid repository fixture path"):
        loader.prepare_agent_workspace("rg-test-001", workspace)


def test_prepare_rejects_task_directory_as_repository(
    benchmark_environment,
    monkeypatch,
):
    loader, workspace_manager, _ = benchmark_environment
    workspace = workspace_manager.create()

    monkeypatch.setattr(
        loader_module,
        "load_task",
        lambda path: SimpleNamespace(
            id="rg-test-001",
            repository=SimpleNamespace(path="."),
        ),
    )

    with pytest.raises(TaskLoadError, match="Invalid repository fixture path"):
        loader.prepare_agent_workspace("rg-test-001", workspace)


def test_load_rejects_directory_as_task_json(benchmark_environment):
    loader, _, task_dir = benchmark_environment

    (task_dir / "task.json").unlink()
    (task_dir / "task.json").mkdir()

    with pytest.raises(TaskLoadError, match="regular file"):
        loader.load("rg-test-001")


def test_load_rejects_directory_as_readme(benchmark_environment):
    loader, _, task_dir = benchmark_environment

    (task_dir / "README.md").unlink()
    (task_dir / "README.md").mkdir()

    with pytest.raises(TaskLoadError, match="regular file"):
        loader.load("rg-test-001")


def test_prepare_cleans_partial_workspace_on_copy_failure(
    benchmark_environment,
    monkeypatch,
):
    loader, workspace_manager, _ = benchmark_environment
    workspace = workspace_manager.create()

    original_copyfile = loader_module.shutil.copyfile

    def failing_copyfile(source, destination, *args, **kwargs):
        if Path(destination).name == "README.md":
            raise OSError("Simulated metadata copy failure")
        return original_copyfile(source, destination, *args, **kwargs)

    monkeypatch.setattr(loader_module.shutil, "copyfile", failing_copyfile)

    with pytest.raises(TaskLoadError, match="Unable to prepare"):
        loader.prepare_agent_workspace("rg-test-001", workspace)

    assert not (workspace.path / "repository").exists()
    assert not (workspace.path / "task.json").exists()
    assert not (workspace.path / "README.md").exists()


def test_repository_context_uses_prepared_agent_workspace(
    benchmark_environment,
):
    loader, workspace_manager, _ = benchmark_environment
    workspace = workspace_manager.create()

    try:
        loader.prepare_agent_workspace(
            "rg-test-001",
            workspace,
        )

        context_builder = RepositoryContextBuilder(
            workspace_manager,
        )

        context = context_builder.build(workspace)

        paths = {
            item.path
            for item in context.files
        }

        assert "order/service.go" in paths

        assert context.file_count == 1
        assert context.total_bytes > 0

        for private_directory in (
            "hidden",
            "reference",
            "regression",
        ):
            assert not any(
                path.startswith(f"{private_directory}/")
                for path in paths
            )

        service_file = next(
            item
            for item in context.files
            if item.path == "order/service.go"
        )

        assert "package order" in service_file.content

    finally:
        workspace_manager.cleanup(workspace)
