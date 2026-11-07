from unittest.mock import Mock, call
from uuid import uuid4

import pytest

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.docker_process import DockerCommandResult
from repoguard_eval.execution.docker_runtime import (
    DockerResourceLimits,
    DockerRuntime,
    DockerRuntimeManager,
)


JOB_ID = str(uuid4())
IMAGE = "repoguard/python:3.13"
CONTAINER_ID = "a" * 64


def make_result(
    stdout: str = "",
    returncode: int = 0,
    stderr: str = "",
) -> DockerCommandResult:
    return DockerCommandResult(
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=0.01,
    )


def make_manager(
    side_effect=None,
    return_value=None,
    limits=None,
):
    process = Mock()
    process.run.side_effect = side_effect
    if return_value is not None:
        process.run.return_value = return_value

    manager = DockerRuntimeManager(
        process_manager=process,
        allowed_images={IMAGE},
        limits=limits,
    )
    return manager, process


def make_runtime() -> DockerRuntime:
    resource_id = JOB_ID.replace("-", "")
    return DockerRuntime(
        job_id=JOB_ID,
        container_id=CONTAINER_ID,
        container_name=f"repoguard-{resource_id}",
        volume_name=f"repoguard-{resource_id}",
        image=IMAGE,
    )


def test_create_creates_volume_and_restricted_container():
    manager, process = make_manager(
        side_effect=[
            make_result(stdout="volume-id"),
            make_result(stdout=CONTAINER_ID),
        ]
    )

    runtime = manager.create(JOB_ID, IMAGE)

    assert runtime == make_runtime()
    assert process.run.call_count == 2

    volume_args = process.run.call_args_list[0].args[0]
    container_args = process.run.call_args_list[1].args[0]

    assert volume_args[:2] == ["volume", "create"]
    assert "--label" in volume_args
    assert "repoguard.managed=true" in volume_args

    assert container_args[0] == "create"
    assert "--network" in container_args
    assert container_args[container_args.index("--network") + 1] == "none"
    assert "--read-only" in container_args
    assert "--cap-drop" in container_args
    assert container_args[container_args.index("--cap-drop") + 1] == "ALL"
    assert "no-new-privileges" in container_args
    assert "--pids-limit" in container_args
    assert "--memory" in container_args
    assert "--cpus" in container_args
    assert "--mount" in container_args
    assert "--tmpfs" in container_args


def test_create_rejects_untrusted_image():
    manager, process = make_manager()

    with pytest.raises(ExecutionError, match="allowlist"):
        manager.create(JOB_ID, "untrusted/image:latest")

    process.run.assert_not_called()


@pytest.mark.parametrize(
    "job_id",
    [
        "",
        "not-a-uuid",
        str(uuid4()).upper(),
        None,
    ],
)
def test_create_rejects_invalid_job_id(job_id):
    manager, process = make_manager()

    with pytest.raises(ExecutionError, match="job ID"):
        manager.create(job_id, IMAGE)

    process.run.assert_not_called()


def test_create_stops_when_volume_creation_fails():
    manager, process = make_manager(
        return_value=make_result(
            returncode=1,
            stderr="volume creation failed",
        )
    )

    with pytest.raises(ExecutionError, match="volume creation failed"):
        manager.create(JOB_ID, IMAGE)

    process.run.assert_called_once()


def test_create_removes_volume_when_container_creation_fails():
    manager, process = make_manager(
        side_effect=[
            make_result(stdout="volume-id"),
            make_result(returncode=1, stderr="container creation failed"),
            make_result(),
        ]
    )

    with pytest.raises(ExecutionError, match="container creation failed"):
        manager.create(JOB_ID, IMAGE)

    assert process.run.call_count == 3
    assert process.run.call_args_list[2].args[0] == [
        "volume",
        "rm",
        f"repoguard-{JOB_ID.replace('-', '')}",
    ]


def test_create_removes_volume_when_container_id_is_invalid():
    manager, process = make_manager(
        side_effect=[
            make_result(stdout="volume-id"),
            make_result(stdout="invalid-container-id"),
            make_result(),
        ]
    )

    with pytest.raises(ExecutionError, match="invalid container ID"):
        manager.create(JOB_ID, IMAGE)

    assert process.run.call_count == 3


def test_start_starts_container():
    manager, process = make_manager(return_value=make_result())

    manager.start(make_runtime())

    process.run.assert_called_once_with(
        ["start", CONTAINER_ID],
        timeout=30.0,
    )


def test_inspect_returns_container_status():
    manager, process = make_manager(
        return_value=make_result(stdout="running")
    )

    assert manager.inspect(make_runtime()) == "running"

    assert process.run.call_args.args[0] == [
        "inspect",
        "--format",
        "{{.State.Status}}",
        CONTAINER_ID,
    ]


def test_inspect_rejects_unknown_status():
    manager, _ = make_manager(
        return_value=make_result(stdout="unknown")
    )

    with pytest.raises(ExecutionError, match="unknown container state"):
        manager.inspect(make_runtime())


def test_stop_stops_container():
    manager, process = make_manager(return_value=make_result())

    manager.stop(make_runtime(), timeout=15)

    process.run.assert_called_once_with(
        ["stop", "--time", "15", CONTAINER_ID],
        timeout=30.0,
    )


@pytest.mark.parametrize("timeout", [-1, True, 1.5, "10", None])
def test_stop_rejects_invalid_timeout(timeout):
    manager, process = make_manager()

    with pytest.raises(ExecutionError, match="stop timeout"):
        manager.stop(make_runtime(), timeout=timeout)

    process.run.assert_not_called()


def test_cleanup_removes_container_and_volume():
    manager, process = make_manager(
        side_effect=[make_result(), make_result()]
    )

    manager.cleanup(make_runtime())

    assert process.run.call_args_list == [
        call(
            ["rm", "--force", CONTAINER_ID],
            timeout=30.0,
        ),
        call(
            ["volume", "rm", f"repoguard-{JOB_ID.replace('-', '')}"],
            timeout=30.0,
        ),
    ]


def test_cleanup_does_not_remove_volume_if_container_removal_fails():
    manager, process = make_manager(
        return_value=make_result(
            returncode=1,
            stderr="container removal failed",
        )
    )

    with pytest.raises(ExecutionError, match="container removal failed"):
        manager.cleanup(make_runtime())

    process.run.assert_called_once()


def test_runtime_validation_rejects_forged_container_name():
    manager, process = make_manager(return_value=make_result())

    runtime = make_runtime()
    forged = DockerRuntime(
        job_id=runtime.job_id,
        container_id=runtime.container_id,
        container_name="unrelated-container",
        volume_name=runtime.volume_name,
        image=runtime.image,
    )

    with pytest.raises(ExecutionError, match="failed validation"):
        manager.start(forged)

    process.run.assert_not_called()


def test_constructor_rejects_empty_image_allowlist():
    process = Mock()

    with pytest.raises(ExecutionError, match="allowlist"):
        DockerRuntimeManager(process, set())


@pytest.mark.parametrize(
    "limits",
    [
        DockerResourceLimits(memory="0m"),
        DockerResourceLimits(memory="512mb"),
        DockerResourceLimits(cpus=0),
        DockerResourceLimits(cpus=float("inf")),
        DockerResourceLimits(pids_limit=0),
        DockerResourceLimits(pids_limit=True),
        DockerResourceLimits(tmpfs_size="../tmp"),
    ],
)
def test_constructor_rejects_invalid_resource_limits(limits):
    process = Mock()

    with pytest.raises(ExecutionError):
        DockerRuntimeManager(process, {IMAGE}, limits=limits)
