"""Tests for repository fixture preparation."""

import os
from pathlib import Path

import pytest

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution import FixtureManager, WorkspaceManager


@pytest.fixture
def workspace_manager(tmp_path: Path) -> WorkspaceManager:
    """Provide a workspace manager for fixture tests."""

    return WorkspaceManager(tmp_path / "workspaces")


@pytest.fixture
def fixture_source(tmp_path: Path) -> Path:
    """Create a sample repository fixture."""

    source = tmp_path / "fixture"
    source.mkdir()

    (source / "README.md").write_text(
        "# Example Repository",
        encoding="utf-8",
    )

    (source / "main.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    nested = source / "src"
    nested.mkdir()

    (nested / "module.py").write_text(
        "VALUE = 42",
        encoding="utf-8",
    )

    return source


def test_copy_fixture_success(
    workspace_manager: WorkspaceManager,
    fixture_source: Path,
) -> None:
    """Fixture files should be copied into the workspace."""

    workspace = workspace_manager.create()
    manager = FixtureManager(workspace_manager)

    destination = manager.copy_fixture(
        source=fixture_source,
        workspace=workspace,
    )

    assert destination.is_dir()
    assert (destination / "README.md").read_text(
        encoding="utf-8"
    ) == "# Example Repository"

    assert (destination / "main.py").read_text(
        encoding="utf-8"
    ) == "print('hello')"

    assert (destination / "src" / "module.py").read_text(
        encoding="utf-8"
    ) == "VALUE = 42"

    workspace_manager.cleanup(workspace)


def test_copy_fixture_preserves_source(
    workspace_manager: WorkspaceManager,
    fixture_source: Path,
) -> None:
    """Copying must not modify the source fixture."""

    workspace = workspace_manager.create()
    manager = FixtureManager(workspace_manager)

    original_content = (fixture_source / "main.py").read_text(
        encoding="utf-8"
    )

    manager.copy_fixture(fixture_source, workspace)

    assert (fixture_source / "main.py").read_text(
        encoding="utf-8"
    ) == original_content

    workspace_manager.cleanup(workspace)


def test_copy_fixture_supports_custom_destination(
    workspace_manager: WorkspaceManager,
    fixture_source: Path,
) -> None:
    """A valid custom destination name should be accepted."""

    workspace = workspace_manager.create()

    destination = FixtureManager(workspace_manager).copy_fixture(
        fixture_source,
        workspace,
        destination_name="baseline",
    )

    assert destination.name == "baseline"
    assert destination.is_dir()

    workspace_manager.cleanup(workspace)


def test_copy_fixture_rejects_missing_source(
    workspace_manager: WorkspaceManager,
    tmp_path: Path,
) -> None:
    """A missing fixture source should be rejected."""

    workspace = workspace_manager.create()

    with pytest.raises(ExecutionError):
        FixtureManager(workspace_manager).copy_fixture(
            tmp_path / "missing",
            workspace,
        )

    workspace_manager.cleanup(workspace)


def test_copy_fixture_rejects_file_source(
    workspace_manager: WorkspaceManager,
    tmp_path: Path,
) -> None:
    """A regular file cannot be used as a repository fixture."""

    source = tmp_path / "file.txt"
    source.write_text("not a repository", encoding="utf-8")

    workspace = workspace_manager.create()

    with pytest.raises(ExecutionError, match="directory"):
        FixtureManager(workspace_manager).copy_fixture(source, workspace)

    workspace_manager.cleanup(workspace)


@pytest.mark.parametrize(
    "destination_name",
    [
        "",
        ".",
        "..",
        "../outside",
        "nested/repository",
        r"nested\repository",
        "C:repository",
        "/absolute",
    ],
)
def test_copy_fixture_rejects_invalid_destination(
    workspace_manager: WorkspaceManager,
    fixture_source: Path,
    destination_name: str,
) -> None:
    """Destination names must be a single safe path component."""

    workspace = workspace_manager.create()

    with pytest.raises(ExecutionError, match="destination"):
        FixtureManager(workspace_manager).copy_fixture(
            fixture_source,
            workspace,
            destination_name=destination_name,
        )

    workspace_manager.cleanup(workspace)


def test_copy_fixture_rejects_existing_destination(
    workspace_manager: WorkspaceManager,
    fixture_source: Path,
) -> None:
    """An existing destination must never be overwritten."""

    workspace = workspace_manager.create()
    destination = workspace.path / "repository"
    destination.mkdir()

    with pytest.raises(ExecutionError, match="already exists"):
        FixtureManager(workspace_manager).copy_fixture(
            fixture_source,
            workspace,
        )

    workspace_manager.cleanup(workspace)


def test_copy_fixture_rejects_symlink(
    workspace_manager: WorkspaceManager,
    fixture_source: Path,
) -> None:
    """Symbolic links inside a fixture must be rejected."""

    external_file = fixture_source.parent / "external.txt"
    external_file.write_text("outside fixture", encoding="utf-8")

    link = fixture_source / "external-link.txt"

    try:
        link.symlink_to(external_file)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"File symlinks are unavailable: {exc}")

    workspace = workspace_manager.create()

    with pytest.raises(ExecutionError, match="Symbolic links"):
        FixtureManager(workspace_manager).copy_fixture(
            fixture_source,
            workspace,
        )

    assert not (workspace.path / "repository").exists()

    workspace_manager.cleanup(workspace)


