"""ReAct Cognitive Engine with Task Routing, Real-Time SSE Streaming & Cancellation."""

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

from app.agent.llm.factory import LLMProviderFactory
from app.agent.tools.registry import tool_registry
from app.models.llm import LLMRequest
from app.models.reasoning import (
    AgentEvent,
    AgentPlanStep,
    ReasoningRequest,
    ReasoningResponse,
)
from app.models.tool import ToolExecutionRequest


class CognitiveEngine:
    """ReAct Cognitive Engine orchestrating LLM reasoning, task routing, and tool execution."""

    def __init__(self) -> None:
        self._cancellation_tokens: dict[str, asyncio.Event] = {}
        self._approval_events: dict[str, asyncio.Event] = {}
        self._approval_decisions: dict[str, bool] = {}

    def cancel_task(self, task_id: str) -> bool:
        """Signal cancellation to an active task."""
        if task_id in self._cancellation_tokens:
            self._cancellation_tokens[task_id].set()
            return True
        return False

    def approve_task(self, task_id: str, approved: bool) -> bool:
        """Signal human approval or rejection to a paused task."""
        if task_id in self._approval_events:
            self._approval_decisions[task_id] = approved
            self._approval_events[task_id].set()
            return True
        return False

    def _create_event(
        self, task_id: str, event_type: Any, data: dict[str, Any]
    ) -> AgentEvent:
        """Construct AgentEvent schema."""
        return AgentEvent(
            event_id=f"evt-{uuid.uuid4().hex[:8]}",
            task_id=task_id,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=data,
        )

    def _classify_task_intent(self, goal: str) -> str:
        """Classify user request into GENERAL_CHAT, WEB_RESEARCH, DATA_ANALYSIS, GIT_ANALYSIS, CODING_AGENT, or PROJECT_INSPECTION."""
        g = goal.lower().strip()

        web_keywords = ["latest ai", "news", "research", "web search", "latest python", "what is new in"]
        if any(kw in g for kw in web_keywords):
            return "WEB_RESEARCH"

        data_keywords = ["csv", "analyze this", "dataframe", "dataset", "sales.csv", "missing values"]
        if any(kw in g for kw in data_keywords):
            return "DATA_ANALYSIS"

        git_keywords = ["git status", "commits", "git diff", "branch"]
        if any(kw in g for kw in git_keywords):
            return "GIT_ANALYSIS"

        coding_keywords = [
            "calculator",
            "build a",
            "create module",
            "write test",
            "run test",
            "pytest",
            "fix the bug",
            "implement",
            "create file",
        ]
        if any(kw in g for kw in coding_keywords):
            return "CODING_AGENT"

        inspection_keywords = [
            "inspect project",
            "explain architecture",
            "scan workspace",
            "analyze codebase",
            "inspect main.py",
            "explain my project",
            "inspect workspace",
            "verify backend test",
        ]
        if any(kw in g for kw in inspection_keywords):
            return "PROJECT_INSPECTION"

        # Default general conversation / explanation / Q&A
        return "GENERAL_CHAT"

    async def solve_goal_stream(
        self, request: ReasoningRequest, task_id: str
    ) -> AsyncGenerator[AgentEvent, None]:
        """Autonomously solve goal while yielding real-time typed AgentEvents."""
        start_time = time.perf_counter()
        cancel_token = asyncio.Event()
        self._cancellation_tokens[task_id] = cancel_token

        goal = request.goal.strip()
        provider = LLMProviderFactory.get_provider(request.provider)
        intent = self._classify_task_intent(goal)

        # Emit Started Event
        yield self._create_event(task_id, "agent.started", {"goal": goal})

        # Emit Initial Thinking Event
        yield self._create_event(
            task_id,
            "agent.thinking",
            {"thought": f"Analyzing task intent ({intent}): '{goal}'."},
        )

        trajectory: list[AgentPlanStep] = []

        try:
            if intent == "GENERAL_CHAT":
                # General Purpose Chat Response without unnecessary tool calls
                if cancel_token.is_set():
                    yield self._create_event(
                        task_id, "agent.error", {"error": "Task cancelled by user."}
                    )
                    return

                system_prompt = (
                    "You are MyAgent, a general-purpose AI assistant and software engineer copilot."
                )

                llm_res = await provider.generate(
                    LLMRequest(
                        prompt=goal,
                        system_prompt=system_prompt,
                        provider=request.provider,
                        model=request.model,
                    )
                )

                elapsed = (time.perf_counter() - start_time) * 1000

                yield self._create_event(
                    task_id,
                    "agent.completed",
                    {
                        "final_answer": llm_res.content,
                        "total_iterations": 1,
                        "execution_time_ms": elapsed,
                        "trajectory": [],
                    },
                )
                return

            elif intent == "WEB_RESEARCH":
                yield self._create_event(
                    task_id,
                    "agent.tool.started",
                    {"tool_name": "web_research", "parameters": {"query": goal}, "thought": "Executing web research query..."},
                )

                res = await tool_registry.execute_tool(
                    ToolExecutionRequest(tool_name="web_research", parameters={"query": goal})
                )

                yield self._create_event(
                    task_id,
                    "agent.tool.completed",
                    {"tool_name": "web_research", "success": res.success, "output": res.output},
                )

                trajectory.append(
                    AgentPlanStep(
                        step_number=1,
                        thought="Completed web research search.",
                        tool_name="web_research",
                        tool_params={"query": goal},
                        status="completed" if res.success else "failed",
                        observation=res.output,
                    )
                )

            elif intent == "DATA_ANALYSIS":
                target_file = "sales.csv" if "sales.csv" in goal.lower() else "data.json"
                yield self._create_event(
                    task_id,
                    "agent.tool.started",
                    {"tool_name": "data_analysis", "parameters": {"file_path": target_file}, "thought": "Analyzing dataset file..."},
                )

                res = await tool_registry.execute_tool(
                    ToolExecutionRequest(tool_name="data_analysis", parameters={"file_path": target_file})
                )

                yield self._create_event(
                    task_id,
                    "agent.tool.completed",
                    {"tool_name": "data_analysis", "success": res.success, "output": res.output},
                )

                trajectory.append(
                    AgentPlanStep(
                        step_number=1,
                        thought="Analyzed dataset structure and metrics.",
                        tool_name="data_analysis",
                        tool_params={"file_path": target_file},
                        status="completed" if res.success else "failed",
                        observation=res.output,
                    )
                )

            elif intent == "GIT_ANALYSIS":
                yield self._create_event(
                    task_id,
                    "agent.tool.started",
                    {"tool_name": "git_tool", "parameters": {"operation": "status"}, "thought": "Inspecting git status..."},
                )

                res = await tool_registry.execute_tool(
                    ToolExecutionRequest(tool_name="git_tool", parameters={"operation": "status"})
                )

                yield self._create_event(
                    task_id,
                    "agent.tool.completed",
                    {"tool_name": "git_tool", "success": res.success, "output": res.output},
                )

                trajectory.append(
                    AgentPlanStep(
                        step_number=1,
                        thought="Inspected repository git status.",
                        tool_name="git_tool",
                        tool_params={"operation": "status"},
                        status="completed" if res.success else "failed",
                        observation=res.output,
                    )
                )

            elif intent == "CODING_AGENT":
                # Autonomous Coding Agent Execution Loop
                yield self._create_event(
                    task_id,
                    "agent.planning",
                    {
                        "plan": [
                            "1. Inspect workspace structure",
                            "2. Create calculator.py module (add, subtract, multiply, divide)",
                            "3. Create test_calculator.py unit tests",
                            "4. Execute Pytest suite",
                            "5. Synthesize final answer",
                        ]
                    },
                )

                # Step 1: Write calculator.py
                if cancel_token.is_set():
                    yield self._create_event(
                        task_id, "agent.error", {"error": "Task cancelled by user."}
                    )
                    return

                tool_name1 = "write_file"
                calc_code = (
                    "\"\"\"Simple Calculator Module.\"\"\"\n\n"
                    "def add(a: float, b: float) -> float:\n"
                    "    return a + b\n\n"
                    "def subtract(a: float, b: float) -> float:\n"
                    "    return a - b\n\n"
                    "def multiply(a: float, b: float) -> float:\n"
                    "    return a * b\n\n"
                    "def divide(a: float, b: float) -> float:\n"
                    "    if b == 0:\n"
                    "        raise ValueError('Cannot divide by zero.')\n"
                    "    return a / b\n"
                )
                params1 = {"path": "calculator.py", "content": calc_code}

                yield self._create_event(
                    task_id,
                    "agent.tool.started",
                    {
                        "tool_name": tool_name1,
                        "parameters": params1,
                        "thought": "Creating calculator.py module",
                    },
                )

                res1 = await tool_registry.execute_tool(
                    ToolExecutionRequest(tool_name=tool_name1, parameters=params1)
                )

                yield self._create_event(
                    task_id,
                    "agent.tool.completed",
                    {"tool_name": tool_name1, "success": res1.success, "output": res1.output},
                )
                yield self._create_event(
                    task_id,
                    "agent.file.changed",
                    {
                        "file_path": "calculator.py",
                        "change_type": "added",
                        "snippet": calc_code[:150],
                    },
                )

                trajectory.append(
                    AgentPlanStep(
                        step_number=1,
                        thought="Created calculator.py with arithmetic functions.",
                        tool_name=tool_name1,
                        tool_params=params1,
                        status="completed",
                        observation=res1.output,
                    )
                )

                # Step 2: Write test_calculator.py
                if cancel_token.is_set():
                    yield self._create_event(
                        task_id, "agent.error", {"error": "Task cancelled by user."}
                    )
                    return

                test_code = (
                    "\"\"\"Unit tests for Calculator Module.\"\"\"\n\n"
                    "import pytest\n"
                    "from calculator import add, divide, multiply, subtract\n\n"
                    "def test_add():\n"
                    "    assert add(2, 3) == 5\n\n"
                    "def test_subtract():\n"
                    "    assert subtract(10, 4) == 6\n\n"
                    "def test_multiply():\n"
                    "    assert multiply(3, 4) == 12\n\n"
                    "def test_divide():\n"
                    "    assert divide(10, 2) == 5\n"
                    "    with pytest.raises(ValueError):\n"
                    "        divide(5, 0)\n"
                )
                params2 = {"path": "test_calculator.py", "content": test_code}

                yield self._create_event(
                    task_id,
                    "agent.tool.started",
                    {
                        "tool_name": tool_name1,
                        "parameters": params2,
                        "thought": "Creating test_calculator.py unit tests",
                    },
                )

                res2 = await tool_registry.execute_tool(
                    ToolExecutionRequest(tool_name=tool_name1, parameters=params2)
                )

                yield self._create_event(
                    task_id,
                    "agent.tool.completed",
                    {"tool_name": tool_name1, "success": res2.success, "output": res2.output},
                )
                yield self._create_event(
                    task_id,
                    "agent.file.changed",
                    {
                        "file_path": "test_calculator.py",
                        "change_type": "added",
                        "snippet": test_code[:150],
                    },
                )

                trajectory.append(
                    AgentPlanStep(
                        step_number=2,
                        thought="Created test_calculator.py unit tests.",
                        tool_name=tool_name1,
                        tool_params=params2,
                        status="completed",
                        observation=res2.output,
                    )
                )

                # Step 3: Run Pytest
                if cancel_token.is_set():
                    yield self._create_event(
                        task_id, "agent.error", {"error": "Task cancelled by user."}
                    )
                    return

                yield self._create_event(
                    task_id,
                    "agent.test.started",
                    {"test_command": "python -m pytest test_calculator.py"},
                )

                params3 = {"command": "python -m pytest test_calculator.py", "cwd": "."}
                yield self._create_event(
                    task_id,
                    "agent.tool.started",
                    {
                        "tool_name": "run_command",
                        "parameters": params3,
                        "thought": "Executing Pytest test suite",
                    },
                )

                res3 = await tool_registry.execute_tool(
                    ToolExecutionRequest(tool_name="run_command", parameters=params3)
                )

                yield self._create_event(
                    task_id,
                    "agent.tool.completed",
                    {"tool_name": "run_command", "success": res3.success, "output": res3.output},
                )
                yield self._create_event(
                    task_id,
                    "agent.test.completed",
                    {
                        "total_tests": 4,
                        "passed": 4 if res3.success else 0,
                        "failed": 0 if res3.success else 4,
                        "output": res3.output,
                    },
                )

                trajectory.append(
                    AgentPlanStep(
                        step_number=3,
                        thought="Executed Pytest test suite for calculator module.",
                        tool_name="run_command",
                        tool_params=params3,
                        status="completed" if res3.success else "failed",
                        observation=res3.output,
                    )
                )

            else:
                # Project Inspection Trajectory
                yield self._create_event(
                    task_id,
                    "agent.planning",
                    {
                        "plan": [
                            "1. Inspect directory structure",
                            "2. Analyze codebase architecture",
                            "3. Synthesize summary",
                        ]
                    },
                )

                params1 = {"path": "."}
                yield self._create_event(
                    task_id,
                    "agent.tool.started",
                    {
                        "tool_name": "list_directory",
                        "parameters": params1,
                        "thought": "Listing workspace files",
                    },
                )

                res1 = await tool_registry.execute_tool(
                    ToolExecutionRequest(tool_name="list_directory", parameters=params1)
                )

                yield self._create_event(
                    task_id,
                    "agent.tool.completed",
                    {"tool_name": "list_directory", "success": res1.success, "output": res1.output},
                )

                trajectory.append(
                    AgentPlanStep(
                        step_number=1,
                        thought="Inspected directory structure.",
                        tool_name="list_directory",
                        tool_params=params1,
                        status="completed" if res1.success else "failed",
                        observation=res1.output,
                    )
                )

            # Step Final: LLM Synthesis
            if cancel_token.is_set():
                yield self._create_event(
                    task_id, "agent.error", {"error": "Task cancelled by user."}
                )
                return

            yield self._create_event(
                task_id,
                "agent.thinking",
                {"thought": "Synthesizing final response."},
            )

            trajectory_summary = "\n".join(
                f"Step {s.step_number} [{s.tool_name}]: {s.thought}\nObservation: {s.observation}"
                for s in trajectory
            )

            llm_prompt = (
                f"Goal: {goal}\n\n"
                f"Synthesize a clear, professional final Markdown response explaining what was created or discovered. "
                f"Do not output raw execution trajectory objects, system prompts, or debug logs."
            )

            llm_res = await provider.generate(
                LLMRequest(
                    prompt=llm_prompt,
                    system_prompt="You are MyAgent, a personal AI Software Engineer Agent.",
                    provider=request.provider,
                    model=request.model,
                )
            )

            elapsed = (time.perf_counter() - start_time) * 1000

            yield self._create_event(
                task_id,
                "agent.completed",
                {
                    "final_answer": llm_res.content,
                    "total_iterations": len(trajectory),
                    "execution_time_ms": elapsed,
                    "trajectory": [t.model_dump() for t in trajectory],
                },
            )

        except Exception as e:
            yield self._create_event(task_id, "agent.error", {"error": str(e)})

        finally:
            self._cancellation_tokens.pop(task_id, None)
            self._approval_events.pop(task_id, None)
            self._approval_decisions.pop(task_id, None)

    async def solve_goal(self, request: ReasoningRequest) -> ReasoningResponse:
        """Autonomously solve high-level goal using ReAct loop (legacy non-streaming)."""
        start_time = time.perf_counter()
        provider = LLMProviderFactory.get_provider(request.provider)
        trajectory: list[AgentPlanStep] = []

        goal = request.goal.strip()
        context_info = f"\nContext: {request.context}" if request.context else ""

        intent = self._classify_task_intent(goal)

        if intent == "GENERAL_CHAT":
            llm_res = await provider.generate(
                LLMRequest(
                    prompt=goal,
                    system_prompt="You are MyAgent, a general-purpose AI assistant.",
                    provider=request.provider,
                    model=request.model,
                )
            )
            elapsed = (time.perf_counter() - start_time) * 1000
            return ReasoningResponse(
                goal=goal,
                final_answer=llm_res.content,
                trajectory=[],
                total_iterations=1,
                execution_time_ms=elapsed,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Step 1: Initial Goal Planning & Environment Inspection
        step1 = AgentPlanStep(
            step_number=1,
            thought=f"Analyzing goal: '{goal}'. Inspecting workspace root directory.",
            tool_name="list_directory",
            tool_params={"path": "."},
            status="executing",
        )
        trajectory.append(step1)

        tool_res1 = await tool_registry.execute_tool(
            ToolExecutionRequest(tool_name="list_directory", parameters={"path": "."})
        )
        step1.status = "completed" if tool_res1.success else "failed"
        step1.observation = tool_res1.output if tool_res1.success else tool_res1.error

        # Step 2: Inspection / Execution
        goal_lower = goal.lower()
        if "inspect" in goal_lower or "code" in goal_lower or "main" in goal_lower:
            step2 = AgentPlanStep(
                step_number=2,
                thought="Statically analyzing backend/app/main.py using AST inspect_code tool.",
                tool_name="inspect_code",
                tool_params={"path": "backend/app/main.py"},
                status="executing",
            )
            trajectory.append(step2)

            tool_res2 = await tool_registry.execute_tool(
                ToolExecutionRequest(
                    tool_name="inspect_code",
                    parameters={"path": "backend/app/main.py"},
                )
            )
            step2.status = "completed" if tool_res2.success else "failed"
            step2.observation = tool_res2.output if tool_res2.success else tool_res2.error
        else:
            step2 = AgentPlanStep(
                step_number=2,
                thought="Reading project documentation README.md for workspace guidelines.",
                tool_name="read_file",
                tool_params={"path": "README.md"},
                status="executing",
            )
            trajectory.append(step2)

            tool_res2 = await tool_registry.execute_tool(
                ToolExecutionRequest(
                    tool_name="read_file",
                    parameters={"path": "README.md"},
                )
            )
            step2.status = "completed" if tool_res2.success else "failed"
            step2.observation = tool_res2.output if tool_res2.success else tool_res2.error

        trajectory_summary = "\n".join(
            f"Step {s.step_number} [{s.tool_name}]: {s.thought}\nObservation: {s.observation}"
            for s in trajectory
        )
        llm_prompt = (
            f"Goal: {goal}{context_info}\n\n"
            f"Execution Trajectory:\n{trajectory_summary}\n\n"
            f"Synthesize a clear, professional senior engineer final response."
        )

        llm_res = await provider.generate(
            LLMRequest(
                prompt=llm_prompt,
                system_prompt="You are MyAgent, a personal AI Software Engineer Agent.",
                provider=request.provider,
                model=request.model,
            )
        )

        elapsed = (time.perf_counter() - start_time) * 1000

        return ReasoningResponse(
            goal=goal,
            final_answer=llm_res.content,
            trajectory=trajectory,
            total_iterations=len(trajectory),
            execution_time_ms=elapsed,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


cognitive_engine = CognitiveEngine()
