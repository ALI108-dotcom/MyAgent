"""ReAct Cognitive Engine Reasoning API Endpoints."""

import uuid
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.agent.reasoning.engine import cognitive_engine
from app.core.security import get_current_user
from app.models.auth import UserRead
from app.models.reasoning import ReasoningRequest, ReasoningResponse

router = APIRouter()


@router.post(
    "/solve",
    response_model=ReasoningResponse,
    status_code=status.HTTP_200_OK,
    summary="Solve high-level software engineering goal using ReAct Cognitive Engine",
    description="Orchestrates ReAct reasoning loop (Thought -> Action -> Observation).",
)
async def solve_reasoning_goal(
    request: ReasoningRequest,
    current_user: UserRead = Depends(get_current_user),
) -> ReasoningResponse:
    """Solve goal using ReAct cognitive engine."""
    return await cognitive_engine.solve_goal(request)


@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
    summary="Stream real-time agent reasoning events using SSE",
    description="Streams Server-Sent Events (SSE) representing live agent thoughts and events.",
)
async def stream_reasoning_goal(
    request: ReasoningRequest,
    current_user: UserRead = Depends(get_current_user),
) -> StreamingResponse:
    """Stream agent reasoning events over Server-Sent Events (SSE)."""
    task_id = f"task-{uuid.uuid4().hex[:8]}"

    async def event_generator() -> AsyncGenerator[str, None]:
        async for event in cognitive_engine.solve_goal_stream(request, task_id):
            json_payload = event.model_dump_json()
            yield f"id: {event.event_id}\nevent: {event.event_type}\ndata: {json_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/cancel/{task_id}",
    status_code=status.HTTP_200_OK,
    summary="Cancel active agent task mid-execution",
    description="Signals cancellation event to safely terminate active task.",
)
async def cancel_reasoning_task(
    task_id: str,
    current_user: UserRead = Depends(get_current_user),
) -> dict[str, Any]:
    """Cancel active task."""
    success = cognitive_engine.cancel_task(task_id)
    msg = f"Task '{task_id}' cancel signal sent." if success else f"Task '{task_id}' not found."
    return {
        "status": "success" if success else "failed",
        "message": msg,
    }


@router.post(
    "/approve/{task_id}",
    status_code=status.HTTP_200_OK,
    summary="Approve or reject dangerous agent operation",
    description="Signals human approval decision for paused operation.",
)
async def approve_reasoning_task(
    task_id: str,
    approved: bool = True,
    current_user: UserRead = Depends(get_current_user),
) -> dict[str, Any]:
    """Approve or reject paused task."""
    success = cognitive_engine.approve_task(task_id, approved)
    msg = f"Task '{task_id}' approval recorded." if success else f"Task '{task_id}' not found."
    return {
        "status": "success" if success else "failed",
        "message": msg,
    }
