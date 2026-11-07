
"""Tests for patch validation."""

from pathlib import Path

import pytest

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.fixtures import FixtureManager
from repoguard_eval.execution.patches import Patch
from repoguard_eval.execution.patch_validator import PatchValidator
from repoguard_eval.execution.workspace import WorkspaceManager


@pytest.fixture
def patch_environment(tmp_path: Path):
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


def test_validate_modification_patch(patch_environment):
    environment = patch_environment

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        '-print("old")\n'
        '+print("new")\n'
    )

    result = environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    assert result.content == content
    assert result.total_bytes == len(content.encode("utf-8"))
    assert len(result.files) == 1
    assert result.files[0].old_path == "main.py"
    assert result.files[0].new_path == "main.py"


def test_validate_addition_patch(patch_environment):
    environment = patch_environment

    content = (
        "--- /dev/null\n"
        "+++ b/new.py\n"
        "@@ -0,0 +1 @@\n"
        "+VALUE = 42\n"
    )

    result = environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    assert result.files[0].old_path is None
    assert result.files[0].new_path == "new.py"


def test_validate_deletion_patch(patch_environment):
    environment = patch_environment

    content = (
        "--- a/main.py\n"
        "+++ /dev/null\n"
        "@@ -1 +0,0 @@\n"
        '-print("old")\n'
    )

    result = environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    assert result.files[0].old_path == "main.py"
    assert result.files[0].new_path is None


def test_validate_deletion_line_starting_with_three_dashes(
    patch_environment,
):
    environment = patch_environment

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        "--- comment\n"
        "+++ replacement\n"
    )

    result = environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    assert len(result.files) == 1


@pytest.mark.parametrize(
    "path",
    [
        "/etc/passwd",
        "../outside.py",
        "a/../../outside.py",
        "C:/Windows/system.ini",
        "a\\..\\outside.py",
        "a//outside.py",
    ],
)
def test_rejects_unsafe_patch_paths(patch_environment, path):
    environment = patch_environment

    content = (
        f"--- {path}\n"
        f"+++ {path}\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )


def test_rejects_malformed_hunk_line_counts(patch_environment):
    environment = patch_environment

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1,2 @@\n"
        "-old\n"
        "+new\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )


def test_rejects_empty_patch(patch_environment):
    environment = patch_environment

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(""),
        )


def test_rejects_invalid_patch_type(patch_environment):
    environment = patch_environment

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            None,
        )


def test_rejects_binary_patch(patch_environment):
    environment = patch_environment

    content = (
        "GIT binary patch\n"
        "literal 10\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )


def test_rejects_git_extended_diff_header(patch_environment):
    environment = patch_environment

    content = (
        "diff --git a/main.py b/main.py\n"
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )


def test_rejects_duplicate_file_targets(patch_environment):
    environment = patch_environment

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        "-new\n"
        "+updated\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )


def test_rejects_patch_exceeding_size_limit(patch_environment):
    environment = patch_environment

    content = "x" * (
        environment["validator"]._MAX_PATCH_BYTES + 1
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )


def test_rejects_missing_repository(patch_environment):
    environment = patch_environment

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
            repository_name="missing",
        )


def test_validation_does_not_modify_repository(patch_environment):
    environment = patch_environment

    file_path = environment["repository"] / "main.py"
    original_content = file_path.read_bytes()

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    assert file_path.read_bytes() == original_content


def test_normalizes_unified_diff_path_prefixes(patch_environment):
    environment = patch_environment

    content = (
        "--- a/src/module.py\n"
        "+++ b/src/module.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    result = environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    assert result.files[0].old_path == "src/module.py"
    assert result.files[0].new_path == "src/module.py"


@pytest.mark.parametrize(
    "path",
    [
        "",
        ".",
        "invalid\x00path.py",
    ],
)
def test_rejects_empty_or_invalid_header_paths(patch_environment, path):
    environment = patch_environment

    content = (
        f"--- {path}\n"
        f"+++ {path}\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )


def test_rejects_malformed_hunk_header(patch_environment):
    environment = patch_environment

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ malformed @@\n"
        "-old\n"
        "+new\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )


def test_rejects_file_without_hunks(patch_environment):
    environment = patch_environment

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )


def test_rejects_patch_exceeding_file_limit(patch_environment):
    environment = patch_environment

    sections = []

    for index in range(101):
        sections.extend(
            [
                f"--- a/file_{index}.py\n",
                f"+++ b/file_{index}.py\n",
                "@@ -1 +1 @@\n",
                "-old\n",
                "+new\n",
            ]
        )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch("".join(sections)),
        )


@pytest.mark.parametrize(
    "metadata",
    [
        "old mode 100644",
        "new mode 100755",
        "new file mode 100644",
        "deleted file mode 100644",
    ],
)
def test_rejects_file_mode_changes(patch_environment, metadata):
    environment = patch_environment

    content = (
        f"{metadata}\n"
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )


def test_constructor_rejects_invalid_workspace_manager():
    with pytest.raises(ExecutionError):
        PatchValidator(None)


@pytest.mark.parametrize(
    "repository_name",
    [
        "",
        ".",
        "..",
        "../outside",
        "nested/repository",
        "C:repository",
    ],
)
def test_rejects_invalid_repository_name(
    patch_environment,
    repository_name,
):
    environment = patch_environment

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
            repository_name=repository_name,
        )


def test_rejects_repository_path_that_is_a_file(patch_environment):
    environment = patch_environment
    repository = environment["repository"]

    (repository / "main.py").unlink()
    repository.rmdir()
    repository.write_text("not a directory", encoding="utf-8")

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )


def test_rejects_missing_destination_header(patch_environment):
    environment = patch_environment

    content = (
        "--- a/main.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )


def test_rejects_patch_with_both_paths_as_dev_null(patch_environment):
    environment = patch_environment

    content = (
        "--- /dev/null\n"
        "+++ /dev/null\n"
        "@@ -0,0 +0,0 @@\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )


def test_validates_context_lines(patch_environment):
    environment = patch_environment

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1,2 +1,2 @@\n"
        " print('first')\n"
        "-print('old')\n"
        "+print('new')\n"
    )

    result = environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    assert len(result.files) == 1


def test_accepts_no_newline_marker(patch_environment):
    environment = patch_environment

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
        "\\ No newline at end of file\n"
    )

    result = environment["validator"].validate(
        environment["workspace"],
        Patch(content),
    )

    assert len(result.files) == 1


def test_rejects_invalid_hunk_line(patch_environment):
    environment = patch_environment

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        "xinvalid\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )


def test_rejects_excess_hunk_lines(patch_environment):
    environment = patch_environment

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "-extra\n"
        "+new\n"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )


def test_rejects_invalid_utf8_string_encoding(patch_environment):
    environment = patch_environment

    content = (
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
        "\ud800"
    )

    with pytest.raises(ExecutionError):
        environment["validator"].validate(
            environment["workspace"],
            Patch(content),
        )
