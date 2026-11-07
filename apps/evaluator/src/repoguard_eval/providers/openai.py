"""OpenAI Responses API provider implementation."""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from repoguard_eval.config.provider import ProviderSettings
from repoguard_eval.providers.base import BaseProvider
from repoguard_eval.providers.errors import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderResponseError,
    ProviderTimeoutError,
)
from repoguard_eval.providers.schemas.response import (
    ProviderRequest,
    ProviderResponse,
    TokenUsage,
)


class OpenAIProvider(BaseProvider):
    """Send model requests to the OpenAI Responses API."""

    RETRYABLE_STATUS_CODES = {500, 502, 503, 504}
    MAX_RETRY_WAIT_SECONDS = 60.0

    NON_RETRYABLE_RATE_LIMIT_CODES = {
        "insufficient_quota",
        "billing_hard_limit_reached",
        "usage_limit_reached",
    }

    def __init__(
        self,
        settings: ProviderSettings,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._client = client

        if settings.provider != "openai":
            raise ProviderConfigurationError(
                "OpenAIProvider requires provider='openai'."
            )

        try:
            self._api_key, self._configured_model = settings.require_ready()
        except ValueError as exc:
            raise ProviderConfigurationError(str(exc)) from exc

    @property
    def name(self) -> str:
        return "openai"

    @property
    def _endpoint(self) -> str:
        return f"{str(self._settings.base_url).rstrip('/')}/responses"

    def _build_payload(self, request: ProviderRequest) -> dict[str, Any]:
        """Build a Responses API request without allowing parameter overrides."""

        payload: dict[str, Any] = {
            "model": request.model,
            "input": [
                {
                    "role": "system",
                    "content": request.system_prompt,
                },
                {
                    "role": "user",
                    "content": request.user_prompt,
                },
            ],
        }

        if self._settings.max_output_tokens is not None:
            payload["max_output_tokens"] = self._settings.max_output_tokens

        return payload

    @staticmethod
    def _parse_retry_after(value: str | None) -> float | None:
        """Parse Retry-After as seconds or an HTTP date."""

        if not value:
            return None

        try:
            return max(0.0, float(value))
        except ValueError:
            pass

        try:
            retry_at = parsedate_to_datetime(value)

            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)

            delay = (retry_at - datetime.now(timezone.utc)).total_seconds()
            return max(0.0, delay)
        except (TypeError, ValueError, OverflowError):
            return None

    @staticmethod
    def _extract_usage(data: dict[str, Any]) -> TokenUsage | None:
        """Extract valid token usage metadata without rejecting the response."""

        usage = data.get("usage")

        if not isinstance(usage, dict):
            return None

        def valid_count(value: Any) -> int | None:
            if (
                isinstance(value, int)
                and not isinstance(value, bool)
                and value >= 0
            ):
                return value
            return None

        input_tokens = valid_count(usage.get("input_tokens"))
        output_tokens = valid_count(usage.get("output_tokens"))
        total_tokens = valid_count(usage.get("total_tokens"))

        if all(
            value is None
            for value in (input_tokens, output_tokens, total_tokens)
        ):
            return None

        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

    @classmethod
    def _is_retryable_rate_limit(cls, response: httpx.Response) -> bool:
        """Distinguish temporary rate limits from quota or billing restrictions."""

        try:
            data = response.json()
        except ValueError:
            return True

        if not isinstance(data, dict):
            return True

        error = data.get("error")
        if not isinstance(error, dict):
            return True

        error_codes = {
            str(error.get("code", "")).lower(),
            str(error.get("type", "")).lower(),
        }

        return not bool(
            error_codes.intersection(cls.NON_RETRYABLE_RATE_LIMIT_CODES)
        )

    @classmethod
    def _retry_delay(
        cls,
        attempt: int,
        retry_after_seconds: float | None = None,
        backoff_seconds: float = 1.0,
    ) -> float | None:
        """Calculate a bounded retry delay with jitter."""

        if retry_after_seconds is not None:
            jitter = random.uniform(0.0, 1.0)
            delay = retry_after_seconds + jitter
        else:
            exponential_cap = min(
                backoff_seconds * (2**attempt),
                30.0,
            )
            delay = random.uniform(0.0, exponential_cap)

        if delay > cls.MAX_RETRY_WAIT_SECONDS:
            return None

        return delay

    async def _post(
        self,
        payload: dict[str, Any],
        experiment_id: str,
    ) -> httpx.Response:
        """Send one HTTP request using an injected or locally owned client."""

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "X-Client-Request-Id": experiment_id,
        }

        if self._client is not None:
            return await self._client.post(
                self._endpoint,
                headers=headers,
                json=payload,
            )

        timeout = httpx.Timeout(self._settings.timeout_seconds)

        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.post(
                self._endpoint,
                headers=headers,
                json=payload,
            )

    async def _post_with_retries(
        self,
        payload: dict[str, Any],
        experiment_id: str,
    ) -> httpx.Response:
        """Send a request with bounded retries for transient failures."""

        max_retries = self._settings.max_retries

        for attempt in range(max_retries + 1):
            try:
                response = await self._post(payload, experiment_id)

            except httpx.TimeoutException as exc:
                if attempt >= max_retries:
                    raise ProviderTimeoutError(
                        "OpenAI request exceeded the configured timeout."
                    ) from exc

                delay = self._retry_delay(
                    attempt,
                    backoff_seconds=self._settings.retry_backoff_seconds,
                )

                if delay is None:
                    raise ProviderTimeoutError(
                        "OpenAI request timed out and retry wait exceeded the limit."
                    ) from exc

                await asyncio.sleep(delay)
                continue

            except httpx.RequestError as exc:
                if attempt >= max_retries:
                    raise ProviderRequestError(
                        "Unable to complete the OpenAI HTTP request."
                    ) from exc

                delay = self._retry_delay(
                    attempt,
                    backoff_seconds=self._settings.retry_backoff_seconds,
                )

                if delay is None:
                    raise ProviderRequestError(
                        "OpenAI request failed and retry wait exceeded the limit."
                    ) from exc

                await asyncio.sleep(delay)
                continue

            retryable = response.status_code in self.RETRYABLE_STATUS_CODES

            if response.status_code == 429:
                retryable = self._is_retryable_rate_limit(response)

            if not retryable or attempt >= max_retries:
                return response

            retry_after = self._parse_retry_after(
                response.headers.get("Retry-After")
            )

            delay = self._retry_delay(
                attempt,
                retry_after_seconds=retry_after,
                backoff_seconds=self._settings.retry_backoff_seconds,
            )

            if delay is None:
                return response

            await asyncio.sleep(delay)

        raise ProviderRequestError("OpenAI retry loop ended unexpectedly.")

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Send a request and preserve the complete raw API response."""

        payload = self._build_payload(request)

        response = await self._post_with_retries(
            payload=payload,
            experiment_id=str(request.experiment_id),
        )

        if response.status_code in (401, 403):
            raise ProviderAuthenticationError(
                f"OpenAI authentication failed (HTTP {response.status_code})."
            )

        if response.status_code == 429:
            raise ProviderRateLimitError(
                "OpenAI rate limit or quota restriction was reached.",
                retry_after_seconds=self._parse_retry_after(
                    response.headers.get("Retry-After")
                ),
            )

        if response.is_error:
            raise ProviderRequestError(
                f"OpenAI request failed (HTTP {response.status_code})."
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderResponseError(
                "OpenAI returned a response that is not valid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise ProviderResponseError(
                "OpenAI response must be a JSON object."
            )

        response_model = data.get("model")
        if not isinstance(response_model, str) or not response_model.strip():
            response_model = request.model

        response_id = data.get("id")
        if not isinstance(response_id, str):
            response_id = None

        status = data.get("status")
        if not isinstance(status, str):
            status = None

        return ProviderResponse(
            provider=self.name,
            model=response_model,
            task_id=request.task_id,
            experiment_id=request.experiment_id,
            usage=self._extract_usage(data),
            response_id=response_id,
            finish_reason=status,
            raw_response=data,
        )