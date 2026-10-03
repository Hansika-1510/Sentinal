"""Resilience of the live LLM provider against rate limiting.

The autonomous pipeline deliberately treats an investigation failure as non-fatal, which
means an unretried 429 reaches the operator as an incident with no RCA and no proposals.
These tests pin the retry policy that closes that gap.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import httpx
import pytest
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import LLMIntegrationException
from app.integrations.llm import OpenRouterLLMProvider

_URL = "https://openrouter.ai/api/v1/chat/completions"


class _Schema(BaseModel):
    ok: bool


def _response(status_code: int, headers: dict | None = None, content: str | None = '{"ok": true}', finish_reason: str = "stop") -> httpx.Response:
    return httpx.Response(
        status_code,
        json={"choices": [{"message": {"content": content}, "finish_reason": finish_reason}]},
        headers=headers or {},
        request=httpx.Request("POST", _URL),
    )


@pytest.fixture
def no_sleep(monkeypatch):
    """Capture backoff delays instead of actually waiting."""
    sleeps: list[float] = []

    async def fake_sleep(seconds: float):
        sleeps.append(seconds)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    return sleeps


def _provider() -> OpenRouterLLMProvider:
    return OpenRouterLLMProvider(api_key="test-key", model="test/model")


def test_retries_a_429_then_succeeds(monkeypatch, no_sleep):
    """A single rate limit must not cost the incident its RCA."""
    calls = []

    async def fake_post(self, url, **kwargs):
        calls.append(url)
        return _response(429) if len(calls) == 1 else _response(200)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = asyncio.run(_provider().generate_structured("prompt", _Schema))

    assert result.ok is True
    assert len(calls) == 2, "the request should have been retried exactly once"
    assert len(no_sleep) == 1, "one backoff before the successful retry"


def test_gives_up_after_the_configured_attempt_budget(monkeypatch, no_sleep):
    """Retries are bounded, so a hard rate limit still fails fast rather than hanging."""
    calls = []

    async def fake_post(self, url, **kwargs):
        calls.append(url)
        return _response(429)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    with pytest.raises(LLMIntegrationException):
        asyncio.run(_provider().generate_structured("prompt", _Schema))

    assert len(calls) == settings.LLM_MAX_ATTEMPTS
    assert len(no_sleep) == settings.LLM_MAX_ATTEMPTS - 1


def test_honours_retry_after_header(monkeypatch, no_sleep):
    """The provider's own backoff instruction wins over our exponential guess."""
    calls = []

    async def fake_post(self, url, **kwargs):
        calls.append(url)
        return _response(429, headers={"Retry-After": "7"}) if len(calls) == 1 else _response(200)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    asyncio.run(_provider().generate_structured("prompt", _Schema))

    assert no_sleep == [7.0]


def test_does_not_retry_a_client_error(monkeypatch, no_sleep):
    """A malformed request is not made better by repeating it."""
    calls = []

    async def fake_post(self, url, **kwargs):
        calls.append(url)
        return _response(400)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    with pytest.raises(LLMIntegrationException):
        asyncio.run(_provider().generate_structured("prompt", _Schema))

    assert len(calls) == 1
    assert no_sleep == []


def test_retries_a_transport_error(monkeypatch, no_sleep):
    """Connection blips are transient too."""
    calls = []

    async def fake_post(self, url, **kwargs):
        calls.append(url)
        if len(calls) == 1:
            raise httpx.ConnectError("connection reset")
        return _response(200)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = asyncio.run(_provider().generate_structured("prompt", _Schema))

    assert result.ok is True
    assert len(calls) == 2


def test_backoff_is_bounded_and_grows(monkeypatch):
    """Delays must escalate but never exceed the configured ceiling."""
    monkeypatch.setattr(settings, "LLM_RETRY_BASE_DELAY_SECONDS", 1.0)
    monkeypatch.setattr(settings, "LLM_RETRY_MAX_DELAY_SECONDS", 20.0)

    delays = [OpenRouterLLMProvider._retry_delay(attempt) for attempt in range(3)]

    assert delays[0] < delays[2], "backoff should escalate with the attempt count"
    assert all(0 < delay <= settings.LLM_RETRY_MAX_DELAY_SECONDS for delay in delays)


