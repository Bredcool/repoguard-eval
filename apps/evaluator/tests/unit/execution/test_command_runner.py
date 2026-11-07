from unittest.mock import Mock
from uuid import uuid4

import pytest

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.command_runner import ContainerCommandRunner
from repoguard_eval.execution.docker_process import DockerCommandResult
from repoguard_eval.execution.docker_runtime import (
    DockerRuntime,
    DockerRuntimeManager,
)
from repoguard_eval.grading.enums import ExecutionStatus


IMAGE = "repoguard/python:3.13"
CONTAINER_ID = "a" * 64


def make_runtime():
    job_id = str(uuid4())
    resource_id = job_id.replace("-", "")

    return DockerRuntime(
        job_id=job_id,
        container_id=CONTAINER_ID,
        container_name=f"repoguard-{resource_id}",
        volume_name=f"repoguard-{resource_id}",
        image=IMAGE,
    )


def make_result(returncode=0, stdout="ok", stderr=""):
    return DockerCommandResult(
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=0.25,
    )


@pytest.fixture
def setup_runner():
    process = Mock()
    process.run.return_value = make_result()

    runtime_manager = DockerRuntimeManager(
        process_manager=process,
        allowed_images={IMAGE},
    )

    return ContainerCommandRunner(runtime_manager), process


def test_run_executes_command_inside_container(setup_runner):
    runner, process = setup_runner
    runtime = make_runtime()

    result = runner.run(runtime, "pytest -q", timeout=60)

    assert result.status == ExecutionStatus.PASSED
    assert result.exit_code == 0
    assert result.stdout == "ok"
    assert result.duration_seconds == 0.25

    process.run.assert_called_once_with(
        [
            "exec",
            "--workdir",
            "/workspace/repository",
            CONTAINER_ID,
            "sh",
            "-lc",
            "pytest -q",
        ],
        timeout=60.0,
    )


def test_run_returns_failed_for_nonzero_exit_code(setup_runner):
    runner, process = setup_runner
    process.run.return_value = make_result(
        returncode=1,
        stdout="",
        stderr="test failed",
    )

    result = runner.run(make_runtime(), "pytest -q")

    assert result.status == ExecutionStatus.FAILED
    assert result.exit_code == 1
    assert result.stderr == "test failed"


def test_run_returns_error_for_infrastructure_failure(setup_runner):
    runner, process = setup_runner
    process.run.side_effect = ExecutionError("Docker daemon unavailable")

    result = runner.run(make_runtime(), "pytest -q")

    assert result.status == ExecutionStatus.ERROR
    assert result.exit_code is None
    assert "Docker daemon unavailable" in result.stderr


@pytest.mark.parametrize("command", ["", " ", "\x00"])
def test_run_rejects_invalid_command(setup_runner, command):
    runner, process = setup_runner

    with pytest.raises(ExecutionError):
        runner.run(make_runtime(), command)

    process.run.assert_not_called()


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan"), True])
def test_run_rejects_invalid_timeout(setup_runner, timeout):
    runner, process = setup_runner

    with pytest.raises(ExecutionError):
        runner.run(make_runtime(), "pytest -q", timeout)

    process.run.assert_not_called()


def test_run_rejects_invalid_runtime(setup_runner):
    runner, process = setup_runner
    runtime = make_runtime()

    forged_runtime = DockerRuntime(
        job_id=runtime.job_id,
        container_id="../invalid",
        container_name=runtime.container_name,
        volume_name=runtime.volume_name,
        image=runtime.image,
    )

    with pytest.raises(ExecutionError):
        runner.run(forged_runtime, "pytest -q")

    process.run.assert_not_called()


def test_run_check_returns_grading_evidence(setup_runner):
    runner, _ = setup_runner

    evidence = runner.run_check(
        make_runtime(),
        name="functional",
        command="pytest -q",
    )

    assert evidence.name == "functional"
    assert evidence.status == ExecutionStatus.PASSED
    assert evidence.command == "pytest -q"
    assert evidence.exit_code == 0