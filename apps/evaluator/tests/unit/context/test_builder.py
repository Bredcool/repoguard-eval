"""Tests for repository context preparation."""

from pathlib import Path

import pytest

from repoguard_eval.context import (
    ContextLimits,
    RepositoryContextBuilder,
)
from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution import WorkspaceManager


@pytest.fixture
def workspace_manager(tmp_path: Path) -> WorkspaceManager:
    return WorkspaceManager(tmp_path / "workspaces")


@pytest.fixture
def repository_workspace(
    workspace_manager: WorkspaceManager,
) -> tuple:
    workspace = workspace_manager.create()
    repository = workspace.path / "repository"
    repository.mkdir()

    (repository / "go.mod").write_text(
        "module example.com/app\n\ngo 1.23\n",
        encoding="utf-8",
    )

    order = repository / "order"
    order.mkdir()

    (order / "service.go").write_text(
        "package order\n\nfunc Create() error { return nil }\n",
        encoding="utf-8",
    )

    (order / "service_test.go").write_text(
        "package order\n\nfunc TestCreate() {}\n",
        encoding="utf-8",
    )

    return workspace, repository


def test_build_reads_repository_files(
    workspace_manager: WorkspaceManager,
    repository_workspace: tuple,
) -> None:
    workspace, _ = repository_workspace
    builder = RepositoryContextBuilder(workspace_manager)

    context = builder.build(workspace)

    assert context.file_count == 3
    assert context.total_bytes > 0

    paths = [item.path for item in context.files]

    assert paths == [
        "go.mod",
        "order/service.go",
        "order/service_test.go",
    ]


def test_build_preserves_file_content(
    workspace_manager: WorkspaceManager,
    repository_workspace: tuple,
) -> None:
    workspace, _ = repository_workspace

    context = RepositoryContextBuilder(
        workspace_manager
    ).build(workspace)

    service_file = next(
        item
        for item in context.files
        if item.path == "order/service.go"
    )

    assert "func Create()" in service_file.content
    assert service_file.size_bytes == len(
        service_file.content.encode("utf-8")
    )


def test_build_ignores_unallowed_files(
    workspace_manager: WorkspaceManager,
    repository_workspace: tuple,
) -> None:
    workspace, repository = repository_workspace

    (repository / "image.png").write_bytes(b"\x89PNG")
    (repository / "notes.log").write_text("ignored")
    (repository / ".env").write_text("API_KEY=secret")

    context = RepositoryContextBuilder(
        workspace_manager
    ).build(workspace)

    paths = {item.path for item in context.files}

    assert "image.png" not in paths
    assert "notes.log" not in paths
    assert ".env" not in paths


def test_build_ignores_sensitive_environment_files(
    workspace_manager: WorkspaceManager,
    repository_workspace: tuple,
) -> None:
    workspace, repository = repository_workspace

    (repository / ".env.production").write_text(
        "SECRET=example",
        encoding="utf-8",
    )

    context = RepositoryContextBuilder(
        workspace_manager
    ).build(workspace)

    paths = {item.path for item in context.files}

    assert ".env.production" not in paths


def test_build_ignores_excluded_directories(
    workspace_manager: WorkspaceManager,
    repository_workspace: tuple,
) -> None:
    workspace, repository = repository_workspace

    ignored = repository / "node_modules"
    ignored.mkdir()

    (ignored / "package.json").write_text(
        '{"name": "ignored"}',
        encoding="utf-8",
    )

    context = RepositoryContextBuilder(
        workspace_manager
    ).build(workspace)

    paths = {item.path for item in context.files}

    assert not any(
        path.startswith("node_modules/")
        for path in paths
    )


def test_build_ignores_binary_content(
    workspace_manager: WorkspaceManager,
    repository_workspace: tuple,
) -> None:
    workspace, repository = repository_workspace

    (repository / "binary.go").write_bytes(
        b"package main\x00binary-data"
    )

    context = RepositoryContextBuilder(
        workspace_manager
    ).build(workspace)

    paths = {item.path for item in context.files}

    assert "binary.go" not in paths


def test_build_respects_max_file_limit(
    workspace_manager: WorkspaceManager,
    repository_workspace: tuple,
) -> None:
    workspace, _ = repository_workspace

    builder = RepositoryContextBuilder(
        workspace_manager,
        ContextLimits(max_files=2),
    )

    context = builder.build(workspace)

    assert context.file_count == 2
    assert context.skipped_files == 1


def test_build_respects_max_single_file_size(
    workspace_manager: WorkspaceManager,
    repository_workspace: tuple,
) -> None:
    workspace, repository = repository_workspace

    (repository / "large.go").write_text(
        "x" * 100,
        encoding="utf-8",
    )

    builder = RepositoryContextBuilder(
        workspace_manager,
        ContextLimits(max_file_bytes=80),
    )

    context = builder.build(workspace)

    paths = {item.path for item in context.files}

    assert "large.go" not in paths
    assert context.skipped_files == 1


def test_build_respects_total_context_size(
    workspace_manager: WorkspaceManager,
    repository_workspace: tuple,
) -> None:
    workspace, repository = repository_workspace

    (repository / "a.go").write_text(
        "a" * 20,
        encoding="utf-8",
    )
    (repository / "b.go").write_text(
        "b" * 20,
        encoding="utf-8",
    )

    builder = RepositoryContextBuilder(
        workspace_manager,
        ContextLimits(max_total_bytes=25),
    )

    context = builder.build(workspace)

    assert context.total_bytes <= 25
    assert context.skipped_files >= 1


def test_build_is_deterministic(
    workspace_manager: WorkspaceManager,
    repository_workspace: tuple,
) -> None:
    workspace, _ = repository_workspace
    builder = RepositoryContextBuilder(workspace_manager)

    first = builder.build(workspace)
    second = builder.build(workspace)

    assert first == second


def test_build_rejects_missing_repository_directory(
    workspace_manager: WorkspaceManager,
) -> None:
    workspace = workspace_manager.create()

    with pytest.raises(
        ExecutionError,
        match="repository directory is invalid",
    ):
        RepositoryContextBuilder(
            workspace_manager
        ).build(workspace)

    workspace_manager.cleanup(workspace)


@pytest.mark.parametrize(
    "limits",
    [
        {"max_files": 0},
        {"max_file_bytes": 0},
        {"max_total_bytes": 0},
    ],
)
def test_context_limits_reject_non_positive_values(
    limits: dict[str, int],
) -> None:
    with pytest.raises(ValueError):
        ContextLimits(**limits)


@pytest.mark.parametrize(
    "filename",
    [
        "credentials.json",
        "service-account.json",
        "token.json",
        ".npmrc",
        ".pypirc",
        "private.pem",
        "private.key",
        "certificate.p12",
    ],
)
def test_build_ignores_sensitive_files(
    workspace_manager: WorkspaceManager,
    repository_workspace: tuple,
    filename: str,
) -> None:
    workspace, repository = repository_workspace

    (repository / filename).write_text(
        "SENSITIVE=example",
        encoding="utf-8",
    )

    context = RepositoryContextBuilder(
        workspace_manager
    ).build(workspace)

    paths = {item.path for item in context.files}

    assert filename not in paths