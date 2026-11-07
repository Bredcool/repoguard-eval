"""Tests for the OpenAI Responses API provider."""

import asyncio
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from repoguard_eval.config.provider import ProviderSettings
from repoguard_eval.providers import (
    OpenAIProvider,
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderRequest,
)


def make_settings(**overrides) -> ProviderSettings:
    values = {
        "provider": "openai",
        "api_key": SecretStr("test-api-key"),
        "model": "test-model",
        "base_url": "https://api.openai.com/v1",
        "timeout_seconds": 5,
        "max_retries": 0,
    }
    values.update(overrides)
    return ProviderSettings(**values)


def make_request(**overrides) -> ProviderRequest:
    values = {
        "task_id": "task-001",
        "experiment_id": uuid4(),
        "model": "test-model",
        "system_prompt": "You are a debugging agent.",
        "user_prompt": "Fix the bug in the repository.",
        "parameters": {},
    }
    values.update(overrides)
    return ProviderRequest(**values)


def make_response(
    status_code: int = 200,
    json_data: dict | None = None,
    headers: dict | None = None,
) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        json=json_data if json_data is not None else {},
        headers=headers,
    )


def make_provider(handler, settings=None) -> OpenAIProvider:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
    )
    return OpenAIProvider(
        settings=settings or make_settings(),
        client=client,
    )


def test_provider_name():
    provider = OpenAIProvider(make_settings())

    assert provider.name == "openai"


def test_provider_rejects_incomplete_configuration():
    settings = make_settings(api_key=None)

    with pytest.raises(ProviderConfigurationError):
        OpenAIProvider(settings)


def test_provider_rejects_other_provider():
    settings = make_settings(provider="anthropic")

    with pytest.raises(ProviderConfigurationError):
        OpenAIProvider(settings)


def test_generate_sends_responses_api_request():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = request.headers
        captured["body"] = request.read()
        return make_response(
            json_data={
                "id": "resp_test123",
                "model": "test-model",
                "status": "completed",
                "usage": {
                    "input_tokens": 120,
                    "output_tokens": 80,
                    "total_tokens": 200,
                },
                "output": [],
            }
        )

    async def run():
        provider = make_provider(handler)
        request = make_request()

        try:
            result = await provider.generate(request)
        finally:
            await provider._client.aclose()

        return request, result

    request, result = asyncio.run(run())

    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["headers"]["Authorization"] == "Bearer test-api-key"
    assert captured["headers"]["Content-Type"] == "application/json"
    assert captured["headers"]["X-Client-Request-Id"] == str(
        request.experiment_id
    )

    import json

    body = json.loads(captured["body"])

    assert body["model"] == "test-model"
    assert body["input"] == [
        {
            "role": "system",
            "content": "You are a debugging agent.",
        },
        {
            "role": "user",
            "content": "Fix the bug in the repository.",
        },
    ]

    assert result.provider == "openai"
    assert result.model == "test-model"
    assert result.task_id == "task-001"
    assert result.experiment_id == request.experiment_id
    assert result.response_id == "resp_test123"
    assert result.finish_reason == "completed"
    assert result.usage.input_tokens == 120
    assert result.usage.output_tokens == 80
    assert result.usage.total_tokens == 200
    assert result.raw_response["id"] == "resp_test123"


def test_generate_uses_configured_output_token_limit():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured["body"] = json.loads(request.read())
        return make_response(json_data={"model": "test-model"})

    async def run():
        provider = make_provider(
            handler,
            settings=make_settings(max_output_tokens=1024),
        )

        try:
            await provider.generate(make_request())
        finally:
            await provider._client.aclose()

    asyncio.run(run())

    assert captured["body"]["max_output_tokens"] == 1024


def test_generate_maps_authentication_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return make_response(status_code=401)

    async def run():
        provider = make_provider(handler)

        try:
            with pytest.raises(ProviderAuthenticationError):
                await provider.generate(make_request())
        finally:
            await provider._client.aclose()

    asyncio.run(run())


def test_generate_maps_rate_limit_and_retry_after():
    def handler(request: httpx.Request) -> httpx.Response:
        return make_response(
            status_code=429,
            headers={"Retry-After": "2.5"},
        )

    async def run():
        provider = make_provider(handler)

        try:
            with pytest.raises(ProviderRateLimitError) as exc_info:
                await provider.generate(make_request())
        finally:
            await provider._client.aclose()

        assert exc_info.value.retry_after_seconds == 2.5

    asyncio.run(run())


def test_generate_maps_server_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return make_response(status_code=500)

    async def run():
        provider = make_provider(handler)

        try:
            with pytest.raises(ProviderRequestError):
                await provider.generate(make_request())
        finally:
            await provider._client.aclose()

    asyncio.run(run())


def test_generate_maps_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("simulated timeout")

    async def run():
        provider = make_provider(handler)

        try:
            with pytest.raises(ProviderTimeoutError):
                await provider.generate(make_request())
        finally:
            await provider._client.aclose()

    asyncio.run(run())


def test_generate_maps_network_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated connection error")

    async def run():
        provider = make_provider(handler)

        try:
            with pytest.raises(ProviderRequestError):
                await provider.generate(make_request())
        finally:
            await provider._client.aclose()

    asyncio.run(run())


def test_generate_rejects_invalid_json():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            content=b"not-json",
        )

    async def run():
        provider = make_provider(handler)

        try:
            with pytest.raises(ProviderResponseError):
                await provider.generate(make_request())
        finally:
            await provider._client.aclose()

    asyncio.run(run())


