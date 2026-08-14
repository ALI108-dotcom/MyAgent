"""Unit tests for safe tool execution subsystem."""

import pytest
from httpx import AsyncClient

from app.agent.tools.base import validate_workspace_path
from app.agent.tools.builtins.code_analysis import InspectPythonCodeTool
from app.agent.tools.builtins.file_ops import ReadFileTool, WriteFileTool
from app.agent.tools.builtins.terminal import SafeCommandExecutorTool
from app.core.exceptions import APIException


def test_path_traversal_prevention() -> None:
    """Verify validate_workspace_path blocks path traversal attempts outside workspace root."""
    # Valid relative path inside workspace
    valid_path = validate_workspace_path("app/main.py")
    assert valid_path.is_file() or "main.py" in str(valid_path)

    # Traversal attempt outside workspace
    with pytest.raises(APIException) as exc_info:
        validate_workspace_path("../../../../../Windows/System32/cmd.exe")

    assert exc_info.value.status_code == 403
    assert "Access denied" in exc_info.value.message


@pytest.mark.asyncio
async def test_file_ops_tools() -> None:
    """Verify WriteFileTool and ReadFileTool execute safely within workspace boundary."""
    write_tool = WriteFileTool()
    read_tool = ReadFileTool()

    target_file = "tests/test_scratch.txt"
    test_content = "Hello from Safe Tool Subsystem!"

    # 1. Write file
    write_result = await write_tool.run({"path": target_file, "content": test_content})
    assert write_result.success is True
    assert "Successfully wrote" in write_result.output

    # 2. Read file
    read_result = await read_tool.run({"path": target_file})
    assert read_result.success is True
    assert read_result.output == test_content

    # Clean up scratch test file
    scratch_path = validate_workspace_path(target_file)
    if scratch_path.exists():
        scratch_path.unlink()


@pytest.mark.asyncio
async def test_inspect_code_tool() -> None:
    """Verify InspectPythonCodeTool performs AST analysis without executing code."""
    inspect_tool = InspectPythonCodeTool()
    result = await inspect_tool.run({"path": "app/main.py"})

    assert result.success is True
    assert "Python AST Analysis" in result.output
    assert "Syntax Status: VALID" in result.output


@pytest.mark.asyncio
async def test_safe_command_executor_tool() -> None:
    """Verify SafeCommandExecutorTool executes allowed commands and blocks blacklisted patterns."""
    executor = SafeCommandExecutorTool()

    # Allowed command
    safe_result = await executor.run({"command": "python --version"})
    assert safe_result.success is True
    assert "Python" in safe_result.output

    # Blocked command (rm -rf)
    blocked_result = await executor.run({"command": "rm -rf /"})
    assert blocked_result.success is False
    assert "Security Block" in str(blocked_result.error)


@pytest.mark.asyncio
async def test_tools_api_endpoints(auth_client: AsyncClient) -> None:
    """Verify GET /api/v1/agent/tools/ and POST /api/v1/agent/tools/execute endpoints."""
    # List tools
    list_resp = await auth_client.get("/api/v1/agent/tools/")
    assert list_resp.status_code == 200
    tools_list = list_resp.json()
    assert len(tools_list) >= 5
    tool_names = [t["name"] for t in tools_list]
    assert "read_file" in tool_names
    assert "run_command" in tool_names

    # Execute tool
    exec_payload = {
        "tool_name": "list_directory",
        "parameters": {"path": "."}
    }
    exec_resp = await auth_client.post("/api/v1/agent/tools/execute", json=exec_payload)
    assert exec_resp.status_code == 200
    result_data = exec_resp.json()
    assert result_data["success"] is True
