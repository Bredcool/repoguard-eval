
"""Tests for provider integration errors."""

from repoguard_eval.providers import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderResponseError,
    ProviderTimeoutError,
)


def test_provider_errors_inherit_from_base_error() -> None:
    errors = [
        ProviderConfigurationError,
        ProviderAuthenticationError,
        ProviderRateLimitError,
        ProviderRequestError,
        ProviderResponseError,
        ProviderTimeoutError,
    ]

    assert all(issubclass(error, ProviderError) for error in errors)


def test_rate_limit_error_stores_retry_after() -> None:
    error = ProviderRateLimitError(
        "Rate limit reached.",
        retry_after_seconds=2.5,
    )

    assert error.retry_after_seconds == 2.5
    assert str(error) == "Rate limit reached."


def test_rate_limit_error_allows_missing_retry_after() -> None:
    error = ProviderRateLimitError("Rate limit reached.")

    assert error.retry_after_seconds is None
