"""Tool Registry Singleton for dynamic tool discovery and execution routing."""

from app.agent.tools.base import BaseTool
from app.agent.tools.builtins.code_analysis import InspectPythonCodeTool
from app.agent.tools.builtins.data_analysis import DataAnalysisTool
from app.agent.tools.builtins.file_ops import ListDirectoryTool, ReadFileTool, WriteFileTool
from app.agent.tools.builtins.git_tool import GitTool
from app.agent.tools.builtins.rag_search import RAGSearchTool
from app.agent.tools.builtins.terminal import SafeCommandExecutorTool
from app.agent.tools.builtins.web_research import WebResearchTool
from app.core.exceptions import APIException
from app.models.tool import ToolDefinition, ToolExecutionRequest, ToolResult


class ToolRegistry:
    """Central registry discovering and managing agent tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register built-in tool strategies."""
        defaults: list[BaseTool] = [
            ReadFileTool(),
            WriteFileTool(),
            ListDirectoryTool(),
            InspectPythonCodeTool(),
            SafeCommandExecutorTool(),
            WebResearchTool(),
            DataAnalysisTool(),
            GitTool(),
            RAGSearchTool(),
        ]
        for tool in defaults:
            self.register_tool(tool)

    def register_tool(self, tool: BaseTool) -> None:
        """Register a new BaseTool instance."""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        """Retrieve tool by name or raise APIException 404."""
        tool = self._tools.get(name)
        if not tool:
            available = ", ".join(sorted(self._tools.keys()))
            raise APIException(
                message=f"Tool '{name}' not found. Available tools: {available}",
                status_code=404,
            )
        return tool

    def list_tools(self) -> list[ToolDefinition]:
        """Return list of all registered tool definitions."""
        return [tool.get_definition() for tool in self._tools.values()]

    async def execute_tool(self, request: ToolExecutionRequest) -> ToolResult:
        """Find target tool and execute with provided parameter dictionary."""
        tool = self.get_tool(request.tool_name)
        return await tool.run(request.parameters)


# Global singleton instance
tool_registry = ToolRegistry()
