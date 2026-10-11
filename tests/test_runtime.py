"""
InBoost LongRun Evaluation Runtime - Comprehensive Test Suite
Verifies binary execution, Ed25519 1-month license expiration, MCP JSON-RPC protocol,
L0 tools functionality, and distribution checksums.
"""

import datetime
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BIN_PATH = REPO_ROOT / "bin" / "inboost-longrun"
LIC_PATH = REPO_ROOT / "inboost.lic"


def run_binary(*args, env=None) -> subprocess.CompletedProcess:
    cmd_env = os.environ.copy()
    if env:
        cmd_env.update(env)
    return subprocess.run(
        [str(BIN_PATH)] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=cmd_env,
        timeout=10,
    )


def send_jsonrpc(requests: list, env=None) -> list:
    cmd_env = os.environ.copy()
    if env:
        cmd_env.update(env)

    input_data = "\n".join(json.dumps(r) for r in requests) + "\n"
    proc = subprocess.run(
        [str(BIN_PATH)],
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=cmd_env,
        timeout=10,
    )
    responses = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line:
            try:
                responses.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return responses


def test_binary_exists():
    assert BIN_PATH.exists(), f"Binary {BIN_PATH} not found"
    assert os.access(BIN_PATH, os.X_OK), f"Binary {BIN_PATH} is not executable"


def test_version_command():
    res = run_binary("version")
    assert res.returncode == 0
    assert "InBoost AI LongRun" in res.stdout
    assert "v1.0.0" in res.stdout


def test_status_command():
    res = run_binary("status")
    assert res.returncode == 0
    assert "Status:         ACTIVE" in res.stdout
    assert "Active 1-Month Evaluation License" in res.stdout


def test_license_one_month_limit():
    """Verify license expiration is strictly limited to 1 month."""
    assert LIC_PATH.exists(), f"License file {LIC_PATH} not found"
    with open(LIC_PATH, "r", encoding="utf-8") as f:
        lic_data = json.load(f)

    payload = lic_data["payload"]
    assert payload["tier"] == "enterprise_pilot"

    # Verify timestamps
    valid_from = datetime.datetime.fromisoformat(payload["valid_from"].replace("Z", "+00:00"))
    valid_until = datetime.datetime.fromisoformat(payload["valid_until"].replace("Z", "+00:00"))

    duration = valid_until - valid_from
    days = duration.total_seconds() / 86400.0

    # Exactly 31.99 days (1 calendar month from 2026-10-11 to 2026-11-11)
    assert 28.0 <= days <= 32.0, f"License duration {days} days is not 1 month"
    assert valid_until.year == 2026
    assert valid_until.month == 11
    assert valid_until.day == 11

    # Verify CLI reports active status with remaining time <= 32 days
    res = run_binary("status")
    assert res.returncode == 0
    assert "ACTIVE" in res.stdout
    assert "remaining" in res.stdout


def test_tampered_license_rejection(tmp_path):
    """Verify that tampering with the license date causes Ed25519 signature failure."""
    with open(LIC_PATH, "r", encoding="utf-8") as f:
        lic_data = json.load(f)

    # Tamper with the expiration date
    lic_data["payload"]["valid_until"] = "2029-12-31T23:59:59Z"
    tampered_file = tmp_path / "tampered.lic"
    tampered_file.write_text(json.dumps(lic_data))

    res = run_binary("status", env={"INBOOST_LICENSE_FILE": str(tampered_file)})
    assert res.returncode != 0
    assert "EXPIRED" in res.stdout or "invalid" in res.stdout.lower()


def test_mcp_protocol_initialize():
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    }
    responses = send_jsonrpc([req])
    assert len(responses) >= 1
    resp = responses[0]
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "inboost-longrun"
    assert "tools" in resp["result"]["capabilities"]


def test_mcp_tools_list():
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}},
    }
    tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    responses = send_jsonrpc([init_req, tools_req])
    assert len(responses) >= 2
    tools_resp = responses[1]
    assert tools_resp["id"] == 2
    tools = {t["name"] for t in tools_resp["result"]["tools"]}

    expected_tools = {
        "l0_view_outline",
        "l0_clean_test_log",
        "l0_verify_syntax",
        "l0_verify_edit_scope",
        "l0_run_test",
        "l0_savings_report",
    }
    assert expected_tools.issubset(tools)


def test_tool_l0_verify_syntax_valid():
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}},
    }
    call_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "l0_verify_syntax",
            "arguments": {
                "file_path": "example.py",
                "content": "def calculate(a, b):\n    return a + b\n",
            },
        },
    }
    responses = send_jsonrpc([init_req, call_req])
    assert len(responses) >= 2
    call_resp = responses[1]
    assert call_resp["id"] == 3
    content_text = call_resp["result"]["content"][0]["text"]
    assert "syntax is valid" in content_text.lower() or "0 syntax errors" in content_text


def test_tool_l0_verify_syntax_invalid():
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}},
    }
    call_req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "l0_verify_syntax",
            "arguments": {
                "file_path": "broken.py",
                "content": "def broken_func(\n    return 42\n",
            },
        },
    }
    responses = send_jsonrpc([init_req, call_req])
    assert len(responses) >= 2
    call_resp = responses[1]
    assert call_resp["id"] == 4
    content_text = call_resp["result"]["content"][0]["text"]
    assert "syntax validation issue" in content_text.lower() or "unclosed" in content_text.lower()


def test_tool_l0_savings_report():
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}},
    }
    call_req = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {"name": "l0_savings_report", "arguments": {}},
    }
    responses = send_jsonrpc([init_req, call_req])
    assert len(responses) >= 2
    call_resp = responses[1]
    assert call_resp["id"] == 5
    content_text = call_resp["result"]["content"][0]["text"]
    assert "SAVINGS SCORECARD" in content_text or "Savings" in content_text


def test_distribution_checksums():
    sums_file = REPO_ROOT / "dist" / "SHA256SUMS"
    assert sums_file.exists(), "dist/SHA256SUMS file missing"

    with open(sums_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        expected_hash, filename = line.split(None, 1)
        artifact_path = REPO_ROOT / "dist" / filename
        assert artifact_path.exists(), f"Archive {filename} listed in SHA256SUMS does not exist"

        hasher = hashlib.sha256()
        with open(artifact_path, "rb") as af:
            while chunk := af.read(65536):
                hasher.update(chunk)
        actual_hash = hasher.hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {filename}: {actual_hash} != {expected_hash}"
