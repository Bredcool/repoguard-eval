
"""Abstract interface for AI model providers."""

from abc import ABC, abstractmethod

from repoguard_eval.providers.schemas.response import (
    ProviderRequest,
    ProviderResponse,
)


class BaseProvider(ABC):
    """Contract implemented by every AI model provider."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider identifier."""

    @abstractmethod
    async def generate(
        self,
        request: ProviderRequest,
    ) -> ProviderResponse:
        """Send a request and return a normalized model response."""
