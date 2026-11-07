"""Tests for safe Docker CLI process execution."""

import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.docker_process import (
    DockerCommandResult,
    DockerProcessManager,
)


def test_run_executes_docker_without_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    completed = subprocess.CompletedProcess(
        args=["docker", "version"],
        returncode=0,
        stdout="Docker version 29.1.3",
        stderr="",
    )
    run_mock = Mock(return_value=completed)
    monkeypatch.setattr(subprocess, "run", run_mock)

    manager = DockerProcessManager()

    result = manager.run(["version"])

    assert isinstance(result, DockerCommandResult)
    assert result.returncode == 0
    assert result.stdout == "Docker version 29.1.3"
    assert result.stderr == ""
    assert result.duration_seconds >= 0

    run_mock.assert_called_once_with(
        ["docker", "version"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30.0,
        check=False,
        shell=False,
    )


def test_run_supports_custom_executable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    completed = subprocess.CompletedProcess(
        args=["/usr/bin/docker", "version"],
        returncode=0,
        stdout="Docker version",
        stderr="",
    )
    run_mock = Mock(return_value=completed)
    monkeypatch.setattr(subprocess, "run", run_mock)

    manager = DockerProcessManager(Path("/usr/bin/docker"))

    manager.run(["version"])

    assert run_mock.call_args.args[0] == [
        str(Path("/usr/bin/docker")),
        "version",
    ]


def test_run_returns_nonzero_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    completed = subprocess.CompletedProcess(
        args=["docker", "inspect", "missing"],
        returncode=1,
        stdout="",
        stderr="No such object",
    )
    monkeypatch.setattr(subprocess, "run", Mock(return_value=completed))

    result = DockerProcessManager().run(["inspect", "missing"])

    assert result.returncode == 1
    assert result.stderr == "No such object"


@pytest.mark.parametrize(
    "args",
    [
        "version",
        b"version",
        None,
        ["version", 123],
        ["version", None],
        ["version\x00invalid"],
    ],
)
def test_run_rejects_invalid_arguments(args: object) -> None:
    manager = DockerProcessManager()

    with pytest.raises(ExecutionError):
        manager.run(args)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "timeout",
    [
        0,
        -1,
        float("inf"),
        float("-inf"),
        float("nan"),
        True,
        "30",
        None,
    ],
)
def test_run_rejects_invalid_timeout(timeout: object) -> None:
    manager = DockerProcessManager()

    with pytest.raises(ExecutionError, match="timeout"):
        manager.run(["version"], timeout=timeout)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "executable",
    [
        "",
        " ",
        "\x00docker",
        None,
        123,
    ],
)
def test_constructor_rejects_invalid_executable(executable: object) -> None:
    with pytest.raises(ExecutionError, match="executable"):
        DockerProcessManager(executable)  # type: ignore[arg-type]


def test_run_converts_missing_docker_to_execution_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        Mock(side_effect=FileNotFoundError("docker not found")),
    )

    with pytest.raises(ExecutionError, match="Unable to execute Docker CLI"):
        DockerProcessManager().run(["version"])


def test_run_converts_os_error_to_execution_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        Mock(side_effect=PermissionError("permission denied")),
    )

    with pytest.raises(ExecutionError, match="Unable to execute Docker CLI"):
        DockerProcessManager().run(["version"])


def test_run_converts_timeout_to_execution_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        Mock(
            side_effect=subprocess.TimeoutExpired(
                cmd=["docker", "version"],
                timeout=1,
                output=b"partial output",
                stderr=b"partial error",
            )
        ),
    )

    with pytest.raises(ExecutionError, match="timed out") as exc_info:
        DockerProcessManager().run(["version"], timeout=1)

    assert "partial output" in str(exc_info.value)
    assert "partial error" in str(exc_info.value)


def test_run_converts_subprocess_error_to_execution_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        Mock(side_effect=subprocess.SubprocessError("process failure")),
    )

    with pytest.raises(ExecutionError, match="process failed"):
        DockerProcessManager().run(["version"])


def test_decode_output_handles_none() -> None:
    assert DockerProcessManager._decode_output(None) == ""


def test_decode_output_handles_bytes() -> None:
    assert DockerProcessManager._decode_output(b"docker output") == "docker output"


def test_decode_output_handles_text() -> None:
    assert DockerProcessManager._decode_output("docker output") == "docker output"
