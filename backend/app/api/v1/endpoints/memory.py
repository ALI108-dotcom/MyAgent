"""Memory and Project Context API Endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status

from app.agent.memory.context_builder import ProjectContextBuilder
from app.agent.memory.session_manager import session_manager
from app.core.security import get_current_user
from app.models.auth import UserRead
from app.models.memory import (
    AddMessageRequest,
    ChatMessage,
    CreateSessionRequest,
    ProjectContext,
    SessionMemory,
)

router = APIRouter()


@router.post(
    "/sessions",
    response_model=SessionMemory,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent conversation session",
    description="Creates and persists a new SessionMemory instance owned by current user.",
)
async def create_session(
    request: CreateSessionRequest,
    current_user: UserRead = Depends(get_current_user),
) -> SessionMemory:
    """Create new session."""
    return await session_manager.create_session(
        title=request.title,
        initial_system_prompt=request.initial_system_prompt,
        user_id=current_user.user_id,
    )


@router.get(
    "/sessions",
    response_model=list[SessionMemory],
    status_code=status.HTTP_200_OK,
    summary="List all active agent sessions",
    description="Returns ordered list of session memories owned by current user (or all if admin).",
)
async def list_sessions(
    current_user: UserRead = Depends(get_current_user),
) -> list[SessionMemory]:
    """List sessions."""
    return await session_manager.list_sessions(
        requesting_user_id=current_user.user_id,
        is_admin=(current_user.role == "admin"),
    )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionMemory,
    status_code=status.HTTP_200_OK,
    summary="Get conversation history for a session",
    description="Retrieves SessionMemory model after verifying user ownership.",
)
async def get_session(
    session_id: str,
    current_user: UserRead = Depends(get_current_user),
) -> SessionMemory:
    """Get session by ID."""
    return await session_manager.get_session(
        session_id,
        requesting_user_id=current_user.user_id,
        is_admin=(current_user.role == "admin"),
    )


@router.post(
    "/sessions/{session_id}/messages",
    response_model=SessionMemory,
    status_code=status.HTTP_200_OK,
    summary="Append a chat message to session history",
    description="Adds a message to session memory after verifying ownership.",
)
async def add_message(
    session_id: str,
    request: AddMessageRequest,
    current_user: UserRead = Depends(get_current_user),
) -> SessionMemory:
    """Append message to session."""
    msg = ChatMessage(
        role=request.role,
        content=request.content,
        timestamp=datetime.now(timezone.utc).isoformat(),
        metadata=request.metadata,
    )
    return await session_manager.add_message(
        session_id,
        msg,
        requesting_user_id=current_user.user_id,
        is_admin=(current_user.role == "admin"),
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a session memory",
    description="Removes specified session after verifying user ownership.",
)
async def delete_session(
    session_id: str,
    current_user: UserRead = Depends(get_current_user),
) -> dict[str, str]:
    """Delete session."""
    success = await session_manager.delete_session(
        session_id,
        requesting_user_id=current_user.user_id,
        is_admin=(current_user.role == "admin"),
    )
    msg = f"Session '{session_id}' deleted." if success else f"Session '{session_id}' not found."
    return {
        "status": "success" if success else "failed",
        "message": msg,
    }


@router.get(
    "/context",
    response_model=ProjectContext,
    status_code=status.HTTP_200_OK,
    summary="Generate workspace project context summary",
    description="Scans workspace, respects .gitignore, builds directory tree, and lists key files.",
)
async def get_project_context(
    current_user: UserRead = Depends(get_current_user),
) -> ProjectContext:
    """Generate workspace context summary."""
    return ProjectContextBuilder.build_context()
