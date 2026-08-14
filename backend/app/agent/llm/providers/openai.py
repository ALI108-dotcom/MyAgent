"""OpenAI / Compatible LLM Provider integration using HTTP REST API."""

from datetime import datetime, timezone

import httpx

from app.agent.llm.base import BaseLLMProvider
from app.core.config import settings
from app.core.exceptions import APIException
from app.models.llm import LLMRequest, LLMResponse, TokenUsage


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI / OpenAI-Compatible LLM Provider."""

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise APIException(
                message="OPENAI_API_KEY is not configured in backend environment variables.",
                status_code=400,
            )

        model_name = request.model or "gpt-4o-mini"
        url = "https://api.openai.com/v1/chat/completions"

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens or 1024,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    raise APIException(
                        message=f"OpenAI API error ({response.status_code}): {response.text}",
                        status_code=response.status_code,
                    )
                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    raise APIException(message="OpenAI returned no choices.", status_code=500)

                generated_text = choices[0].get("message", {}).get("content", "")
                usage_meta = data.get("usage", {})

                return LLMResponse(
                    content=generated_text,
                    provider=self.provider_name,
                    model=model_name,
                    finish_reason=choices[0].get("finish_reason", "stop"),
                    usage=TokenUsage(
                        prompt_tokens=usage_meta.get("prompt_tokens", 0),
                        completion_tokens=usage_meta.get("completion_tokens", 0),
                        total_tokens=usage_meta.get("total_tokens", 0),
                    ),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
        except httpx.HTTPError as e:
            raise APIException(
                message=f"Network error connecting to OpenAI API: {e}",
                status_code=502,
            ) from e
