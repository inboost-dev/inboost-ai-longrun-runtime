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


def test_node_init_command(tmp_path):
    js_cli = REPO_ROOT / "bin" / "inboost-longrun.js"
    res = subprocess.run(
        ["node", str(js_cli), "init"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "✓ InBoost LongRun rules & skills successfully configured for Claude Code and Cursor!" in res.stdout
    assert (tmp_path / ".cursorrules").exists()
    assert (tmp_path / ".cursor" / "mcp.json").exists()
    assert (tmp_path / ".claude" / "rules" / "inboost_longrun.md").exists()
    mcp_data = json.loads((tmp_path / ".cursor" / "mcp.json").read_text(encoding="utf-8"))
    assert "inboost-longrun" in mcp_data["mcpServers"]


def test_python_init_command(tmp_path):
    py_cli = REPO_ROOT / "inboost_longrun" / "cli.py"
    res = subprocess.run(
        [sys.executable, str(py_cli), "init"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "✓ InBoost LongRun rules & skills successfully configured for Claude Code and Cursor!" in res.stdout
    assert (tmp_path / ".cursorrules").exists()
    assert (tmp_path / ".cursor" / "mcp.json").exists()
    assert (tmp_path / ".claude" / "rules" / "inboost_longrun.md").exists()


def test_install_script_dependency_preflight(tmp_path):
    """Verify that install.sh checks for find, grep, diff, patch, git, python3."""
    import re
    import shutil
    install_sh = REPO_ROOT / "install.sh"
    assert install_sh.exists(), "install.sh not found"

    def clean_ansi(text: str) -> str:
        return re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)

    # 1. Normal run with existing dependencies
    res = subprocess.run(
        ["bash", str(install_sh)],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    clean_out = clean_ansi(res.stdout)
    assert "Checking system dependencies for Local Offload:" in clean_out
    assert "[✓] find" in clean_out
    assert "[✓] grep" in clean_out
    assert "[✓] diff" in clean_out
    assert "[✓] patch" in clean_out
    assert "[✓] git" in clean_out
    assert "[✓] python3" in clean_out
    assert "All core offload tools verified" in clean_out

    # 2. Simulated missing dependency (diff)
    fake_bin = tmp_path / "fake_bin"
    fake_bin.mkdir()
    for tool_name in ["bash", "uname", "tr", "id", "mkdir", "dirname", "pwd", "echo", "cat", "find", "grep", "patch", "git", "python3"]:
        src = shutil.which(tool_name)
        if src:
            (fake_bin / tool_name).symlink_to(src)

    fake_env = {"PATH": str(fake_bin), "HOME": str(tmp_path)}
    res_missing = subprocess.run(
        ["bash", str(install_sh)],
        env=fake_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_missing.returncode != 0
    clean_missing = clean_ansi(res_missing.stdout)
    assert "[✗] diff (missing)" in clean_missing
    assert "Required tools missing for InBoost LongRun Local Offload: diff" in clean_missing
    assert "diffutils" in clean_missing


def test_npm_preflight_checks(tmp_path):
    import re
    import shutil

    js_entry = REPO_ROOT / "bin" / "inboost-longrun.js"
    assert js_entry.exists(), "bin/inboost-longrun.js not found"
    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("Node.js is not installed on this system")

    def clean_ansi(text: str) -> str:
        return re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)

    # 1. Test check command
    res = subprocess.run(
        [node_bin, str(js_entry), "check"],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    clean_out = clean_ansi(res.stdout)
    assert "Checking system dependencies for Local Offload:" in clean_out
    assert "[✓] find" in clean_out
    assert "[✓] diff" in clean_out
    assert "All core offload tools verified" in clean_out

    # 2. Test missing dependencies in strict mode
    fake_bin = tmp_path / "fake_bin_npm"
    fake_bin.mkdir()
    for tool_name in ["node", "sh", "find", "grep", "patch", "git", "python3"]:
        src = shutil.which(tool_name)
        if src:
            (fake_bin / tool_name).symlink_to(src)

    fake_env = {"PATH": str(fake_bin), "HOME": str(tmp_path)}
    res_missing = subprocess.run(
        [node_bin, str(js_entry), "check"],
        env=fake_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_missing.returncode != 0
    clean_missing = clean_ansi(res_missing.stderr)
    assert "Required tools missing for InBoost LongRun Local Offload: diff" in clean_missing


def test_pip_cli_preflight_checks(tmp_path):
    import re
    import shutil

    cli_py = REPO_ROOT / "inboost_longrun" / "cli.py"
    assert cli_py.exists(), "inboost_longrun/cli.py not found"

    def clean_ansi(text: str) -> str:
        return re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)

    # 1. Normal run check
    res = subprocess.run(
        [sys.executable, str(cli_py), "check"],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    clean_out = clean_ansi(res.stdout)
    assert "Checking system dependencies for Local Offload:" in clean_out
    assert "[✓] find" in clean_out
    assert "[✓] diff" in clean_out
    assert "All core offload tools verified" in clean_out

    # 2. Python module execution check
    res_mod = subprocess.run(
        [sys.executable, "-m", "inboost_longrun", "check"],
        env=dict(os.environ, PYTHONPATH=str(REPO_ROOT)),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_mod.returncode == 0
    assert "All core offload tools verified" in clean_ansi(res_mod.stdout)

    # 3. Missing dependencies simulation
    fake_bin = tmp_path / "fake_bin_pip"
    fake_bin.mkdir()
    for tool_name in ["python3", "find", "grep", "patch", "git"]:
        src = shutil.which(tool_name)
        if src:
            (fake_bin / tool_name).symlink_to(src)

    fake_env = {"PATH": str(fake_bin), "HOME": str(tmp_path), "PYTHONPATH": str(REPO_ROOT)}
    res_missing = subprocess.run(
        [sys.executable, str(cli_py), "check"],
        env=fake_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_missing.returncode != 0
    clean_missing = clean_ansi(res_missing.stderr)
    assert "Required tools missing for InBoost LongRun Local Offload: diff" in clean_missing
    assert "diffutils" in clean_missing


def test_cross_platform_cli_macos_and_windows():
    import io
    import re
    import sys
    from unittest.mock import patch

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    from inboost_longrun.cli import check_system_dependencies

    def clean_ansi(text: str) -> str:
        return re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)

    # 1. macOS with missing diff
    captured_err = io.StringIO()
    with patch("platform.system", return_value="Darwin"), \
         patch("shutil.which", side_effect=lambda t: None if t == "diff" else "/usr/bin/" + t), \
         patch("sys.stderr", captured_err):
        ok = check_system_dependencies(strict=False)
    assert ok is False
    assert "brew install diffutils" in clean_ansi(captured_err.getvalue())

    # 2. Windows with missing diff and python fallback
    captured_err = io.StringIO()
    captured_out = io.StringIO()
    with patch("platform.system", return_value="Windows"), \
         patch("shutil.which", side_effect=lambda t: "C:/Python312/python.exe" if t == "python" else (None if t in ("python3", "diff") else "C:/tools/" + t)), \
         patch("sys.stderr", captured_err), \
         patch("sys.stdout", captured_out):
        ok = check_system_dependencies(strict=False)
    assert ok is False
    assert "winget install --id Git.Git" in clean_ansi(captured_err.getvalue())
    assert "[✓] python3 (C:/Python312/python.exe)" in clean_ansi(captured_out.getvalue())

    # 3. Windows System32 find trap
    captured_err = io.StringIO()
    captured_out = io.StringIO()
    with patch("platform.system", return_value="Windows"), \
         patch("shutil.which", side_effect=lambda t: "C:/Windows/System32/find.exe" if t == "find" else "C:/tools/" + t), \
         patch("pathlib.Path.exists", return_value=False), \
         patch("sys.stderr", captured_err), \
         patch("sys.stdout", captured_out):
        ok = check_system_dependencies(strict=False)
    assert ok is False
    assert "[✗] find (missing)" in clean_ansi(captured_out.getvalue())


def test_doctor_command_and_agent_detection():
    import re
    import shutil

    cli_py = REPO_ROOT / "inboost_longrun" / "cli.py"
    res = subprocess.run(
        [sys.executable, str(cli_py), "doctor"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    clean_out = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", res.stdout)
    assert "Checking AI Coding Agents & IDEs:" in clean_out
    assert "Claude Code" in clean_out
    assert "Google Antigravity" in clean_out
    assert "Cursor IDE" in clean_out

    node_bin = shutil.which("node")
    if node_bin:
        js_entry = REPO_ROOT / "bin" / "inboost-longrun.js"
        res_node = subprocess.run(
            [node_bin, str(js_entry), "doctor"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert res_node.returncode == 0
        clean_node = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", res_node.stdout)
        assert "Checking AI Coding Agents & IDEs:" in clean_node
        assert "Claude Code" in clean_node
        assert "Cursor IDE" in clean_node


def test_benchmarks_harness_dry_run(tmp_path):
    bare_script = REPO_ROOT / "benchmarks" / "scripts" / "run_bare_agy.py"
    lr_script = REPO_ROOT / "benchmarks" / "scripts" / "run_inboost_longrun.py"
    score_script = REPO_ROOT / "benchmarks" / "scripts" / "compare_and_scorecard.py"

    bare_out = tmp_path / "bare_run"
    lr_out = tmp_path / "lr_run"

    # 1. Run bare dry-run (1 task)
    res_bare = subprocess.run(
        [sys.executable, str(bare_script), "--dry-run", "--max-tasks", "1", "--output-dir", str(bare_out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_bare.returncode == 0
    assert (bare_out / "predictions.jsonl").exists()
    assert (bare_out / "metrics.json").exists()

    # 2. Run longrun dry-run (1 task)
    res_lr = subprocess.run(
        [sys.executable, str(lr_script), "--dry-run", "--max-tasks", "1", "--output-dir", str(lr_out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_lr.returncode == 0
    assert (lr_out / "predictions.jsonl").exists()
    assert (lr_out / "metrics.json").exists()

    # 3. Compare and scorecard
    card_md = tmp_path / "SCORECARD.md"
    card_json = tmp_path / "comparison.json"
    res_score = subprocess.run(
        [
            sys.executable,
            str(score_script),
            "--bare-dir",
            str(bare_out),
            "--longrun-dir",
            str(lr_out),
            "--output-md",
            str(card_md),
            "--output-json",
            str(card_json),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_score.returncode == 0
    assert card_md.exists()
    assert card_json.exists()