def test_generate_rejects_non_object_json():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=["unexpected", "array"],
        )

    async def run():
        provider = make_provider(handler)

        try:
            with pytest.raises(ProviderResponseError):
                await provider.generate(make_request())
        finally:
            await provider._client.aclose()

    asyncio.run(run())


def test_generate_handles_missing_usage():
    def handler(request: httpx.Request) -> httpx.Response:
        return make_response(
            json_data={
                "id": "resp_without_usage",
                "model": "test-model",
                "status": "completed",
            }
        )

    async def run():
        provider = make_provider(handler)

        try:
            result = await provider.generate(make_request())
        finally:
            await provider._client.aclose()

        return result

    result = asyncio.run(run())

    assert result.usage is None


def test_generate_does_not_leak_api_key_in_errors():
    def handler(request: httpx.Request) -> httpx.Response:
        return make_response(status_code=500)

    async def run():
        provider = make_provider(handler)

        try:
            with pytest.raises(ProviderRequestError) as exc_info:
                await provider.generate(make_request())
        finally:
            await provider._client.aclose()

        assert "test-api-key" not in str(exc_info.value)

    asyncio.run(run())


def test_generate_retries_temporary_server_error(monkeypatch):
    calls = {"count": 0}
    sleeps = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1

        if calls["count"] == 1:
            return make_response(status_code=503)

        return make_response(
            json_data={
                "id": "resp_after_retry",
                "model": "test-model",
                "status": "completed",
            }
        )

    async def fake_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(
        "repoguard_eval.providers.openai.asyncio.sleep",
        fake_sleep,
    )
    monkeypatch.setattr(
        "repoguard_eval.providers.openai.random.uniform",
        lambda minimum, maximum: minimum,
    )

    async def run():
        provider = make_provider(
            handler,
            settings=make_settings(max_retries=2),
        )

        try:
            return await provider.generate(make_request())
        finally:
            await provider._client.aclose()

    result = asyncio.run(run())

    assert result.response_id == "resp_after_retry"
    assert calls["count"] == 2
    assert len(sleeps) == 1


def test_generate_retries_rate_limit_using_retry_after(monkeypatch):
    calls = {"count": 0}
    sleeps = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1

        if calls["count"] == 1:
            return make_response(
                status_code=429,
                headers={"Retry-After": "2"},
                json_data={
                    "error": {
                        "type": "rate_limit_error",
                        "code": "rate_limit_exceeded",
                    }
                },
            )

        return make_response(
            json_data={
                "id": "resp_after_rate_limit",
                "model": "test-model",
                "status": "completed",
            }
        )

    async def fake_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(
        "repoguard_eval.providers.openai.asyncio.sleep",
        fake_sleep,
    )
    monkeypatch.setattr(
        "repoguard_eval.providers.openai.random.uniform",
        lambda minimum, maximum: minimum,
    )

    async def run():
        provider = make_provider(
            handler,
            settings=make_settings(max_retries=1),
        )

        try:
            return await provider.generate(make_request())
        finally:
            await provider._client.aclose()

    result = asyncio.run(run())

    assert result.response_id == "resp_after_rate_limit"
    assert calls["count"] == 2
    assert sleeps == [2.0]


def test_generate_does_not_retry_quota_error(monkeypatch):
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return make_response(
            status_code=429,
            json_data={
                "error": {
                    "type": "insufficient_quota",
                    "code": "insufficient_quota",
                }
            },
        )

    async def fake_sleep(delay):
        pytest.fail("Quota errors must not be retried.")

    monkeypatch.setattr(
        "repoguard_eval.providers.openai.asyncio.sleep",
        fake_sleep,
    )

    async def run():
        provider = make_provider(
            handler,
            settings=make_settings(max_retries=3),
        )

        try:
            with pytest.raises(ProviderRateLimitError):
                await provider.generate(make_request())
        finally:
            await provider._client.aclose()

    asyncio.run(run())

    assert calls["count"] == 1


def test_generate_stops_after_max_retries(monkeypatch):
    calls = {"count": 0}
    sleeps = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return make_response(status_code=503)

    async def fake_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(
        "repoguard_eval.providers.openai.asyncio.sleep",
        fake_sleep,
    )
    monkeypatch.setattr(
        "repoguard_eval.providers.openai.random.uniform",
        lambda minimum, maximum: minimum,
    )

    async def run():
        provider = make_provider(
            handler,
            settings=make_settings(max_retries=2),
        )

        try:
            with pytest.raises(ProviderRequestError):
                await provider.generate(make_request())
        finally:
            await provider._client.aclose()

    asyncio.run(run())

    assert calls["count"] == 3
    assert len(sleeps) == 2


def test_retry_after_supports_http_date():
    from datetime import datetime, timedelta, timezone
    from email.utils import format_datetime

    from repoguard_eval.providers.openai import OpenAIProvider

    future = datetime.now(timezone.utc) + timedelta(seconds=30)
    header = format_datetime(future)

    delay = OpenAIProvider._parse_retry_after(header)

    assert delay is not None
    assert 0 <= delay <= 31


def test_retry_delay_rejects_excessive_wait():
    from repoguard_eval.providers.openai import OpenAIProvider

    delay = OpenAIProvider._retry_delay(
        attempt=0,
        retry_after_seconds=120,
    )

    assert delay is None