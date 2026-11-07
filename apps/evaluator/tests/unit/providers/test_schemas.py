
"""Tests for provider request and response schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from repoguard_eval.providers import (
    Diagnosis,
    Patch,
    ProviderRequest,
    ProviderResponse,
    TokenUsage,
)


def test_provider_request_creation() -> None:
    experiment_id = uuid4()

    request = ProviderRequest(
        task_id="rg-go-001",
        experiment_id=experiment_id,
        model="test-model",
        system_prompt="You are a software debugging agent.",
        user_prompt="Fix the transaction defect.",
        parameters={"temperature": 0.0},
    )

    assert request.task_id == "rg-go-001"
    assert request.experiment_id == experiment_id
    assert request.model == "test-model"
    assert request.parameters["temperature"] == 0.0


def test_provider_request_requires_model() -> None:
    with pytest.raises(ValidationError):
        ProviderRequest(
            task_id="rg-go-001",
            experiment_id=uuid4(),
            system_prompt="System",
            user_prompt="User",
        )


def test_provider_request_rejects_invalid_task_id() -> None:
    with pytest.raises(ValidationError):
        ProviderRequest(
            task_id="INVALID ID",
            experiment_id=uuid4(),
            model="test-model",
            system_prompt="System",
            user_prompt="User",
        )


def test_diagnosis_creation() -> None:
    diagnosis = Diagnosis(
        root_cause="Transaction commits before inventory reservation.",
        evidence=["order/service.go"],
    )

    assert diagnosis.root_cause is not None
    assert len(diagnosis.evidence) == 1


def test_patch_creation() -> None:
    patch = Patch(
        format="unified_diff",
        content="--- a/order/service.go\n+++ b/order/service.go",
    )

    assert patch.format == "unified_diff"
    assert patch.content.startswith("---")


def test_patch_rejects_empty_content() -> None:
    with pytest.raises(ValidationError):
        Patch(
            format="unified_diff",
            content="",
        )


def test_token_usage_allows_missing_values() -> None:
    usage = TokenUsage(input_tokens=100)

    assert usage.input_tokens == 100
    assert usage.output_tokens is None
    assert usage.total_tokens is None


def test_token_usage_rejects_negative_values() -> None:
    with pytest.raises(ValidationError):
        TokenUsage(input_tokens=-1)


def test_provider_response_creation() -> None:
    experiment_id = uuid4()
    raw_response = {"id": "response-123", "output": []}

    response = ProviderResponse(
        provider="openai",
        model="test-model",
        task_id="rg-go-001",
        experiment_id=experiment_id,
        diagnosis=Diagnosis(
            root_cause="Transaction lifecycle is incorrect.",
            evidence=["order/service.go"],
        ),
        patch=Patch(
            format="unified_diff",
            content="--- a/file.go\n+++ b/file.go",
        ),
        usage=TokenUsage(
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
        ),
        raw_response=raw_response,
    )

    assert response.provider == "openai"
    assert response.model == "test-model"
    assert response.experiment_id == experiment_id
    assert response.raw_response == raw_response
    assert response.usage is not None
    assert response.usage.total_tokens == 300


def test_provider_response_allows_missing_diagnosis_and_patch() -> None:
    response = ProviderResponse(
        provider="openai",
        model="test-model",
        task_id="rg-go-001",
        experiment_id=uuid4(),
        raw_response={"output": []},
    )

    assert response.diagnosis is None
    assert response.patch is None
    assert response.usage is None


def test_provider_response_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ProviderResponse(
            provider="openai",
            model="test-model",
            task_id="rg-go-001",
            experiment_id=uuid4(),
            raw_response={},
            unknown_field="unexpected",
        )
