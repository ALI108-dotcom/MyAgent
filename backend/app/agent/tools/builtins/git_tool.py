"""Git & Repository Inspection Tool."""

import subprocess
import time
from datetime import datetime, timezone
from typing import Any

from app.agent.tools.base import BaseTool
from app.models.tool import ToolParameterSpec, ToolResult


class GitTool(BaseTool):
    """Tool for inspecting git status, branch metadata, and commit history."""

    @property
    def name(self) -> str:
        return "git_tool"

    @property
    def description(self) -> str:
        return "Inspect git status, list active branches, view commit logs, or inspect diffs."

    @property
    def parameters(self) -> dict[str, ToolParameterSpec]:
        return {
            "operation": ToolParameterSpec(
                type="string",
                description="Git operation to perform: status, branch, log, or diff.",
                required=True,
            )
        }

    async def run(self, params: dict[str, Any]) -> ToolResult:
        t0 = time.perf_counter()
        op = str(params.get("operation", "status")).strip().lower()
        now_iso = datetime.now(timezone.utc).isoformat()

        allowed_ops = {
            "status": ["git", "status"],
            "branch": ["git", "branch"],
            "log": ["git", "log", "-n", "5"],
            "diff": ["git", "diff"],
        }
        cmd = allowed_ops.get(op, ["git", "status"])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            elapsed = (time.perf_counter() - t0) * 1000
            if res.returncode == 0:
                output = res.stdout.strip() or "No output returned from git command."
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=output,
                    execution_time_ms=elapsed,
                    timestamp=now_iso,
                )
            else:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output="",
                    error=res.stderr.strip(),
                    execution_time_ms=elapsed,
                    timestamp=now_iso,
                )
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"Git command failed: {str(e)}",
                execution_time_ms=elapsed,
                timestamp=now_iso,
            )
