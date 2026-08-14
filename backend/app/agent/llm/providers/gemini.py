"""Google Gemini LLM Provider integration using HTTP REST API."""

from datetime import datetime, timezone

import httpx

from app.agent.llm.base import BaseLLMProvider
from app.core.config import settings
from app.core.exceptions import APIException
from app.models.llm import LLMRequest, LLMResponse, TokenUsage


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini LLM Provider."""

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise APIException(
                message="GEMINI_API_KEY is not configured in backend environment variables.",
                status_code=400,
            )

        model_name = request.model or "gemini-1.5-flash"
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            f"?key={api_key}"
        )

        contents = []
        if request.system_prompt:
            sys_text = f"System Instruction: {request.system_prompt}"
            contents.append({"role": "user", "parts": [{"text": sys_text}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": request.prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens or 1024,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    raise APIException(
                        message=f"Gemini API error ({response.status_code}): {response.text}",
                        status_code=response.status_code,
                    )
                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise APIException(
                        message="Gemini returned no response candidates.",
                        status_code=500,
                    )

                generated_text = (
                    candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                )

                usage_meta = data.get("usageMetadata", {})
                prompt_tokens = usage_meta.get("promptTokenCount", len(request.prompt.split()))
                comp_tokens = usage_meta.get("candidatesTokenCount", len(generated_text.split()))

                return LLMResponse(
                    content=generated_text,
                    provider=self.provider_name,
                    model=model_name,
                    finish_reason=candidates[0].get("finishReason", "stop"),
                    usage=TokenUsage(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=comp_tokens,
                        total_tokens=prompt_tokens + comp_tokens,
                    ),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
        except httpx.HTTPError as e:
            raise APIException(
                message=f"Network error connecting to Gemini API: {e}",
                status_code=502,
            ) from e
