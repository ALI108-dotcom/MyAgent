"""RAG Search Tool for querying workspace knowledge base & indexed documents."""

import time
from datetime import datetime, timezone
from typing import Any

from app.agent.rag.indexer import CodebaseIndexer
from app.agent.rag.vector_store import vector_store
from app.agent.tools.base import BaseTool
from app.models.tool import ToolParameterSpec, ToolResult


class RAGSearchTool(BaseTool):
    """Tool for querying indexed workspace codebase and documents."""

    @property
    def name(self) -> str:
        return "search_knowledge_base"

    @property
    def description(self) -> str:
        return "Query indexed codebase and documents for relevant code snippets or evidence."

    @property
    def parameters(self) -> dict[str, ToolParameterSpec]:
        return {
            "query": ToolParameterSpec(
                type="string",
                description="The search query or keyword phrase to search in knowledge base.",
                required=True,
            ),
            "top_k": ToolParameterSpec(
                type="integer",
                description="Number of matching snippets to return (default 5).",
                required=False,
                default=5,
            ),
        }

    async def run(self, params: dict[str, Any]) -> ToolResult:
        t0 = time.perf_counter()
        query = str(params.get("query", "")).strip()
        top_k = int(params.get("top_k", 5))
        now_iso = datetime.now(timezone.utc).isoformat()

        if not query:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="Query parameter is required for knowledge base search.",
                execution_time_ms=(time.perf_counter() - t0) * 1000,
                timestamp=now_iso,
            )

        if vector_store.total_chunks() == 0:
            CodebaseIndexer.index_workspace()

        results = vector_store.search_similar(query=query, top_k=top_k)
        if not results:
            return ToolResult(
                tool_name=self.name,
                success=True,
                output="No relevant indexed knowledge chunks found matching query threshold.",
                execution_time_ms=(time.perf_counter() - t0) * 1000,
                timestamp=now_iso,
            )

        output_lines = [f"Found {len(results)} relevant indexed knowledge sources:\n"]
        for idx, res in enumerate(results, 1):
            output_lines.append(
                f"{idx}. {res.citation} (Score: {res.score:.2f})\n"
                f"```\n{res.chunk.content[:300]}\n```\n"
            )

        return ToolResult(
            tool_name=self.name,
            success=True,
            output="\n".join(output_lines),
            execution_time_ms=(time.perf_counter() - t0) * 1000,
            timestamp=now_iso,
        )
