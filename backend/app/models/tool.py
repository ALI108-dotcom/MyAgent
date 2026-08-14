"""Pydantic schemas for Tool Definitions, Execution Requests, and Tool Results."""

from typing import Any

from pydantic import BaseModel, Field


class ToolParameterSpec(BaseModel):
    """Parameter specification for an agent tool."""

    type: str = Field(..., description="Data type (string, integer, boolean, object)")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=True, description="Whether parameter is mandatory")
    default: Any | None = Field(default=None, description="Default value if optional")


class ToolDefinition(BaseModel):
    """Tool schema metadata exposed to clients and LLMs."""

    name: str = Field(..., description="Unique tool identifier name")
    description: str = Field(..., description="Human-readable capability description")
    parameters: dict[str, ToolParameterSpec] = Field(
        ..., description="Map of parameter names to specs"
    )


class ToolExecutionRequest(BaseModel):
    """Payload model for invoking a tool via API."""

    tool_name: str = Field(..., min_length=1, description="Target tool name to execute")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Parameters dictionary to pass to tool"
    )


class ToolResult(BaseModel):
    """Standardized result returned by tool execution."""

    tool_name: str = Field(..., description="Name of executed tool")
    success: bool = Field(..., description="Whether execution succeeded without errors")
    output: str = Field(..., description="Tool output or return payload string")
    error: str | None = Field(default=None, description="Error message if execution failed")
    execution_time_ms: float = Field(..., description="Execution duration in milliseconds")
    timestamp: str = Field(..., description="ISO 8601 server completion timestamp")
