"""Unit tests for LLM provider abstraction, factory pattern, and endpoints."""

import pytest
from httpx import AsyncClient

from app.agent.llm.base import BaseLLMProvider
from app.agent.llm.factory import LLMProviderFactory
from app.agent.llm.providers.mock import MockLLMProvider
from app.core.exceptions import APIException
from app.models.llm import LLMRequest, LLMResponse


@pytest.mark.asyncio
async def test_mock_llm_provider_generate() -> None:
    """Verify MockLLMProvider produces structured response without external network calls."""
    provider = MockLLMProvider()
    request = LLMRequest(
        prompt="Write a function to calculate factorial in Python",
        provider="mock",
        temperature=0.7,
    )
    response = await provider.generate(request)

    assert isinstance(response, LLMResponse)
    assert response.provider == "mock"
    assert response.model == "mock-agent-v1"
    assert "def factorial" in response.content or len(response.content) > 0
    assert response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens > 0


def test_llm_provider_factory_valid() -> None:
    """Verify LLMProviderFactory returns correct provider instance for 'mock'."""
    provider = LLMProviderFactory.get_provider("mock")
    assert isinstance(provider, BaseLLMProvider)
    assert isinstance(provider, MockLLMProvider)


def test_llm_provider_factory_invalid() -> None:
    """Verify requesting an unsupported provider raises APIException 400."""
    with pytest.raises(APIException) as exc_info:
        LLMProviderFactory.get_provider("invalid_provider")

    assert exc_info.value.status_code == 400
    assert "Unsupported LLM provider" in exc_info.value.message


@pytest.mark.asyncio
async def test_llm_generate_endpoint_success(auth_client: AsyncClient) -> None:
    """Verify POST /api/v1/agent/llm/generate returns 200 OK with valid response schema."""
    payload = {
        "prompt": "Explain dependency injection simply.",
        "system_prompt": "You are ALI, AI Software Engineer",
        "provider": "mock",
        "temperature": 0.5,
    }
    response = await auth_client.post("/api/v1/agent/llm/generate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["provider"] == "mock"
    assert "content" in data
    assert len(data["content"]) > 0


@pytest.mark.asyncio
async def test_llm_generate_endpoint_missing_api_key(auth_client: AsyncClient) -> None:
    """Verify requesting Gemini or OpenAI without API key returns structured 400 error."""
    payload = {
        "prompt": "Test prompt",
        "provider": "gemini",
    }
    response = await auth_client.post("/api/v1/agent/llm/generate", json=payload)
    assert response.status_code == 400

    data = response.json()
    assert data["status"] == "error"
    assert "GEMINI_API_KEY is not configured" in data["message"]
