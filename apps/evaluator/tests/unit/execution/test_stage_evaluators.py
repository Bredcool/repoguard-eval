from unittest.mock import Mock
from uuid import uuid4

import pytest

from repoguard_eval.exceptions import ExecutionError
from repoguard_eval.execution.docker_runtime import DockerRuntime
from repoguard_eval.execution.stage_evaluators import (
    BuildEvaluator,
    FunctionalTestEvaluator,
    HiddenTestEvaluator,
    RegressionTestEvaluator,
)


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


@pytest.mark.parametrize(
    ("evaluator_class", "expected_name"),
    [
        (BuildEvaluator, "build"),
        (FunctionalTestEvaluator, "functional"),
        (HiddenTestEvaluator, "hidden"),
        (RegressionTestEvaluator, "regression"),
    ],
)
def test_stage_evaluator_uses_correct_stage_name(
    evaluator_class,
    expected_name,
):
    execution = Mock()
    execution.evaluate.return_value = ()

    evaluator = evaluator_class(execution)
    commands = ["pytest -q"]

    result = evaluator.evaluate(
        runtime=make_runtime(),
        commands=commands,
        timeout=120,
    )

    assert result == ()
    execution.evaluate.assert_called_once_with(
        runtime=execution.evaluate.call_args.kwargs["runtime"],
        name=expected_name,
        commands=commands,
        timeout=120,
    )


def test_hidden_evaluator_keeps_hidden_commands_in_private_execution_layer():
    execution = Mock()
    execution.evaluate.return_value = ()

    evaluator = HiddenTestEvaluator(execution)
    hidden_command = "pytest tests/private --secret-config"

    evaluator.evaluate(make_runtime(), [hidden_command])

    call = execution.evaluate.call_args.kwargs

    assert call["name"] == "hidden"
    assert call["commands"] == [hidden_command]


def test_stage_evaluator_rejects_invalid_execution_evaluator():
    with pytest.raises(ExecutionError):
        BuildEvaluator(object())