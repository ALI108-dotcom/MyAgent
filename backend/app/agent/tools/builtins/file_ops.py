"""Workspace-bounded File Operation Tools."""

import time
from datetime import datetime, timezone
from typing import Any

from app.agent.tools.base import BaseTool, validate_workspace_path
from app.models.tool import ToolParameterSpec, ToolResult


class ReadFileTool(BaseTool):
    """Tool for reading file contents safely within workspace boundary."""

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read text file contents from specified workspace relative path."

    @property
    def parameters(self) -> dict[str, ToolParameterSpec]:
        return {
            "path": ToolParameterSpec(
                type="string",
                description="Relative file path within workspace (e.g. backend/app/main.py)",
                required=True,
            )
        }

    async def run(self, params: dict[str, Any]) -> ToolResult:
        start_time = time.perf_counter()
        raw_path = str(params.get("path", "")).strip()
        if not raw_path:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="Parameter 'path' is required.",
                execution_time_ms=0.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        try:
            target_path = validate_workspace_path(raw_path)
            if not target_path.exists():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output="",
                    error=f"File not found: {raw_path}",
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

            if target_path.is_dir():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output="",
                    error=f"Path '{raw_path}' is a directory, not a file. Use list_directory tool.",
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

            content = target_path.read_text(encoding="utf-8")
            elapsed = (time.perf_counter() - start_time) * 1000
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=content,
                error=None,
                execution_time_ms=elapsed,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=str(e),
                execution_time_ms=elapsed,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )


class WriteFileTool(BaseTool):
    """Tool for creating or modifying files safely within workspace boundary."""

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Write text content to specified file path within workspace."

    @property
    def parameters(self) -> dict[str, ToolParameterSpec]:
        return {
            "path": ToolParameterSpec(
                type="string",
                description="Relative file path within workspace to create or update",
                required=True,
            ),
            "content": ToolParameterSpec(
                type="string",
                description="Text content to write into file",
                required=True,
            ),
        }

    async def run(self, params: dict[str, Any]) -> ToolResult:
        start_time = time.perf_counter()
        raw_path = str(params.get("path", "")).strip()
        content = str(params.get("content", ""))

        if not raw_path:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="Parameter 'path' is required.",
                execution_time_ms=0.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        try:
            target_path = validate_workspace_path(raw_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
            elapsed = (time.perf_counter() - start_time) * 1000

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=f"Successfully wrote {len(content)} characters to '{raw_path}'.",
                error=None,
                execution_time_ms=elapsed,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=str(e),
                execution_time_ms=elapsed,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )


class ListDirectoryTool(BaseTool):
    """Tool for listing files and subdirectories within workspace boundary."""

    @property
    def name(self) -> str:
        return "list_directory"

    @property
    def description(self) -> str:
        return "List files and directories inside specified workspace folder."

    @property
    def parameters(self) -> dict[str, ToolParameterSpec]:
        return {
            "path": ToolParameterSpec(
                type="string",
                description="Relative directory path within workspace (default '.' for root)",
                required=False,
                default=".",
            )
        }

    async def run(self, params: dict[str, Any]) -> ToolResult:
        start_time = time.perf_counter()
        raw_path = str(params.get("path", ".")).strip() or "."

        try:
            target_path = validate_workspace_path(raw_path)
            if not target_path.exists():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output="",
                    error=f"Directory not found: {raw_path}",
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

            if not target_path.is_dir():
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output="",
                    error=f"Path '{raw_path}' is a file, not a directory.",
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

            items = []
            for child in sorted(target_path.iterdir()):
                kind = "DIR " if child.is_dir() else "FILE"
                size = f"({child.stat().st_size} bytes)" if child.is_file() else ""
                items.append(f"{kind}  {child.name} {size}".strip())

            elapsed = (time.perf_counter() - start_time) * 1000
            output_str = "\n".join(items) if items else "(Empty Directory)"

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=output_str,
                error=None,
                execution_time_ms=elapsed,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=str(e),
                execution_time_ms=elapsed,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
