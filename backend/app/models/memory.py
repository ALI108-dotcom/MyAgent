"""Pydantic schemas for Session Memory, Chat History, and Project Context."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single message in a conversational session history."""

    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Message author role"
    )
    content: str = Field(..., min_length=1, description="Message text content")
    timestamp: str = Field(..., description="ISO 8601 message timestamp")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional extra metadata (tool calls, execution stats)"
    )


class SessionMemory(BaseModel):
    """Conversational session memory object."""

    session_id: str = Field(..., description="Unique session string identifier")
    user_id: str | None = Field(default=None, description="Owner user string identifier")
    title: str = Field(..., description="Human readable session title")
    messages: list[ChatMessage] = Field(
        default_factory=list, description="Ordered conversation history"
    )
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    updated_at: str = Field(..., description="ISO 8601 last update timestamp")


class CreateSessionRequest(BaseModel):
    """Payload model for creating a new agent session."""

    title: str | None = Field(default=None, description="Optional custom session title")
    initial_system_prompt: str | None = Field(
        default=None, description="Optional initial system prompt"
    )


class AddMessageRequest(BaseModel):
    """Payload model for appending a message to a session."""

    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., min_length=1, description="Message content")
    metadata: dict[str, Any] | None = Field(default=None, description="Optional metadata")


class ProjectContext(BaseModel):
    """Workspace project structure context summary."""

    workspace_root: str = Field(..., description="Absolute workspace root path")
    file_count: int = Field(..., ge=0, description="Total files scanned in workspace")
    structure_summary: str = Field(..., description="Formatted workspace file tree")
    key_files: list[str] = Field(
        default_factory=list, description="Detected key configuration & entry point files"
    )
    timestamp: str = Field(..., description="ISO 8601 generation timestamp")
