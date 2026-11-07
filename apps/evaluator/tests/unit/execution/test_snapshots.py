"""Tests for repository snapshot management."""

from pathlib import Path
from dataclasses import replace

import pytest

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution import (
    FixtureManager,
    SnapshotManager,
    WorkspaceManager,
)


@pytest.fixture
def snapshot_environment(tmp_path: Path):
    """Create an isolated workspace with a repository fixture."""

    workspace_manager = WorkspaceManager(tmp_path / "workspaces")
    fixture_manager = FixtureManager(workspace_manager)
    snapshot_manager = SnapshotManager(workspace_manager)

    workspace = workspace_manager.create()

    source = tmp_path / "source"
    source.mkdir()

    (source / "main.py").write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    (source / "src").mkdir()
    (source / "src" / "module.py").write_text(
        "VALUE = 42\n",
        encoding="utf-8",
    )

    fixture_manager.copy_fixture(source, workspace)

    return {
        "workspace_manager": workspace_manager,
        "workspace": workspace,
        "repository": workspace.path / "repository",
        "snapshot_manager": snapshot_manager,
    }


def test_create_snapshot_records_repository_entries(snapshot_environment):
    environment = snapshot_environment

    snapshot = environment["snapshot_manager"].create_snapshot(
        environment["workspace"]
    )

    entries = {entry.path: entry for entry in snapshot.entries}

    assert snapshot.job_id == environment["workspace"].job_id
    assert snapshot.snapshot_id
    assert "main.py" in entries
    assert "src" in entries
    assert "src/module.py" in entries

    assert entries["main.py"].kind == "file"
    assert entries["main.py"].size == (environment["repository"] / "main.py").stat().st_size
    assert len(entries["main.py"].sha256) == 64

    assert entries["src"].kind == "directory"
    assert entries["src/module.py"].kind == "file"


def test_snapshot_entries_are_deterministically_sorted(snapshot_environment):
    environment = snapshot_environment

    snapshot = environment["snapshot_manager"].create_snapshot(
        environment["workspace"]
    )

    paths = [entry.path for entry in snapshot.entries]

    assert paths == sorted(paths)


def test_verify_snapshot_returns_true_when_repository_is_unchanged(
    snapshot_environment,
):
    environment = snapshot_environment

    snapshot = environment["snapshot_manager"].create_snapshot(
        environment["workspace"]
    )

    assert environment["snapshot_manager"].verify_snapshot(
        environment["workspace"],
        snapshot,
    )


def test_verify_snapshot_detects_modified_file(snapshot_environment):
    environment = snapshot_environment

    snapshot = environment["snapshot_manager"].create_snapshot(
        environment["workspace"]
    )

    (environment["repository"] / "main.py").write_text(
        "print('modified')\n",
        encoding="utf-8",
    )

    assert not environment["snapshot_manager"].verify_snapshot(
        environment["workspace"],
        snapshot,
    )


def test_verify_snapshot_detects_new_file(snapshot_environment):
    environment = snapshot_environment

    snapshot = environment["snapshot_manager"].create_snapshot(
        environment["workspace"]
    )

    (environment["repository"] / "new.py").write_text(
        "NEW = True\n",
        encoding="utf-8",
    )

    assert not environment["snapshot_manager"].verify_snapshot(
        environment["workspace"],
        snapshot,
    )


def test_verify_snapshot_detects_deleted_file(snapshot_environment):
    environment = snapshot_environment

    snapshot = environment["snapshot_manager"].create_snapshot(
        environment["workspace"]
    )

    (environment["repository"] / "main.py").unlink()

    assert not environment["snapshot_manager"].verify_snapshot(
        environment["workspace"],
        snapshot,
    )


def test_verify_snapshot_detects_new_directory(snapshot_environment):
    environment = snapshot_environment

    snapshot = environment["snapshot_manager"].create_snapshot(
        environment["workspace"]
    )

    (environment["repository"] / "empty").mkdir()

    assert not environment["snapshot_manager"].verify_snapshot(
        environment["workspace"],
        snapshot,
    )


