
"""Provider integration error hierarchy."""


class ProviderError(Exception):
    """Base exception for provider integration failures."""


class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration is invalid or incomplete."""


class ProviderAuthenticationError(ProviderError):
    """Raised when provider authentication fails."""


class ProviderRateLimitError(ProviderError):
    """Raised when a provider rate limit is reached."""

    def __init__(
        self,
        message: str,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request times out."""


class ProviderRequestError(ProviderError):
    """Raised when a provider rejects or cannot process a request."""


class ProviderResponseError(ProviderError):
    """Raised when a provider response is invalid or cannot be parsed."""
