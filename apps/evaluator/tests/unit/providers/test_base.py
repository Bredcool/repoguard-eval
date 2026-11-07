
"""Tests for the provider abstraction."""

import pytest

from repoguard_eval.providers import (
    BaseProvider,
    ProviderRequest,
    ProviderResponse,
)


def test_base_provider_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        BaseProvider()


def test_concrete_provider_implements_contract() -> None:
    class FakeProvider(BaseProvider):
        @property
        def name(self) -> str:
            return "fake"

        async def generate(
            self,
            request: ProviderRequest,
        ) -> ProviderResponse:
            return ProviderResponse(
                provider=self.name,
                model=request.model,
                task_id=request.task_id,
                experiment_id=request.experiment_id,
                raw_response={"mock": True},
            )

    provider = FakeProvider()

    assert provider.name == "fake"
    assert isinstance(provider, BaseProvider)
