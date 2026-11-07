from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.docker_process import DockerCommandResult
from repoguard_eval.execution.docker_runtime import DockerRuntime, DockerRuntimeManager
from repoguard_eval.execution.docker_transfer import DockerVolumeTransfer
from repoguard_eval.execution.workspace import WorkspaceManager


JOB_ID = str(uuid4())
CONTAINER_ID = "a" * 64
IMAGE = "repoguard/python:3.13"


def make_result(returncode=0, stderr=""):
    return DockerCommandResult(
        returncode=returncode,
        stdout="",
        stderr=stderr,
        duration_seconds=0.01,
    )


def make_runtime():
    resource_id = JOB_ID.replace("-", "")
    return DockerRuntime(
        job_id=JOB_ID,
        container_id=CONTAINER_ID,
        container_name=f"repoguard-{resource_id}",
        volume_name=f"repoguard-{resource_id}",
        image=IMAGE,
    )


@pytest.fixture
def setup_transfer(tmp_path):
    process = Mock()
    process.run.return_value = make_result()

    runtime_manager = DockerRuntimeManager(
        process_manager=process,
        allowed_images={IMAGE},
    )
    workspace_manager = WorkspaceManager(tmp_path / "workspaces")
    workspace = workspace_manager.create()

    transfer = DockerVolumeTransfer(runtime_manager, workspace_manager)

    return transfer, process, workspace, workspace_manager


def test_copy_to_container_transfers_repository(setup_transfer):
    transfer, process, workspace, _ = setup_transfer
    repository = workspace.path / "repository"
    repository.mkdir()
    (repository / "main.py").write_text("print('hello')", encoding="utf-8")

    transfer.copy_to_container(make_runtime(), workspace)

    process.run.assert_called_once_with(
        [
            "cp",
            str(repository),
            f"{CONTAINER_ID}:/workspace/",
        ],
        timeout=120.0,
    )


def test_copy_from_container_transfers_repository(setup_transfer):
    transfer, process, workspace, _ = setup_transfer
    process.run.side_effect = lambda args, timeout: (
        (workspace.path / "repository-output").mkdir()
        or make_result()
    )

    destination = transfer.copy_from_container(
        make_runtime(),
        workspace,
    )

    assert destination == workspace.path / "repository-output"
    assert destination.is_dir()
    assert process.run.call_args.args[0] == [
        "cp",
        f"{CONTAINER_ID}:/workspace/repository",
        str(destination),
    ]


def test_copy_to_container_rejects_missing_source(setup_transfer):
    transfer, process, workspace, _ = setup_transfer

    with pytest.raises(ExecutionError):
        transfer.copy_to_container(make_runtime(), workspace)

    process.run.assert_not_called()


@pytest.mark.parametrize("name", ["", "../escape", "a/b", "a\\b", ".", ".."])
def test_copy_to_container_rejects_invalid_source_name(setup_transfer, name):
    transfer, process, workspace, _ = setup_transfer

    with pytest.raises(ExecutionError, match="directory name"):
        transfer.copy_to_container(make_runtime(), workspace, name)

    process.run.assert_not_called()


def test_copy_to_container_rejects_invalid_runtime(setup_transfer):
    transfer, process, workspace, _ = setup_transfer
    repository = workspace.path / "repository"
    repository.mkdir()

    runtime = make_runtime()
    forged = DockerRuntime(
        job_id=runtime.job_id,
        container_id="../invalid",
        container_name=runtime.container_name,
        volume_name=runtime.volume_name,
        image=runtime.image,
    )

    with pytest.raises(ExecutionError):
        transfer.copy_to_container(forged, workspace)

    process.run.assert_not_called()


def test_copy_from_container_rejects_existing_destination(setup_transfer):
    transfer, process, workspace, _ = setup_transfer
    (workspace.path / "repository-output").mkdir()

    with pytest.raises(ExecutionError, match="already exists"):
        transfer.copy_from_container(make_runtime(), workspace)

    process.run.assert_not_called()


def test_copy_from_container_cleans_partial_destination_on_failure(setup_transfer):
    transfer, process, workspace, _ = setup_transfer

    def fail_copy(args, timeout):
        (workspace.path / "repository-output").mkdir()
        raise ExecutionError("copy failed")

    process.run.side_effect = fail_copy

    with pytest.raises(ExecutionError, match="copy failed"):
        transfer.copy_from_container(make_runtime(), workspace)

    assert not (workspace.path / "repository-output").exists()


def test_copy_from_container_rejects_symlink_output(setup_transfer):
    transfer, process, workspace, _ = setup_transfer

    def create_link(args, timeout):
        target = workspace.path / "target"
        target.mkdir()
        (workspace.path / "repository-output").symlink_to(
            target,
            target_is_directory=True,
        )
        return make_result()

    process.run.side_effect = create_link

    with pytest.raises(ExecutionError):
        transfer.copy_from_container(make_runtime(), workspace)

    assert not (workspace.path / "repository-output").exists()
