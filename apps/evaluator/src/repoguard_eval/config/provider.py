
"""Configuration for external AI model providers."""

from functools import lru_cache
from typing import Self

from pydantic import (
    AnyHttpUrl,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderSettings(BaseSettings):
    """Environment-based configuration for AI model providers."""

    model_config = SettingsConfigDict(
        env_prefix="RG_PROVIDER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_assignment=True,
    )

    provider: str = "openai"

    api_key: SecretStr | None = None

    model: str | None = None

    base_url: AnyHttpUrl = "https://api.openai.com/v1"

    timeout_seconds: float = Field(
        default=60.0,
        gt=0,
        le=600,
    )

    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
    )

    retry_backoff_seconds: float = Field(
        default=1.0,
        gt=0,
        le=30,
    )

    max_output_tokens: int | None = Field(
        default=None,
        gt=0,
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        """Normalize and validate the provider identifier."""

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError("Provider name cannot be empty.")

        if not normalized.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Provider name contains invalid characters.")

        return normalized

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str | None) -> str | None:
        """Reject empty model identifiers."""

        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            raise ValueError("Model identifier cannot be empty.")

        return normalized

    @model_validator(mode="after")
    def validate_provider_configuration(self) -> Self:
        """Validate fields that are optional during configuration loading."""

        if self.max_retries == 0 and self.retry_backoff_seconds <= 0:
            raise ValueError(
                "Retry backoff must be positive when retries are enabled."
            )

        return self

    @property
    def is_ready(self) -> bool:
        """Return whether credentials and model configuration are available."""

        return (
            self.api_key is not None
            and bool(self.api_key.get_secret_value())
            and self.model is not None
        )

    def require_ready(self) -> tuple[str, str]:
        """Return API key and model or reject incomplete configuration."""

        if self.api_key is None or not self.api_key.get_secret_value():
            raise ValueError("Provider API key is not configured.")

        if self.model is None:
            raise ValueError("Provider model is not configured.")

        return self.api_key.get_secret_value(), self.model


@lru_cache(maxsize=1)
def get_provider_settings() -> ProviderSettings:
    """Return a cached provider settings instance."""

    return ProviderSettings()
