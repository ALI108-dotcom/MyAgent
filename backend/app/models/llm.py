"""Pydantic schemas for LLM Request and Response models."""

from typing import Literal

from pydantic import BaseModel, Field


class LLMRequest(BaseModel):
    """Payload model for generating LLM completions."""

    prompt: str = Field(..., min_length=1, description="Input user prompt")
    system_prompt: str | None = Field(
        default=None,
        description="Optional system instruction for agent behavior"
    )
    provider: Literal["mock", "gemini", "openai"] | None = Field(
        default=None,
        description="Override default LLM provider"
    )
    model: str | None = Field(
        default=None,
        description="Override default model identifier"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Sampling temperature between 0.0 and 1.0"
    )
    max_tokens: int | None = Field(
        default=1024,
        gt=0,
        description="Maximum completion tokens to generate"
    )


class TokenUsage(BaseModel):
    """Token consumption metadata."""

    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class LLMResponse(BaseModel):
    """Standardized output model for LLM completions."""

    content: str = Field(..., description="Generated text completion")
    provider: str = Field(..., description="LLM provider name (e.g. mock, gemini, openai)")
    model: str = Field(..., description="Model identifier used for generation")
    finish_reason: str = Field(default="stop", description="Reason completion finished")
    usage: TokenUsage = Field(default_factory=TokenUsage, description="Token usage details")
    timestamp: str = Field(..., description="ISO 8601 server completion timestamp")
