"""Tests for safe patch application."""

from pathlib import Path

import pytest

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.patch_applier import PatchApplier
from repoguard_eval.execution.patch_validator import PatchValidator
from repoguard_eval.execution.patches import Patch


@pytest.fixture
def applier_environment(patch_environment):
    environment = patch_environment
    validator = environment["validator"]

    environment["applier"] = PatchApplier(
        validator.workspace_manager,
        validator,
    )

    return environment


def test_apply_modification_patch(applier_environment):
    environment = applier_environment
    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        '-print("old")\n'
        '+print("new")\n'
    )

    validated = environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    result = environment["applier"].apply(
        environment["workspace"],
        validated,
    )

    assert result.changed_files == ("main.py",)
    assert (result.repository_path / "main.py").read_text(
        encoding="utf-8"
    ) == 'print("new")\n'
    assert result.snapshot.repository_path == result.repository_path


def test_apply_addition_patch_creates_nested_directories(
    applier_environment,
):
    environment = applier_environment
    content = (
        "--- /dev/null\n"
        "+++ b/nested/new.py\n"
        "@@ -0,0 +1 @@\n"
        "+VALUE = 42\n"
    )

    validated = environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    result = environment["applier"].apply(
        environment["workspace"],
        validated,
    )

    assert result.changed_files == ("nested/new.py",)
    assert (
        result.repository_path / "nested" / "new.py"
    ).read_text(encoding="utf-8") == "VALUE = 42\n"


def test_apply_deletion_patch(applier_environment):
    environment = applier_environment
    content = (
        "--- a/main.py\n"
        "+++ /dev/null\n"
        "@@ -1 +0,0 @@\n"
        '-print("old")\n'
    )

    validated = environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    result = environment["applier"].apply(
        environment["workspace"],
        validated,
    )

    assert result.changed_files == ("main.py",)
    assert not (result.repository_path / "main.py").exists()


def test_failed_git_check_preserves_original_repository(
    applier_environment,
):
    environment = applier_environment
    repository = environment["repository"]
    original = (repository / "main.py").read_bytes()

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        "-different content\n"
        "+new content\n"
    )

    validated = environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    with pytest.raises(ExecutionError):
        environment["applier"].apply(
            environment["workspace"],
            validated,
        )

    assert (repository / "main.py").read_bytes() == original
    assert not list(
        environment["workspace"].path.glob("repoguard-stage-*")
    )


def test_apply_rejects_invalid_patch_type(applier_environment):
    environment = applier_environment

    with pytest.raises(ExecutionError):
        environment["applier"].apply(
            environment["workspace"],
            None,
        )


@pytest.mark.parametrize("timeout", [0, -1, True, 1.5, "10"])
def test_apply_rejects_invalid_timeout(
    applier_environment,
    timeout,
):
    environment = applier_environment
    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    validated = environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    with pytest.raises(ExecutionError):
        environment["applier"].apply(
            environment["workspace"],
            validated,
            timeout=timeout,
        )


def test_apply_rejects_invalid_workspace_manager():
    with pytest.raises(ExecutionError):
        PatchApplier(None, None)


def test_apply_rejects_invalid_patch_validator(applier_environment):
    environment = applier_environment

    with pytest.raises(ExecutionError):
        PatchApplier(
            environment["applier"].workspace_manager,
            None,
        )


@pytest.fixture
def patch_environment(tmp_path: Path):
    from repoguard_eval.execution.fixtures import FixtureManager
    from repoguard_eval.execution.workspace import WorkspaceManager

    workspace_manager = WorkspaceManager(tmp_path / "workspaces")
    fixture_manager = FixtureManager(workspace_manager)
    validator = PatchValidator(workspace_manager)

    workspace = workspace_manager.create()
    source = tmp_path / "source"
    source.mkdir()

    (source / "main.py").write_text(
        'print("old")\n',
        encoding="utf-8",
    )

    fixture_manager.copy_fixture(source, workspace)

    return {
        "workspace": workspace,
        "validator": validator,
        "repository": workspace.path / "repository",
    }


def test_apply_supports_unprefixed_patch_paths(applier_environment):
    environment = applier_environment
    content = (
        "--- main.py\n"
        "+++ main.py\n"
        "@@ -1 +1 @@\n"
        '-print("old")\n'
        '+print("normalized")\n'
    )

    validated = environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    result = environment["applier"].apply(
        environment["workspace"],
        validated,
    )

    assert result.changed_files == ("main.py",)
    assert (result.repository_path / "main.py").read_text(
        encoding="utf-8"
    ) == 'print("normalized")\n'


def test_backup_cleanup_failure_is_reported_without_failing_application(
    applier_environment,
    monkeypatch,
):
    import repoguard_eval.execution.patch_applier as patch_applier_module

    environment = applier_environment
    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        '-print("old")\n'
        '+print("new")\n'
    )

    validated = environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    original_rmtree = patch_applier_module.shutil.rmtree

    def fail_backup_cleanup(path, *args, **kwargs):
        if Path(path).name.startswith("repoguard-backup-"):
            raise OSError("simulated backup cleanup failure")
        return original_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(
        patch_applier_module.shutil,
        "rmtree",
        fail_backup_cleanup,
    )

    result = environment["applier"].apply(
        environment["workspace"],
        validated,
    )

    assert result.backup_cleanup_pending is True
    assert (result.repository_path / "main.py").read_text(
        encoding="utf-8"
    ) == 'print("new")\n'

    backups = list(
        environment["workspace"].path.glob("repoguard-backup-*")
    )
    assert len(backups) == 1


def test_promotion_failure_rolls_back_original_repository(
    applier_environment,
    monkeypatch,
):
    import repoguard_eval.execution.patch_applier as patch_applier_module

    environment = applier_environment
    repository = environment["repository"]
    original_content = (repository / "main.py").read_bytes()
    original_replace = patch_applier_module.os.replace

    def fail_staging_promotion(source, destination):
        source_path = Path(source)

        if source_path.name.startswith("repoguard-stage-"):
            raise OSError("simulated promotion failure")

        return original_replace(source, destination)

    monkeypatch.setattr(
        patch_applier_module.os,
        "replace",
        fail_staging_promotion,
    )

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        '-print("old")\n'
        '+print("new")\n'
    )

    validated = environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    with pytest.raises(ExecutionError, match="Unable to promote"):
        environment["applier"].apply(
            environment["workspace"],
            validated,
        )

    assert repository.exists()
    assert (repository / "main.py").read_bytes() == original_content
    assert not list(
        environment["workspace"].path.glob("repoguard-backup-*")
    )
    assert not list(
        environment["workspace"].path.glob("repoguard-stage-*")
    )