@pytest.mark.skipif(
    os.name == "nt",
    reason="Creating FIFO files is not supported on Windows.",
)
def test_copy_fixture_rejects_special_file(
    workspace_manager: WorkspaceManager,
    fixture_source: Path,
) -> None:
    """Unsupported filesystem entries must be rejected."""

    import os

    fifo = fixture_source / "unsupported-pipe"
    os.mkfifo(fifo)

    workspace = workspace_manager.create()

    with pytest.raises(ExecutionError, match="special file"):
        FixtureManager(workspace_manager).copy_fixture(
            fixture_source,
            workspace,
        )

    workspace_manager.cleanup(workspace)


def test_copy_fixture_cleans_partial_destination(
    workspace_manager: WorkspaceManager,
    fixture_source: Path,
) -> None:
    """A failed copy must not leave a partial destination."""

    invalid_file = fixture_source / "unsupported-entry"

    try:
        invalid_file.symlink_to(
            fixture_source / "main.py"
        )
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"File symlinks are unavailable: {exc}")

    workspace = workspace_manager.create()

    with pytest.raises(ExecutionError):
        FixtureManager(workspace_manager).copy_fixture(
            fixture_source,
            workspace,
        )

    assert not (workspace.path / "repository").exists()

    workspace_manager.cleanup(workspace)


def test_copy_fixture_rejects_workspace_as_source(
    workspace_manager: WorkspaceManager,
) -> None:
    """Workspace must not be copied into a child of itself."""

    workspace = workspace_manager.create()
    manager = FixtureManager(workspace_manager)

    with pytest.raises(
        ExecutionError,
        match="must not overlap",
    ):
        manager.copy_fixture(
            source=workspace.path,
            workspace=workspace,
        )

    assert not (workspace.path / "repository").exists()

    workspace_manager.cleanup(workspace)



def test_copy_fixture_rejects_junction(
    workspace_manager: WorkspaceManager,
    fixture_source: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Junction entries must not be copied into a fixture workspace."""

    junction_target = fixture_source / "junction-target"
    junction_target.mkdir()

    junction = fixture_source / "junction-entry"
    junction.mkdir()

    original_is_junction = Path.is_junction

    def fake_is_junction(path: Path) -> bool:
        if path == junction:
            return True

        return original_is_junction(path)

    monkeypatch.setattr(Path, "is_junction", fake_is_junction)

    workspace = workspace_manager.create()

    with pytest.raises(
        ExecutionError,
        match="junctions are not allowed",
    ):
        FixtureManager(workspace_manager).copy_fixture(
            fixture_source,
            workspace,
        )

    assert not (workspace.path / "repository").exists()

    workspace_manager.cleanup(workspace)


def test_copy_fixture_rejects_invalid_source(tmp_path: Path) -> None:
    from repoguard_eval.exceptions import ExecutionError

    workspace_manager = WorkspaceManager(tmp_path / "workspaces")
    workspace = workspace_manager.create()
    fixture_manager = FixtureManager(workspace_manager)

    try:
        with pytest.raises(ExecutionError, match="Invalid fixture source"):
            fixture_manager.copy_fixture(
                source=None,  # type: ignore[arg-type]
                workspace=workspace,
            )
    finally:
        workspace_manager.cleanup(workspace)
