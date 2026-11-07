"""Tests for execution workspace management."""

from pathlib import Path
from uuid import uuid4

import pytest

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution import Workspace, WorkspaceManager


def test_create_workspace(tmp_path: Path) -> None:
    """Manager should create a unique workspace."""

    manager = WorkspaceManager(tmp_path / "workspaces")

    workspace = manager.create()

    assert workspace.path.is_dir()
    assert workspace.path.parent == manager.root
    assert workspace.path.name == f"job-{workspace.job_id}"

    manager.cleanup(workspace)


def test_create_multiple_workspaces(tmp_path: Path) -> None:
    """Each job should receive a different workspace."""

    manager = WorkspaceManager(tmp_path / "workspaces")

    first = manager.create()
    second = manager.create()

    assert first.job_id != second.job_id
    assert first.path != second.path
    assert first.path.is_dir()
    assert second.path.is_dir()

    manager.cleanup(first)
    manager.cleanup(second)


def test_workspace_root_is_created(tmp_path: Path) -> None:
    """Manager should create a missing workspace root."""

    root = tmp_path / "nested" / "workspaces"

    manager = WorkspaceManager(root)

    assert manager.root.is_dir()


def test_cleanup_removes_workspace(tmp_path: Path) -> None:
    """Cleanup should remove the selected workspace."""

    manager = WorkspaceManager(tmp_path / "workspaces")
    workspace = manager.create()

    (workspace.path / "example.txt").write_text(
        "temporary data",
        encoding="utf-8",
    )

    manager.cleanup(workspace)

    assert not workspace.path.exists()


def test_cleanup_is_idempotent(tmp_path: Path) -> None:
    """Cleaning an already removed workspace should be safe."""

    manager = WorkspaceManager(tmp_path / "workspaces")
    workspace = manager.create()

    manager.cleanup(workspace)
    manager.cleanup(workspace)

    assert not workspace.path.exists()


def test_cleanup_preserves_other_workspaces(tmp_path: Path) -> None:
    """Cleanup must not remove another job's workspace."""

    manager = WorkspaceManager(tmp_path / "workspaces")

    first = manager.create()
    second = manager.create()

    manager.cleanup(first)

    assert not first.path.exists()
    assert second.path.is_dir()

    manager.cleanup(second)


def test_cleanup_rejects_invalid_workspace_object(
    tmp_path: Path,
) -> None:
    """Cleanup should reject arbitrary objects."""

    manager = WorkspaceManager(tmp_path / "workspaces")

    with pytest.raises(ExecutionError, match="Invalid workspace"):
        manager.cleanup("not-a-workspace")  # type: ignore[arg-type]


def test_cleanup_rejects_invalid_job_id(
    tmp_path: Path,
) -> None:
    """Cleanup should reject malformed job identifiers."""

    manager = WorkspaceManager(tmp_path / "workspaces")

    workspace = Workspace(
        job_id="invalid-id",
        path=manager.root / "job-invalid-id",
    )

    with pytest.raises(ExecutionError):
        manager.cleanup(workspace)


def test_cleanup_rejects_path_outside_root(
    tmp_path: Path,
) -> None:
    """Cleanup must not remove a directory outside the managed root."""

    manager = WorkspaceManager(tmp_path / "workspaces")
    outside = tmp_path / "outside"

    outside.mkdir()

    workspace = Workspace(
        job_id=str(uuid4()),
        path=outside,
    )

    with pytest.raises(ExecutionError, match="does not match"):
        manager.cleanup(workspace)

    assert outside.is_dir()


def test_workspace_root_rejects_file(tmp_path: Path) -> None:
    """A regular file cannot be used as the workspace root."""

    root = tmp_path / "not-a-directory"
    root.write_text("file", encoding="utf-8")

    with pytest.raises(ExecutionError):
        WorkspaceManager(root)


def test_workspace_root_rejects_symlink(tmp_path: Path) -> None:
    """A symlink cannot be used as the workspace root."""

    actual_root = tmp_path / "actual"
    actual_root.mkdir()

    symlink_root = tmp_path / "linked"

    try:
        symlink_root.symlink_to(actual_root, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Directory symlinks are unavailable: {exc}")

    with pytest.raises(ExecutionError, match="symbolic link"):
        WorkspaceManager(symlink_root)


def test_validate_workspace_rejects_path_outside_root(
    tmp_path: Path,
) -> None:
    """Workspace validation must reject paths outside the managed root."""

    manager = WorkspaceManager(tmp_path / "workspaces")
    outside = tmp_path / "outside"
    outside.mkdir()

    job_id = str(uuid4())

    workspace = Workspace(
        job_id=job_id,
        path=outside / f"job-{job_id}",
    )

    with pytest.raises(
        ExecutionError,
        match="outside the managed workspace root",
    ):
        manager.validate_workspace(workspace)



def test_validate_workspace_rejects_invalid_job_id_type(
    tmp_path: Path,
) -> None:
    """Workspace validation must reject non-string job identifiers."""

    manager = WorkspaceManager(tmp_path / "workspaces")

    workspace = Workspace(
        job_id=None,  # type: ignore[arg-type]
        path=manager.root / "job-invalid",
    )

    with pytest.raises(ExecutionError, match="must be a string"):
        manager.validate_workspace(workspace)


def test_validate_workspace_rejects_invalid_path_type(
    tmp_path: Path,
) -> None:
    """Workspace validation must reject non-Path workspace paths."""

    manager = WorkspaceManager(tmp_path / "workspaces")
    job_id = str(uuid4())

    workspace = Workspace(
        job_id=job_id,
        path=None,  # type: ignore[arg-type]
    )

    with pytest.raises(ExecutionError, match="path must be"):
        manager.validate_workspace(workspace)


def test_validate_workspace_rejects_resolved_path_outside_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Resolved workspace paths must remain inside the managed root."""

    manager = WorkspaceManager(tmp_path / "workspaces")
    workspace = manager.create()

    outside = tmp_path / "outside"
    outside.mkdir()

    original_resolve = Path.resolve

    def fake_resolve(
        path: Path,
        strict: bool = False,
    ) -> Path:
        if path == workspace.path:
            return outside / workspace.path.name

        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", fake_resolve)

    with pytest.raises(
        ExecutionError,
        match="Resolved workspace is outside",
    ):
        manager.validate_workspace(workspace)


def test_workspace_root_rejects_invalid_input() -> None:
    from repoguard_eval.exceptions import ExecutionError

    with pytest.raises(ExecutionError, match="Invalid workspace root"):
        WorkspaceManager(None)  # type: ignore[arg-type]