@pytest.mark.parametrize(
    "repository_name",
    [
        "",
        "../outside",
        ".",
        "..",
        "nested/repository",
        "repository/name",
    ],
)
def test_create_snapshot_rejects_invalid_repository_name(
    snapshot_environment,
    repository_name,
):
    environment = snapshot_environment

    with pytest.raises(ExecutionError):
        environment["snapshot_manager"].create_snapshot(
            environment["workspace"],
            repository_name=repository_name,
        )


def test_create_snapshot_rejects_missing_repository(
    snapshot_environment,
):
    environment = snapshot_environment

    with pytest.raises(ExecutionError):
        environment["snapshot_manager"].create_snapshot(
            environment["workspace"],
            repository_name="missing",
        )


def test_verify_snapshot_rejects_snapshot_from_another_workspace(
    snapshot_environment,
):
    environment = snapshot_environment

    snapshot = environment["snapshot_manager"].create_snapshot(
        environment["workspace"]
    )

    other_workspace = environment["workspace_manager"].create()

    with pytest.raises(ExecutionError):
        environment["snapshot_manager"].verify_snapshot(
            other_workspace,
            snapshot,
        )


def test_verify_snapshot_rejects_invalid_snapshot(
    snapshot_environment,
):
    environment = snapshot_environment

    with pytest.raises(ExecutionError):
        environment["snapshot_manager"].verify_snapshot(
            environment["workspace"],
            None,
        )


def test_create_snapshot_rejects_symbolic_link(
    snapshot_environment,
    tmp_path,
):
    environment = snapshot_environment

    target = tmp_path / "target.txt"
    target.write_text("external content", encoding="utf-8")

    link = environment["repository"] / "linked.txt"

    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symbolic link creation is unavailable: {exc}")

    with pytest.raises(ExecutionError):
        environment["snapshot_manager"].create_snapshot(
            environment["workspace"]
        )


def test_verify_snapshot_rejects_invalid_workspace(
    snapshot_environment,
):
    environment = snapshot_environment

    snapshot = environment["snapshot_manager"].create_snapshot(
        environment["workspace"]
    )

    with pytest.raises(ExecutionError):
        environment["snapshot_manager"].verify_snapshot(
            None,
            snapshot,
        )


def test_verify_snapshot_rejects_invalid_repository_path(
    snapshot_environment,
):
    environment = snapshot_environment

    snapshot = environment["snapshot_manager"].create_snapshot(
        environment["workspace"]
    )

    malformed_snapshot = replace(
        snapshot,
        repository_path="invalid-path",
    )

    with pytest.raises(ExecutionError):
        environment["snapshot_manager"].verify_snapshot(
            environment["workspace"],
            malformed_snapshot,
        )


def test_verify_snapshot_rejects_invalid_entries(
    snapshot_environment,
):
    environment = snapshot_environment

    snapshot = environment["snapshot_manager"].create_snapshot(
        environment["workspace"]
    )

    malformed_snapshot = replace(
        snapshot,
        entries=[],
    )

    with pytest.raises(ExecutionError):
        environment["snapshot_manager"].verify_snapshot(
            environment["workspace"],
            malformed_snapshot,
        )


def test_snapshot_detects_same_size_content_modification(
    snapshot_environment,
):
    environment = snapshot_environment

    snapshot = environment["snapshot_manager"].create_snapshot(
        environment["workspace"]
    )

    file_path = environment["repository"] / "main.py"
    original_content = file_path.read_bytes()

    modified_content = b"print('world')\r\n"
    assert len(modified_content) == len(original_content)

    file_path.write_bytes(modified_content)

    assert not environment["snapshot_manager"].verify_snapshot(
        environment["workspace"],
        snapshot,
    )


def test_snapshot_handles_empty_file(snapshot_environment):
    environment = snapshot_environment

    empty_file = environment["repository"] / "empty.txt"
    empty_file.write_bytes(b"")

    snapshot = environment["snapshot_manager"].create_snapshot(
        environment["workspace"]
    )

    entries = {entry.path: entry for entry in snapshot.entries}

    assert entries["empty.txt"].size == 0
    assert entries["empty.txt"].sha256 is not None
    assert len(entries["empty.txt"].sha256) == 64
