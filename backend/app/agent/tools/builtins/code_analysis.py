"""Python AST Static Code Inspection Tool."""

import ast
import time
from datetime import datetime, timezone
from typing import Any

from app.agent.tools.base import BaseTool, validate_workspace_path
from app.models.tool import ToolParameterSpec, ToolResult


class InspectPythonCodeTool(BaseTool):
    """Tool for statically analyzing Python source files or snippets using AST."""

    @property
    def name(self) -> str:
        return "inspect_code"

    @property
    def description(self) -> str:
        return (
            "Statically inspect Python source code file or snippet using AST "
            "to extract functions, classes, imports, and syntax validity."
        )

    @property
    def parameters(self) -> dict[str, ToolParameterSpec]:
        return {
            "path": ToolParameterSpec(
                type="string",
                description="Relative path to Python file within workspace",
                required=False,
            ),
            "code": ToolParameterSpec(
                type="string",
                description="Python code string to analyze (optional if path provided)",
                required=False,
            ),
        }

    async def run(self, params: dict[str, Any]) -> ToolResult:
        start_time = time.perf_counter()
        path = str(params.get("path", "")).strip()
        code = str(params.get("code", ""))

        if not path and not code:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error="Must provide either 'path' or 'code' parameter.",
                execution_time_ms=0.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        source_code = code
        filename_label = "<snippet>"

        if path:
            try:
                target_path = validate_workspace_path(path)
                if not target_path.exists():
                    return ToolResult(
                        tool_name=self.name,
                        success=False,
                        output="",
                        error=f"File not found: {path}",
                        execution_time_ms=(time.perf_counter() - start_time) * 1000,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                source_code = target_path.read_text(encoding="utf-8")
                filename_label = path
            except Exception as e:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output="",
                    error=str(e),
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

        try:
            tree = ast.parse(source_code, filename=filename_label)
        except SyntaxError as syn_err:
            elapsed = (time.perf_counter() - start_time) * 1000
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"SyntaxError in {filename_label} (line {syn_err.lineno}): {syn_err.msg}",
                execution_time_ms=elapsed,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        classes = []
        functions = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or "No docstring"
                classes.append(f"- Class '{node.name}' (line {node.lineno}): {doc}")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                kind = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                args = [arg.arg for arg in node.args.args]
                functions.append(f"- {kind} {node.name}({', '.join(args)}) (line {node.lineno})")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"- import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = ", ".join(alias.name for alias in node.names)
                imports.append(f"- from {module} import {names}")

        output_lines = [
            f"=== Python AST Analysis for [{filename_label}] ===",
            "Syntax Status: VALID",
            f"Total Lines of Code: {len(source_code.splitlines())}",
            "",
            "--- Classes ---",
            "\n".join(classes) if classes else "None",
            "",
            "--- Functions & Methods ---",
            "\n".join(functions) if functions else "None",
            "",
            "--- Imports ---",
            "\n".join(imports) if imports else "None",
        ]

        elapsed = (time.perf_counter() - start_time) * 1000
        return ToolResult(
            tool_name=self.name,
            success=True,
            output="\n".join(output_lines),
            error=None,
            execution_time_ms=elapsed,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
