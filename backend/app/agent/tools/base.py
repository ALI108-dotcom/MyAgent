"""Base class and security utilities for agent tools."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.core.exceptions import APIException
from app.models.tool import ToolDefinition, ToolParameterSpec, ToolResult


def validate_workspace_path(input_path: str | Path) -> Path:
    """Validate that target path stays strictly inside workspace boundaries."""
    workspace_root = Path(__file__).resolve().parents[3]
    raw_path = Path(input_path)
    if not raw_path.is_absolute():
        target_path = (workspace_root / raw_path).resolve()
    else:
        target_path = raw_path.resolve()

    try:
        target_path.relative_to(workspace_root)
    except ValueError as err:
        err_msg = f"Access denied: Path '{input_path}' is outside workspace root."
        raise APIException(message=err_msg, status_code=403) from err

    return target_path


class BaseTool(ABC):
    """Abstract Base Class for all agent tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return unique tool name identifier."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Return human-readable tool capability description."""

    @property
    @abstractmethod
    def parameters(self) -> dict[str, ToolParameterSpec]:
        """Return parameter specifications dict."""

    def get_definition(self) -> ToolDefinition:
        """Return ToolDefinition Pydantic model for schema discovery."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )

    @abstractmethod
    async def run(self, params: dict[str, Any]) -> ToolResult:
        """Asynchronously execute tool with provided parameters."""
