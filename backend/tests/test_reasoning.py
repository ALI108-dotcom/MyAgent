"""Unit and integration tests for ReAct Cognitive Engine Subsystem."""

import pytest
from httpx import AsyncClient

from app.agent.reasoning.engine import cognitive_engine
from app.models.reasoning import ReasoningRequest, ReasoningResponse


@pytest.mark.asyncio
async def test_cognitive_engine_solve_goal() -> None:
    """Verify CognitiveEngine executes ReAct loop and decomposes software engineering goals."""
    request = ReasoningRequest(
        goal="Inspect workspace directory structure and inspect backend/app/main.py architecture",
        provider="mock",
        max_iterations=5,
    )
    response = await cognitive_engine.solve_goal(request)

    assert isinstance(response, ReasoningResponse)
    assert response.goal == request.goal
    assert len(response.trajectory) >= 2
    assert response.total_iterations >= 2
    assert len(response.final_answer) > 0

    # Verify Trajectory Steps
    first_step = response.trajectory[0]
    assert first_step.step_number == 1
    assert first_step.tool_name == "list_directory"
    assert first_step.status == "completed"
    assert first_step.observation is not None


@pytest.mark.asyncio
async def test_reasoning_solve_endpoint(auth_client: AsyncClient) -> None:
    """Verify POST /api/v1/agent/reasoning/solve REST endpoint."""
    payload = {
        "goal": "Verify backend test suite execution",
        "provider": "mock",
    }
    response = await auth_client.post("/api/v1/agent/reasoning/solve", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["goal"] == payload["goal"]
    assert len(data["trajectory"]) >= 1
    assert "final_answer" in data
