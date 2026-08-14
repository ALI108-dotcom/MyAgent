"""LLM Provider Factory for instantiating concrete provider strategies with API key validation."""

from app.agent.llm.base import BaseLLMProvider
from app.agent.llm.providers.gemini import GeminiLLMProvider
from app.agent.llm.providers.mock import MockLLMProvider
from app.agent.llm.providers.openai import OpenAILLMProvider
from app.core.config import settings
from app.core.exceptions import APIException


class LLMProviderFactory:
    """Factory creating LLM provider instances based on requested name or system configuration."""

    @staticmethod
    def get_provider(provider_name: str | None = None) -> BaseLLMProvider:
        """Instantiate and return the requested BaseLLMProvider strategy enforcing key configuration."""
        target_provider = (provider_name or settings.DEFAULT_LLM_PROVIDER).strip().lower()

        if target_provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise APIException(
                    message="LLM provider is not configured. OPENAI_API_KEY is not configured in the server environment.",
                    status_code=400,
                )
            return OpenAILLMProvider()
        elif target_provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise APIException(
                    message="LLM provider is not configured. GEMINI_API_KEY is not configured in the server environment.",
                    status_code=400,
                )
            return GeminiLLMProvider()
        elif target_provider == "mock":
            return MockLLMProvider()
        else:
            raise APIException(
                message=f"Unsupported LLM provider '{target_provider}'. "
                        f"Supported providers are: mock, gemini, openai.",
                status_code=400,
            )
