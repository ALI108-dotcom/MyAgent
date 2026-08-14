"""Mock LLM Provider for 100% offline development and deterministic unit testing."""

from datetime import datetime, timezone

from app.agent.llm.base import BaseLLMProvider
from app.models.llm import LLMRequest, LLMResponse, TokenUsage


class MockLLMProvider(BaseLLMProvider):
    """Deterministic Mock LLM provider returning clean ChatGPT-style Markdown responses."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        model_name = request.model or "mock-agent-v1"
        prompt_lower = request.prompt.lower()

        if "calculator" in prompt_lower or "module" in prompt_lower:
            content = (
                "Done! I created the calculator module and verified it with the test suite.\n\n"
                "### Created Files\n"
                "- `calculator.py`\n"
                "- `test_calculator.py`\n\n"
                "### Functions Implemented\n"
                "- `add(a, b)`: Returns sum of a and b\n"
                "- `subtract(a, b)`: Returns difference of a and b\n"
                "- `multiply(a, b)`: Returns product of a and b\n"
                "- `divide(a, b)`: Returns quotient with divide-by-zero validation\n\n"
                "### Test Verification\n"
                "✓ Executed Pytest test suite\n"
                "✓ 4 tests passed successfully"
            )
        elif "bayes" in prompt_lower:
            content = (
                "### Bayes' Theorem Overview\n\n"
                "Bayes' Theorem describes the probability of an event based on prior knowledge of conditions related to the event:\n\n"
                "$$\\text{P}(A|B) = \\frac{\\text{P}(B|A) \\cdot \\text{P}(A)}{\\text{P}(B)}$$\n\n"
                "- **P(A|B)**: Posterior probability of event A given evidence B.\n"
                "- **P(B|A)**: Likelihood of evidence B given event A.\n"
                "- **P(A)**: Prior probability of event A.\n"
                "- **P(B)**: Marginal likelihood of evidence B."
            )
        elif "project" in prompt_lower or "architecture" in prompt_lower:
            content = (
                "### Project Architecture Overview\n\n"
                "The workspace is structured into a production FastAPI backend and a Next.js 15 frontend:\n\n"
                "- **Backend (`/backend`)**: Built with FastAPI, Pydantic, MongoDB, JWT security, and a ReAct cognitive agent engine.\n"
                "- **Frontend (`/frontend`)**: Built with Next.js 15, Tailwind CSS, TypeScript, and real-time SSE stream integration.\n"
                "- **Agent Core**: Modular tool registry supporting file operations, AST inspection, shell execution, web research, data analysis, and git tools."
            )
        else:
            content = (
                "Hello! I'm MyAgent, your personal AI assistant and software engineering copilot.\n\n"
                "I'm ready to help you with general questions, software development, building modules, debugging code, data analysis, or inspecting your workspace."
            )

        prompt_tokens = len(request.prompt.split()) + (
            len(request.system_prompt.split()) if request.system_prompt else 0
        )
        completion_tokens = len(content.split())
        total_tokens = prompt_tokens + completion_tokens

        return LLMResponse(
            content=content,
            provider=self.provider_name,
            model=model_name,
            finish_reason="stop",
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
