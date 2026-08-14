"""LLM Subsystem API Endpoints."""

from fastapi import APIRouter, Depends, status

from app.agent.llm.base import BaseLLMProvider
from app.agent.llm.factory import LLMProviderFactory
from app.core.security import get_current_user
from app.models.auth import UserRead
from app.models.llm import LLMRequest, LLMResponse

router = APIRouter()


@router.post(
    "/generate",
    response_model=LLMResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate text completion from selected LLM provider",
    description="Routes completion request to the configured LLM provider strategy.",
)
async def generate_llm_completion(
    request: LLMRequest,
    current_user: UserRead = Depends(get_current_user),
) -> LLMResponse:
    """Generate completion."""
    provider: BaseLLMProvider = LLMProviderFactory.get_provider(request.provider)
    return await provider.generate(request)
