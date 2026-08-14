"""Tools Subsystem API Endpoints."""

from fastapi import APIRouter, Depends, status

from app.agent.tools.registry import tool_registry
from app.core.security import get_current_user
from app.models.auth import UserRead
from app.models.tool import ToolDefinition, ToolExecutionRequest, ToolResult

router = APIRouter()


@router.get(
    "/",
    response_model=list[ToolDefinition],
    status_code=status.HTTP_200_OK,
    summary="List all available agent tools",
    description="Returns metadata definitions for registered built-in tools.",
)
async def list_available_tools(
    current_user: UserRead = Depends(get_current_user),
) -> list[ToolDefinition]:
    """List available tools."""
    return tool_registry.list_tools()


@router.post(
    "/execute",
    response_model=ToolResult,
    status_code=status.HTTP_200_OK,
    summary="Execute a registered agent tool",
    description="Runs target tool with parameters after enforcing workspace safety boundaries.",
)
async def execute_tool(
    request: ToolExecutionRequest,
    current_user: UserRead = Depends(get_current_user),
) -> ToolResult:
    """Execute tool."""
    tool = tool_registry.get_tool(request.tool_name)
    return await tool.run(request.parameters)
