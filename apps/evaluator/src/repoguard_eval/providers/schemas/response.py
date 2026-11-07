
"""Internal request and response schemas for AI providers."""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProviderRequest(BaseModel):
    """Provider-independent request sent to an AI model."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    experiment_id: UUID
    model: str = Field(min_length=1)
    system_prompt: str = Field(min_length=1)
    user_prompt: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)


class Diagnosis(BaseModel):
    """Normalized diagnosis extracted from a model response."""

    model_config = ConfigDict(extra="forbid")

    root_cause: str | None = None
    evidence: list[str] = Field(default_factory=list)


class Patch(BaseModel):
    """Normalized patch extracted from a model response."""

    model_config = ConfigDict(extra="forbid")

    format: Literal["unified_diff"]
    content: str = Field(min_length=1)


class TokenUsage(BaseModel):
    """Token usage reported by a provider, when available."""

    model_config = ConfigDict(extra="forbid")

    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class ProviderResponse(BaseModel):
    """Provider-independent normalized model response."""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    task_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    experiment_id: UUID

    diagnosis: Diagnosis | None = None
    patch: Patch | None = None
    usage: TokenUsage | None = None

    response_id: str | None = None
    finish_reason: str | None = None
    raw_response: dict[str, Any]
    raw_response_path: str | None = None
