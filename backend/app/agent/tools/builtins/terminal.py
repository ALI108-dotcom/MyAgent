"""Restricted Shell / Terminal Execution Tool."""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from app.agent.tools.base import BaseTool, validate_workspace_path
from app.models.tool import ToolParameterSpec, ToolResult

# Destructive command patterns that are unconditionally blocked
BLOCKED_COMMAND_PATTERNS = [
    "rm -rf", "rmdir /s", "del /f", "format", "mkfs", "dd ",
    "drop database", "shutdown", "reboot", ":(){ :|:& };:"
]


class SafeCommandExecutorTool(BaseTool):
    """Tool for executing non-destructive terminal commands within workspace directory."""

    @property
    def name(self) -> str:
        return "run_command"

    @property
    def description(self) -> str:
        return "Execute shell command within workspace directory with timeout restriction."

    @property
    def parameters(self) -> dict[str, ToolParameterSpec]:
        return {
            "command": ToolParameterSpec(
                type="string",
                description="Command line string to execute (e.g. python -m pytest)",
                required=True,
            ),
            "cwd": ToolParameterSpec(
                type="string",
                description="Relative working directory within workspace (default '.')",
                required=False,
                default=".",
            ),
            "timeout_seconds": ToolParameterSpec(
                type="integer",
                description="Maximum execution timeout in seconds (default 10s)",
                required=False,
                default=10,
            ),
        }

    async def run(self, params: dict[str, Any]) -> ToolResult:
        start_time = time.perf_counter()
        raw_cmd = str(params.get("command", "")).strip()
        raw_cwd = str(params.get("cwd", ".")).strip() or "."
        timeout_sec = int(params.get("timeout_seconds", 10))

        if not raw_cmd:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="Parameter 'command' is required.",
                execution_time_ms=0.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Check command against destructive blacklist
        cmd_lower = raw_cmd.lower()
        for blocked_pattern in BLOCKED_COMMAND_PATTERNS:
            if blocked_pattern in cmd_lower:
                err_msg = f"Security Block: Command contains forbidden pattern '{blocked_pattern}'."
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output="",
                    error=err_msg,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

        try:
            target_cwd = validate_workspace_path(raw_cwd)
        except Exception as err:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=str(err),
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        try:
            process = await asyncio.create_subprocess_shell(
                raw_cmd,
                cwd=str(target_cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    process.communicate(), timeout=float(timeout_sec)
                )
            except asyncio.TimeoutError:
                process.kill()
                elapsed = (time.perf_counter() - start_time) * 1000
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output="",
                    error=f"Execution timed out after {timeout_sec} seconds.",
                    execution_time_ms=elapsed,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

            stdout_text = stdout_data.decode("utf-8", errors="replace").strip()
            stderr_text = stderr_data.decode("utf-8", errors="replace").strip()
            elapsed = (time.perf_counter() - start_time) * 1000

            success = (process.returncode == 0)
            combined_output = stdout_text
            if stderr_text:
                combined_output = f"{stdout_text}\n[Stderr]: {stderr_text}".strip()

            return ToolResult(
                tool_name=self.name,
                success=success,
                output=combined_output or f"(Command exited with code {process.returncode})",
                error=None if success else f"Command failed with exit code {process.returncode}",
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