def test_retry_after_is_clamped_to_the_ceiling(monkeypatch):
    monkeypatch.setattr(settings, "LLM_RETRY_MAX_DELAY_SECONDS", 20.0)

    delay = OpenRouterLLMProvider._retry_delay(0, _response(429, headers={"Retry-After": "600"}))

    assert delay == 20.0


def _http_date(seconds_from_now: float) -> str:
    """An RFC 9110 HTTP-date, the other legal spelling of Retry-After."""
    return format_datetime(datetime.now(timezone.utc) + timedelta(seconds=seconds_from_now), usegmt=True)


def test_honours_a_dated_retry_after_header(monkeypatch):
    """Providers send Retry-After as an HTTP-date too, and that form must not be ignored.

    It used to raise ValueError inside float() and fall through to our exponential guess,
    discarding the delay the provider explicitly asked for.
    """
    monkeypatch.setattr(settings, "LLM_RETRY_MAX_DELAY_SECONDS", 60.0)

    delay = OpenRouterLLMProvider._retry_delay(0, _response(429, headers={"Retry-After": _http_date(12)}))

    assert 9.0 <= delay <= 12.5, f"expected roughly the 12s the header asked for, got {delay}"


def test_a_past_dated_retry_after_means_retry_now(monkeypatch):
    monkeypatch.setattr(settings, "LLM_RETRY_MAX_DELAY_SECONDS", 60.0)

    delay = OpenRouterLLMProvider._retry_delay(0, _response(429, headers={"Retry-After": _http_date(-30)}))

    assert delay == 0.0


def test_an_unparseable_retry_after_falls_back_to_backoff(monkeypatch):
    """A header we cannot read must not become a zero-delay hammer on the provider."""
    monkeypatch.setattr(settings, "LLM_RETRY_BASE_DELAY_SECONDS", 1.0)
    monkeypatch.setattr(settings, "LLM_RETRY_MAX_DELAY_SECONDS", 20.0)

    delay = OpenRouterLLMProvider._retry_delay(0, _response(429, headers={"Retry-After": "soon"}))

    assert 0 < delay <= 1.5, f"expected the jittered backoff band, got {delay}"


# ------------------------------------------------------ truncated / empty completions


def test_empty_content_names_the_truncation_cause(monkeypatch, no_sleep):
    """A reasoning model that exhausts max_tokens returns content=None.

    That failure must explain itself, because the orchestrator only logs the message.
    """
    async def fake_post(self, url, **kwargs):
        return _response(200, content=None, finish_reason="length")

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    with pytest.raises(LLMIntegrationException) as exc:
        asyncio.run(_provider().generate_structured("prompt", _Schema))

    assert "no content" in str(exc.value)
    assert "length" in str(exc.value)


def test_truncated_json_names_the_finish_reason(monkeypatch, no_sleep):
    """A half-written JSON object is the other symptom of the same truncation."""
    async def fake_post(self, url, **kwargs):
        return _response(200, content='{"ok": tr', finish_reason="length")

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    with pytest.raises(LLMIntegrationException) as exc:
        asyncio.run(_provider().generate_structured("prompt", _Schema))

    assert "unparseable JSON" in str(exc.value)
    assert "length" in str(exc.value)


def test_token_budget_clears_a_reasoning_models_overhead():
    """The cap must leave room for reasoning *and* the RCA JSON it precedes.

    Regression guard: at a 4096 cap qwen3.8-27b:free spent 3712 tokens reasoning and
    returned a truncated object, so every autonomous investigation failed.
    """
    assert settings.LLM_MAX_TOKENS >= 8192
