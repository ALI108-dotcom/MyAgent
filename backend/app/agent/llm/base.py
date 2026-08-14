"""Abstract Base Class for LLM Providers."""

from abc import ABC, abstractmethod

from app.models.llm import LLMRequest, LLMResponse


class BaseLLMProvider(ABC):
    """Unified interface for all LLM providers (Mock, Gemini, OpenAI)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return canonical provider string identifier."""

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Asynchronously generate LLM completion for given request."""
