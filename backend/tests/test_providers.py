"""
Unit tests for LLM provider implementations. These don't require a live
Ollama instance or Anthropic API key — they test error-handling paths,
which is exactly where resilience matters most.
"""
import pytest
import httpx

from app.providers.ollama_provider import OllamaProvider
from app.providers.anthropic_provider import AnthropicProvider


@pytest.mark.asyncio
async def test_ollama_provider_connect_error_yields_visible_message(monkeypatch):
    """If Ollama is unreachable, the provider should yield a clear in-chat
    error rather than raising an unhandled exception."""
    provider = OllamaProvider(base_url="http://localhost:1", model="llama3.2:3b")

    chunks = []
    async for chunk in provider.generate_response(
        messages=[{"role": "user", "content": "hello"}],
        system_prompt="test",
    ):
        chunks.append(chunk)

    joined = "".join(chunks)
    assert "Error" in joined
    assert "Ollama" in joined


@pytest.mark.asyncio
async def test_ollama_provider_non_200_status(monkeypatch):
    """A non-200 response from Ollama should surface the status code, not crash."""

    class FakeResponse:
        status_code = 500

        async def aiter_lines(self):
            return
            yield  # pragma: no cover

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        def stream(self, method, url, json):
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: FakeClient())

    provider = OllamaProvider(base_url="http://fake", model="llama3.2:3b")
    chunks = []
    async for chunk in provider.generate_response(
        messages=[{"role": "user", "content": "hi"}], system_prompt="test"
    ):
        chunks.append(chunk)

    assert "500" in "".join(chunks)


@pytest.mark.asyncio
async def test_anthropic_provider_missing_key_yields_visible_message():
    """No API key configured should produce a clear error, not a crash."""
    provider = AnthropicProvider(api_key="", model="claude-sonnet-4-6")

    chunks = []
    async for chunk in provider.generate_response(
        messages=[{"role": "user", "content": "hello"}],
        system_prompt="test",
    ):
        chunks.append(chunk)

    joined = "".join(chunks)
    assert "ANTHROPIC_API_KEY" in joined