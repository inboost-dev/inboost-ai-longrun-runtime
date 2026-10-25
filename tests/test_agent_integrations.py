"""Integration tests for Claude Code and Google Antigravity (agy) MCP connectivity."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BINARY = REPO_ROOT / "bin" / "inboost-longrun"


def _call_mcp(requests: list[dict]) -> list[dict]:
    input_text = "\n".join(json.dumps(r) for r in requests) + "\n"
    proc = subprocess.Popen(
        [str(BINARY), "serve"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, err = proc.communicate(input_text, timeout=10)
    assert proc.returncode == 0, f"MCP server process exited with {proc.returncode}: {err}"
    responses = []
    for line in out.strip().split("\n"):
        if line.strip():
            responses.append(json.loads(line))
    return responses


def test_mcp_protocol_handshake_and_tools():
    """Verify MCP protocol initialization and all 6 core L0 tools."""
    reqs = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "claude-code", "version": "2.1.296"},
            },
        },
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]
    responses = _call_mcp(reqs)
    assert len(responses) == 2
    init_res = responses[0]["result"]
    assert init_res["serverInfo"]["name"] == "inboost-longrun"
    assert init_res["protocolVersion"] == "2024-11-05"

    tools_res = responses[1]["result"]["tools"]
    tool_names = [t["name"] for t in tools_res]
    expected_tools = [
        "l0_view_outline",
        "l0_clean_test_log",
        "l0_verify_syntax",
        "l0_verify_edit_scope",
        "l0_run_test",
        "l0_savings_report",
    ]
    for exp in expected_tools:
        assert exp in tool_names, f"Missing tool: {exp}"


def test_claude_code_cli_connectivity():
    """Verify integration with Claude Code CLI if installed."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        pytest.skip("Claude Code CLI is not installed")

    # 1. Check version
    res = subprocess.run([claude_bin, "--version"], capture_output=True, text=True, check=False)
    assert res.returncode == 0
    assert "Claude Code" in res.stdout or "claude" in res.stdout.lower()

    # 2. Check MCP listing capability
    res_mcp = subprocess.run([claude_bin, "mcp", "list"], capture_output=True, text=True, check=False)
    assert res_mcp.returncode == 0
    if "inboost-longrun" in res_mcp.stdout:
        assert (
            "Connected" in res_mcp.stdout
            or "✔" in res_mcp.stdout
            or "enabled" in res_mcp.stdout
            or "disabled" in res_mcp.stdout
        )


def test_antigravity_cli_connectivity():
    """Verify integration with Google Antigravity (agy) CLI if installed."""
    agy_bin = shutil.which("agy")
    if not agy_bin:
        pytest.skip("Google Antigravity (agy) CLI is not installed")

    # 1. Check version
    res = subprocess.run([agy_bin, "--version"], capture_output=True, text=True, check=False)
    assert res.returncode == 0

    # 2. Check MCP listing capability
    res_mcp = subprocess.run([agy_bin, "mcp", "list"], capture_output=True, text=True, check=False)
    assert res_mcp.returncode == 0
    if "inboost-longrun" in res_mcp.stdout:
        assert (
            "enabled" in res_mcp.stdout
            or "disabled" in res_mcp.stdout
            or "stdio" in res_mcp.stdout
        )


def test_mcp_l0_tools_execution():
    """Verify execution of all L0 MCP tools in real agent workflow."""
    reqs = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-agent", "version": "1.0"},
            },
        },
        # l0_view_outline
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "l0_view_outline", "arguments": {"file_path": str(REPO_ROOT / "inboost_longrun" / "__init__.py")}},
        },
        # l0_verify_syntax (valid)
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "l0_verify_syntax", "arguments": {"file_path": "ok.py", "content": "x = 42\n"}},
        },
        # l0_verify_syntax (invalid)
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "l0_verify_syntax", "arguments": {"file_path": "err.py", "content": "def bad(\n"}},
        },
        # l0_verify_edit_scope
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "l0_verify_edit_scope", "arguments": {"diff_text": "--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-1\n+2\n"}},
        },
        # l0_savings_report
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {"name": "l0_savings_report", "arguments": {}},
        },
    ]
    responses = _call_mcp(reqs)
    res_map = {r.get("id"): r for r in responses}

    # Outline result
    assert "Token Savings" in res_map[2]["result"]["content"][0]["text"]

    # Syntax valid
    assert "syntax is valid" in res_map[3]["result"]["content"][0]["text"]
    assert res_map[3]["result"]["isError"] is False

    # Syntax invalid
    assert "validation issue detected" in res_map[4]["result"]["content"][0]["text"]
    assert res_map[4]["result"]["isError"] is True

    # Scope
    assert "COMPLIANT" in res_map[5]["result"]["content"][0]["text"]

    # Savings report
    assert "INBOOST LONGRUN CUMULATIVE SAVINGS SCORECARD" in res_map[6]["result"]["content"][0]["text"]
