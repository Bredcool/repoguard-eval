from unittest.mock import Mock
from uuid import uuid4

import pytest

from repoguard_eval.execution.docker_runtime import DockerRuntime
from repoguard_eval.execution.language_validators import (
    CppValidator,
    GoValidator,
    PythonValidator,
)
from repoguard_eval.grading.enums import ExecutionStatus
from repoguard_eval.grading.schemas import ExecutionCheckEvidence


def make_runtime():
    job_id = str(uuid4())
    resource_id = job_id.replace("-", "")

    return DockerRuntime(
        job_id=job_id,
        container_id="a" * 64,
        container_name=f"repoguard-{resource_id}",
        volume_name=f"repoguard-{resource_id}",
        image="repoguard/python:3.13",
    )


def make_evidence(name, command, status=ExecutionStatus.PASSED):
    return ExecutionCheckEvidence(
        name=name,
        status=status,
        command=command,
        exit_code=0 if status == ExecutionStatus.PASSED else 1,
        duration_seconds=0.1,
        stdout="",
        stderr="",
    )


@pytest.mark.parametrize(
    ("validator_class", "expected"),
    [
        (
            GoValidator,
            [
                ("go_static", ("go vet ./...",)),
                ("go_build", ("go build ./...",)),
                ("go_test", ("go test ./...",)),
            ],
        ),
        (
            PythonValidator,
            [
                ("python_static", ("python -m compileall -q .",)),
                ("python_build", ()),
                ("python_test", ("python -m pytest -q",)),
            ],
        ),
        (
            CppValidator,
            [
                ("cpp_static", ()),
                (
                    "cpp_build",
                    (
                        "cmake -S . -B build",
                        "cmake --build build --parallel 2",
                    ),
                ),
                (
                    "cpp_test",
                    ("ctest --test-dir build --output-on-failure",),
                ),
            ],
        ),
    ],
)
def test_language_validator_uses_correct_commands(
    validator_class,
    expected,
):
    evaluator = Mock()
    evaluator.evaluate.side_effect = lambda runtime, name, commands, timeout: tuple(
        make_evidence(f"{name}_{index + 1}", command)
        for index, command in enumerate(commands)
    )

    validator = validator_class(evaluator)
    results = validator.validate(make_runtime())

    assert len(results) == sum(len(commands) for _, commands in expected)
    assert evaluator.evaluate.call_count == sum(
        bool(commands) for _, commands in expected
    )

    actual = [
        (call.kwargs["name"], call.kwargs["commands"])
        for call in evaluator.evaluate.call_args_list
    ]

    assert actual == [
        (name, commands)
        for name, commands in expected
        if commands
    ]


def test_go_validator_stops_after_static_failure():
    evaluator = Mock()

    evaluator.evaluate.side_effect = [
        (
            make_evidence(
                "go_static_1",
                "go vet ./...",
                ExecutionStatus.FAILED,
            ),
        )
    ]

    validator = GoValidator(evaluator)
    results = validator.validate(make_runtime())

    assert len(results) == 3
    assert results[0].status == ExecutionStatus.FAILED
    assert results[1].status == ExecutionStatus.SKIPPED
    assert results[2].status == ExecutionStatus.SKIPPED

    assert evaluator.evaluate.call_count == 1


def test_python_validator_preserves_infrastructure_error():
    evaluator = Mock()
    evaluator.evaluate.return_value = (
        make_evidence(
            "python_static_1",
            "python -m compileall -q .",
            ExecutionStatus.ERROR,
        ),
    )

    validator = PythonValidator(evaluator)
    results = validator.validate(make_runtime())

    assert results[0].status == ExecutionStatus.ERROR
    assert all(
        item.status == ExecutionStatus.SKIPPED
        for item in results[1:]
    )


def test_validator_rejects_invalid_evaluator():
    with pytest.raises(Exception):
        GoValidator(object())