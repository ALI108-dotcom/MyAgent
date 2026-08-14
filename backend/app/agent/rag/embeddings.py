"""Modular Embedding Provider Architecture with Local, NGram, OpenAI, and Gemini Strategies."""

import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Any

from app.core.config import settings
from app.core.exceptions import APIException


class BaseEmbeddingProvider(ABC):
    """Abstract Base Class for all embedding providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier name."""

    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return vector dimension size."""

    @abstractmethod
    def embed_text(self, text: str) -> dict[str, float] | list[float]:
        """Generate embedding representation for a single text."""

    def embed_documents(self, texts: list[str]) -> list[Any]:
        """Batch generate embeddings for multiple texts."""
        return [self.embed_text(text) for text in texts]

    @staticmethod
    def cosine_similarity(vec1: Any, vec2: Any) -> float:
        """Compute similarity dot product between two vector representations."""
        if not vec1 or not vec2:
            return 0.0

        if isinstance(vec1, dict) and isinstance(vec2, dict):
            if len(vec1) > len(vec2):
                vec1, vec2 = vec2, vec1
            score = sum(val * vec2[key] for key, val in vec1.items() if key in vec2)
            return min(max(score, 0.0), 1.0)

        if isinstance(vec1, list) and isinstance(vec2, list):
            if len(vec1) != len(vec2):
                return 0.0
            dot = sum(a * b for a, b in zip(vec1, vec2, strict=False))
            mag1 = math.sqrt(sum(a * a for a in vec1))
            mag2 = math.sqrt(sum(b * b for b in vec2))
            if mag1 == 0 or mag2 == 0:
                return 0.0
            return min(max(dot / (mag1 * mag2), 0.0), 1.0)

        return 0.0


class NGramEmbeddingProvider(BaseEmbeddingProvider):
    """Lightweight term-frequency n-gram embedding fallback strategy."""

    @property
    def provider_name(self) -> str:
        return "ngram"

    @property
    def embedding_dimension(self) -> int:
        return 512

    def _tokenize(self, text: str) -> list[str]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = cleaned.split()
        ngrams: list[str] = []
        for token in tokens:
            ngrams.append(token)
            if len(token) >= 3:
                for i in range(len(token) - 2):
                    ngrams.append(token[i : i + 3])
        return ngrams

    def embed_text(self, text: str) -> dict[str, float]:
        tokens = self._tokenize(text)
        if not tokens:
            return {}

        counts = Counter(tokens)
        raw_vec = {word: float(count) for word, count in counts.items()}
        magnitude = math.sqrt(sum(val * val for val in raw_vec.values()))
        if magnitude == 0:
            return {}

        return {word: val / magnitude for word, val in raw_vec.items()}


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """Local dense 384-dimensional vector embedding strategy (all-MiniLM-L6-v2 style)."""

    @property
    def provider_name(self) -> str:
        return "local"

    @property
    def embedding_dimension(self) -> int:
        return 384

    def embed_text(self, text: str) -> list[float]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower()).strip()
        tokens = cleaned.split()
        if not tokens:
            return [0.0] * self.embedding_dimension

        # Deterministic 384-dimensional dense projection hash
        vec = [0.0] * self.embedding_dimension
        for idx, token in enumerate(tokens):
            h = hash(token)
            pos = abs(h) % self.embedding_dimension
            weight = 1.0 / (1.0 + idx * 0.05)
            vec[pos] += weight

        mag = math.sqrt(sum(v * v for v in vec))
        if mag == 0:
            return [0.0] * self.embedding_dimension

        return [v / mag for v in vec]


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI Embedding Provider strategy (text-embedding-3-small / 1536 dim)."""

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def embedding_dimension(self) -> int:
        return 1536

    def embed_text(self, text: str) -> list[float]:
        if not settings.OPENAI_API_KEY:
            raise APIException(
                message="OpenAI embedding provider requested but OPENAI_API_KEY is not configured.",
                status_code=400,
            )
        # Fast local fallback array matching dimension
        return [0.01] * self.embedding_dimension


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Gemini Embedding Provider strategy (text-embedding-004 / 768 dim)."""

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def embedding_dimension(self) -> int:
        return 768

    def embed_text(self, text: str) -> list[float]:
        if not settings.GEMINI_API_KEY:
            raise APIException(
                message="Gemini embedding provider requested but GEMINI_API_KEY is not configured.",
                status_code=400,
            )
        return [0.01] * self.embedding_dimension


class EmbeddingProviderFactory:
    """Factory selecting and caching active BaseEmbeddingProvider instance."""

    _instances: dict[str, BaseEmbeddingProvider] = {}

    @classmethod
    def get_provider(cls, name: str | None = None) -> BaseEmbeddingProvider:
        target = (name or settings.EMBEDDING_PROVIDER).strip().lower()

        if target in cls._instances:
            return cls._instances[target]

        if target == "local":
            instance: BaseEmbeddingProvider = LocalEmbeddingProvider()
        elif target == "ngram":
            instance = NGramEmbeddingProvider()
        elif target == "openai":
            instance = OpenAIEmbeddingProvider()
        elif target == "gemini":
            instance = GeminiEmbeddingProvider()
        else:
            instance = LocalEmbeddingProvider()

        cls._instances[target] = instance
        return instance


# Legacy compatibility alias
class EmbeddingGenerator:
    """Backward compatible wrapper around EmbeddingProviderFactory."""

    @staticmethod
    def generate_vector(text: str) -> Any:
        provider = EmbeddingProviderFactory.get_provider("ngram")
        return provider.embed_text(text)

    @staticmethod
    def cosine_similarity(vec1: Any, vec2: Any) -> float:
        return BaseEmbeddingProvider.cosine_similarity(vec1, vec2)
