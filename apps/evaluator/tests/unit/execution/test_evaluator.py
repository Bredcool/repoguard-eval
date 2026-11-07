from unittest.mock import Mock
from uuid import uuid4

from repoguard_eval.execution.docker_runtime import DockerRuntime
from repoguard_eval.execution.evaluator import ExecutionEvaluator
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


def make_evidence(name, command, status):
    return ExecutionCheckEvidence(
        name=name,
        status=status,
        command=command,
        exit_code=0 if status == ExecutionStatus.PASSED else 1,
        duration_seconds=0.1,
        stdout="",
        stderr="",
    )


def test_evaluate_runs_all_commands_when_passed():
    runner = Mock()
    runner.run_check.side_effect = [
        make_evidence("build_1", "python -m compileall .", ExecutionStatus.PASSED),
        make_evidence("build_2", "pytest -q", ExecutionStatus.PASSED),
    ]

    evaluator = ExecutionEvaluator(runner)

    results = evaluator.evaluate(
        make_runtime(),
        "build",
        ["python -m compileall .", "pytest -q"],
    )

    assert len(results) == 2
    assert all(item.status == ExecutionStatus.PASSED for item in results)
    assert runner.run_check.call_count == 2


def test_evaluate_skips_remaining_commands_after_failure():
    runner = Mock()
    runner.run_check.return_value = make_evidence(
        "functional_1",
        "pytest tests/public",
        ExecutionStatus.FAILED,
    )

    evaluator = ExecutionEvaluator(runner)

    results = evaluator.evaluate(
        make_runtime(),
        "functional",
        [
            "pytest tests/public",
            "pytest tests/hidden",
            "pytest tests/regression",
        ],
    )

    assert len(results) == 3
    assert results[0].status == ExecutionStatus.FAILED
    assert results[1].status == ExecutionStatus.SKIPPED
    assert results[2].status == ExecutionStatus.SKIPPED
    assert runner.run_check.call_count == 1


def test_evaluate_skips_remaining_commands_after_infrastructure_error():
    runner = Mock()
    runner.run_check.return_value = make_evidence(
        "build_1",
        "go build ./...",
        ExecutionStatus.ERROR,
    )

    evaluator = ExecutionEvaluator(runner)

    results = evaluator.evaluate(
        make_runtime(),
        "build",
        ["go build ./...", "go test ./..."],
    )

    assert results[0].status == ExecutionStatus.ERROR
    assert results[1].status == ExecutionStatus.SKIPPED
    assert runner.run_check.call_count == 1


def test_evaluate_returns_empty_tuple_for_no_commands():
    runner = Mock()
    evaluator = ExecutionEvaluator(runner)

    results = evaluator.evaluate(make_runtime(), "build", [])

    assert results == ()
    runner.run_check.assert_not_called()