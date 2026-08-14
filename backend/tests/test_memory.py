"""Unit and integration tests for Memory and Project Context Subsystem."""

import pytest
from httpx import AsyncClient

from app.agent.memory.context_builder import ProjectContextBuilder
from app.agent.memory.session_manager import session_manager
from app.models.memory import ChatMessage, ProjectContext, SessionMemory


@pytest.mark.asyncio
async def test_session_memory_manager_lifecycle() -> None:
    """Verify SessionMemoryManager session creation, message addition, retrieval, and deletion."""
    # 1. Create session
    session: SessionMemory = await session_manager.create_session(
        title="Test Development Session",
        initial_system_prompt="You are a helpful test agent.",
    )
    assert session.session_id.startswith("session-")
    assert session.title == "Test Development Session"
    assert len(session.messages) == 1
    assert session.messages[0].role == "system"

    # 2. Add message
    msg = ChatMessage(
        role="user",
        content="How do I configure MongoDB in FastAPI?",
        timestamp="2026-08-14T20:00:00Z",
    )
    updated_session = await session_manager.add_message(session.session_id, msg)
    assert len(updated_session.messages) == 2
    assert updated_session.messages[1].content == "How do I configure MongoDB in FastAPI?"

    # 3. Retrieve session
    retrieved = await session_manager.get_session(session.session_id)
    assert retrieved.session_id == session.session_id
    assert len(retrieved.messages) == 2

    # 4. Delete session
    deleted = await session_manager.delete_session(session.session_id)
    assert deleted is True


def test_project_context_builder() -> None:
    """Verify ProjectContextBuilder generates workspace structure summary and lists key files."""
    context: ProjectContext = ProjectContextBuilder.build_context()
    assert context.file_count > 0
    assert "AgentAI" in context.workspace_root or "backend" in context.structure_summary
    assert len(context.key_files) > 0


@pytest.mark.asyncio
async def test_memory_api_endpoints(auth_client: AsyncClient) -> None:
    """Verify Memory REST API endpoints (sessions CRUD and project context)."""
    # Create session API
    create_resp = await auth_client.post(
        "/api/v1/agent/memory/sessions",
        json={"title": "API Test Session"},
    )
    assert create_resp.status_code == 201
    session_data = create_resp.json()
    session_id = session_data["session_id"]
    assert session_data["title"] == "API Test Session"

    # List sessions API
    list_resp = await auth_client.get("/api/v1/agent/memory/sessions")
    assert list_resp.status_code == 200
    sessions_list = list_resp.json()
    assert any(s["session_id"] == session_id for s in sessions_list)

    # Get project context API
    context_resp = await auth_client.get("/api/v1/agent/memory/context")
    assert context_resp.status_code == 200
    context_data = context_resp.json()
    assert "workspace_root" in context_data
    assert context_data["file_count"] > 0
