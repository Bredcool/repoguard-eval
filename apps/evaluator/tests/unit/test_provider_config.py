    
"""Tests for AI provider configuration."""

import pytest
from pydantic import SecretStr, ValidationError

from repoguard_eval.config import (
    ProviderSettings,
    get_provider_settings,
)


def test_default_provider_settings() -> None:
    settings = ProviderSettings(_env_file=None)

    assert settings.provider == "openai"
    assert settings.api_key is None
    assert settings.model is None
    assert str(settings.base_url).startswith("https://api.openai.com")
    assert settings.timeout_seconds == 60.0
    assert settings.max_retries == 3
    assert settings.retry_backoff_seconds == 1.0
    assert settings.max_output_tokens is None
    assert settings.is_ready is False


def test_custom_provider_settings() -> None:
    settings = ProviderSettings(
        _env_file=None,
        provider="openai",
        api_key="test-api-key",
        model="test-model",
        timeout_seconds=30,
        max_retries=5,
        retry_backoff_seconds=2,
        max_output_tokens=2048,
    )

    assert settings.provider == "openai"
    assert isinstance(settings.api_key, SecretStr)
    assert settings.model == "test-model"
    assert settings.timeout_seconds == 30
    assert settings.max_retries == 5
    assert settings.retry_backoff_seconds == 2
    assert settings.max_output_tokens == 2048
    assert settings.is_ready is True


def test_provider_name_is_normalized() -> None:
    settings = ProviderSettings(
        _env_file=None,
        provider="  OpenAI  ",
    )

    assert settings.provider == "openai"


def test_empty_provider_name_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProviderSettings(
            _env_file=None,
            provider="   ",
        )


def test_empty_model_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProviderSettings(
            _env_file=None,
            model="   ",
        )


def test_api_key_is_masked() -> None:
    settings = ProviderSettings(
        _env_file=None,
        api_key="secret-value",
    )

    assert settings.api_key is not None
    assert "secret-value" not in str(settings.api_key)
    assert settings.api_key.get_secret_value() == "secret-value"


def test_require_ready_rejects_missing_api_key() -> None:
    settings = ProviderSettings(
        _env_file=None,
        model="test-model",
    )

    with pytest.raises(ValueError, match="API key"):
        settings.require_ready()


def test_require_ready_rejects_missing_model() -> None:
    settings = ProviderSettings(
        _env_file=None,
        api_key="test-api-key",
    )

    with pytest.raises(ValueError, match="model"):
        settings.require_ready()


def test_require_ready_returns_credentials() -> None:
    settings = ProviderSettings(
        _env_file=None,
        api_key="test-api-key",
        model="test-model",
    )

    api_key, model = settings.require_ready()

    assert api_key == "test-api-key"
    assert model == "test-model"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("timeout_seconds", 0),
        ("timeout_seconds", -1),
        ("timeout_seconds", 601),
        ("max_retries", -1),
        ("max_retries", 11),
        ("retry_backoff_seconds", 0),
        ("retry_backoff_seconds", 31),
        ("max_output_tokens", 0),
        ("max_output_tokens", -1),
    ],
)
def test_invalid_provider_limits_are_rejected(
    field: str,
    value: int,
) -> None:
    with pytest.raises(ValidationError):
        ProviderSettings(
            _env_file=None,
            **{field: value},
        )


def test_provider_settings_load_from_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv("RG_PROVIDER_PROVIDER", "openai")
    monkeypatch.setenv("RG_PROVIDER_API_KEY", "environment-api-key")
    monkeypatch.setenv("RG_PROVIDER_MODEL", "environment-model")
    monkeypatch.setenv("RG_PROVIDER_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("RG_PROVIDER_MAX_RETRIES", "2")

    settings = ProviderSettings(_env_file=None)

    assert settings.provider == "openai"
    assert settings.api_key is not None
    assert settings.api_key.get_secret_value() == "environment-api-key"
    assert settings.model == "environment-model"
    assert settings.timeout_seconds == 45
    assert settings.max_retries == 2


def test_get_provider_settings_returns_cached_instance(
    monkeypatch,
) -> None:
    get_provider_settings.cache_clear()
    monkeypatch.setenv("RG_PROVIDER_MODEL", "cached-model")

    try:
        first = get_provider_settings()
        second = get_provider_settings()

        assert first is second
        assert first.model == "cached-model"
    finally:
        get_provider_settings.cache_clear()
