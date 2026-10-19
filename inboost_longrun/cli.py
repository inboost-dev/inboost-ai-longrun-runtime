#!/usr/bin/env python3
"""
CLI launcher for InBoost LongRun Evaluation Runtime.
Resolves platform-native binary, ensures license is placed, and executes the engine.
"""

import contextlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path

VERSION = "0.3.0.post1"
GITHUB_REPO = "inboost-dev/inboost-ai-longrun-runtime"

RULES_CONTENT = """# InBoost LongRun Optimization Rules

1. **Context Conservation**: Before reading large files, use `l0_view_outline` to inspect declarations and structure.
2. **Test Failure Isolation**: Filter test logs and runtime exceptions via `l0_clean_test_log` to eliminate noise and isolate failing lines.
3. **Syntax Integrity**: Validate all code modifications and diffs with `l0_verify_syntax` prior to finalizing changes.
4. **Edit Scope Compliance**: Ensure edits remain focused and within budget. Verify with `l0_verify_edit_scope`.
5. **Execution Optimization**: Run test commands via `l0_run_test` for compact results. Check session economy with `l0_savings_report`.
"""


def get_binary_name() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        if machine in ("x86_64", "amd64"):
            return "inboost-longrun-linux-amd64"
        if machine in ("aarch64", "arm64"):
            return "inboost-longrun-linux-arm64"
    elif system == "darwin":
        if machine in ("arm64", "aarch64"):
            return "inboost-longrun-darwin-arm64"
        if machine in ("x86_64", "amd64"):
            return "inboost-longrun-darwin-amd64"
    elif system == "windows" and machine in ("x86_64", "amd64"):
        return "inboost-longrun-windows-amd64.exe"

    raise RuntimeError(f"Unsupported platform: {system} {machine}")


def find_windows_git_tool(tool: str) -> str | None:
    if platform.system().lower() != "windows":
        return None
    candidates = [
        os.environ.get("ProgramFiles", "C:\\Program Files"),
        os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
        (os.environ.get("LOCALAPPDATA") + "\\Programs") if os.environ.get("LOCALAPPDATA") else None,
        os.environ.get("ProgramW6432", "C:\\Program Files"),
    ]
    for base in candidates:
        if not base:
            continue
        candidate_path = Path(base) / "Git" / "usr" / "bin" / f"{tool}.exe"
        if candidate_path.exists():
            return str(candidate_path)
    return None


def check_system_dependencies(strict: bool = False) -> bool:
    """
    Verifies that system utilities required for InBoost LongRun local offload are present.
    Provides platform-specific package manager instructions for any missing dependencies.
    """
    is_win = platform.system().lower() == "windows"
    is_mac = platform.system().lower() == "darwin"

    sys.stdout.write("\nChecking system dependencies for Local Offload:\n")

    mandatory_tools = ["find", "grep", "diff", "patch", "git", "python3"]
    missing_mandatory = []

    for tool in mandatory_tools:
        p = shutil.which(tool)
        if not p and is_win and tool == "python3":
            p = shutil.which("python") or shutil.which("py")
        if is_win:
            if tool == "find":
                if p and "system32" in p.lower():
                    p = None
                if not p:
                    p = find_windows_git_tool("find")
            elif not p and tool in ("diff", "patch", "grep"):
                p = find_windows_git_tool(tool)

        if p:
            sys.stdout.write(f"  [\033[1;32m✓\033[0m] {tool} ({p})\n")
        else:
            sys.stdout.write(f"  [\033[1;31m✗\033[0m] {tool} (missing)\n")
            missing_mandatory.append(tool)

    recommended_tools = [
        ("ast-grep", ["sg"]),
        ("ruff", []),
        ("biome", []),
        ("docker", []),
    ]

    for name, fallbacks in recommended_tools:
        found = shutil.which(name)
        if not found:
            for fb in fallbacks:
                found = shutil.which(fb)
                if found:
                    break
        if found:
            sys.stdout.write(f"  [\033[1;32m✓\033[0m] {name} ({found}) [recommended acceleration]\n")
        else:
            sys.stdout.write(f"  [\033[1;33m○\033[0m] {name} (optional, recommended for <2ms local linting)\n")

    # Target AI Coding Agents & IDEs
    sys.stdout.write("\nChecking AI Coding Agents & IDEs:\n")
    agent_tools = [
        ("Claude Code", "claude", "claude mcp add inboost-longrun -- inboost-longrun serve"),
        ("Google Antigravity", "agy", "agy mcp add inboost-longrun inboost-longrun serve"),
        ("Cursor IDE", "cursor", "inboost-longrun init (configures .cursor/mcp.json)"),
        ("VS Code", "code", "add to .vscode/mcp.json or workspace rules"),
    ]
    for agent_name, agent_cmd, integration_hint in agent_tools:
        found_agent = shutil.which(agent_cmd)
        if not found_agent and is_win:
            found_agent = shutil.which(f"{agent_cmd}.cmd") or shutil.which(f"{agent_cmd}.exe")
        if not found_agent and agent_cmd == "cursor":
            if (Path.cwd() / ".cursor").exists() or (Path.home() / ".cursor").exists():
                found_agent = "detected via .cursor/ directory"

        if found_agent:
            sys.stdout.write(f"  [\033[1;32m✓\033[0m] {agent_name} ({found_agent})\n       Integration: {integration_hint}\n")
        else:
            sys.stdout.write(f"  [\033[1;33m○\033[0m] {agent_name} (optional, not found in PATH)\n")

    if missing_mandatory:
        pkg_map = {"find": "findutils", "diff": "diffutils"}
        pkg_list = " ".join(pkg_map.get(t, t) for t in missing_mandatory)
        sys.stderr.write(
            f"\n\033[1;31mError: Required tools missing for InBoost LongRun Local Offload: {', '.join(missing_mandatory)}\033[0m\n"
        )
        sys.stderr.write(
            "InBoost LongRun requires these tools locally to inspect outlines, calculate AST diffs, and filter test traces.\n"
        )
        sys.stderr.write("Please install the missing packages before proceeding:\n")

        if is_mac:
            sys.stderr.write(f"  \033[1;36mbrew install {pkg_list}\033[0m\n\n")
        elif is_win:
            sys.stderr.write(
                "  \033[1;36mwinget install --id Git.Git\033[0m (provides find, grep, diff, patch)\n\n"
            )
        else:
            sys.stderr.write(
                f"  Debian/Ubuntu: \033[1;36msudo apt-get update && sudo apt-get install -y {pkg_list}\033[0m\n"
            )
            sys.stderr.write(f"  RHEL/Fedora:   \033[1;36msudo dnf install -y {pkg_list}\033[0m\n")
            sys.stderr.write(f"  Alpine:        \033[1;36msudo apk add {pkg_list}\033[0m\n")
            sys.stderr.write(f"  Arch Linux:    \033[1;36msudo pacman -S {pkg_list}\033[0m\n\n")

        if strict and os.environ.get("INBOOST_IGNORE_MISSING_DEPS") != "1":
            sys.exit(1)
        return False

    sys.stdout.write("\033[1;32m✓ All core offload tools verified.\033[0m\n\n")
    return True


def ensure_license_installed(package_root: Path) -> None:
    inboost_home = Path.home() / ".inboost"
    inboost_home.mkdir(parents=True, exist_ok=True)
    target_lic = inboost_home / "inboost.lic"

    if not target_lic.exists():
        candidates = [
            package_root / "inboost.lic",
            package_root.parent / "inboost.lic",
            Path(__file__).parent / "inboost.lic",
        ]
        for c in candidates:
            if c.exists():
                with contextlib.suppress(OSError):
                    shutil.copy2(c, target_lic)
                    break


def handle_init(package_root: Path) -> None:
    user_home = Path.home()
    cwd = Path.cwd()

    # 1. Global Claude Code rules (~/.claude/rules/inboost_longrun.md)
    with contextlib.suppress(OSError):
        global_claude = user_home / ".claude" / "rules"
        global_claude.mkdir(parents=True, exist_ok=True)
        (global_claude / "inboost_longrun.md").write_text(RULES_CONTENT, encoding="utf-8")

    with contextlib.suppress(OSError):
        global_agents = user_home / ".agents" / "rules"
        global_agents.mkdir(parents=True, exist_ok=True)
        (global_agents / "inboost_longrun.md").write_text(RULES_CONTENT, encoding="utf-8")

    # 2. Local rules in current directory (.claude/rules and .cursorrules)
    with contextlib.suppress(OSError):
        local_claude = cwd / ".claude" / "rules"
        local_claude.mkdir(parents=True, exist_ok=True)
        (local_claude / "inboost_longrun.md").write_text(RULES_CONTENT, encoding="utf-8")

    with contextlib.suppress(OSError):
        local_agents = cwd / ".agents" / "rules"
        local_agents.mkdir(parents=True, exist_ok=True)
        (local_agents / "inboost_longrun.md").write_text(RULES_CONTENT, encoding="utf-8")

    with contextlib.suppress(OSError):
        cursorrules = cwd / ".cursorrules"
        existing = cursorrules.read_text(encoding="utf-8") if cursorrules.exists() else ""
        if "InBoost LongRun Optimization Rules" not in existing:
            glue = "\n\n" if existing.strip() else ""
            cursorrules.write_text(existing + glue + RULES_CONTENT, encoding="utf-8")

    # 3. .cursor/mcp.json
    with contextlib.suppress(OSError):
        cursor_dir = cwd / ".cursor"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        mcp_file = cursor_dir / "mcp.json"
        mcp_config = {"mcpServers": {}}
        if mcp_file.exists():
            with contextlib.suppress(json.JSONDecodeError, OSError):
                loaded = json.loads(mcp_file.read_text(encoding="utf-8"))
                if isinstance(loaded, dict) and isinstance(loaded.get("mcpServers"), dict):
                    mcp_config = loaded
        mcp_config["mcpServers"]["inboost-longrun"] = {
            "command": "inboost-longrun",
            "args": ["serve"],
        }
        mcp_file.write_text(json.dumps(mcp_config, indent=2) + "\n", encoding="utf-8")

    ensure_license_installed(package_root)
    sys.stdout.write("✓ InBoost LongRun rules & skills successfully configured for Claude Code and Cursor!\n")


def find_or_download_binary() -> Path:
    bin_name = get_binary_name()
    package_dir = Path(__file__).resolve().parent
    repo_root = package_dir.parent

    # Check candidates
    candidates = [
        package_dir / "bin" / bin_name,
        package_dir / bin_name,
        repo_root / "bin" / bin_name,
        repo_root / "bin" / "inboost-longrun",
        Path.home() / ".local" / "bin" / "inboost-longrun",
        Path("/usr/local/bin/inboost-longrun"),
        Path.home() / ".inboost" / "bin" / bin_name,
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            if os.name != "nt":
                with contextlib.suppress(OSError):
                    candidate.chmod(candidate.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            return candidate

    # Check PATH
    which_bin = shutil.which("inboost-longrun")
    if which_bin:
        return Path(which_bin)

    # Download if missing
    inboost_bin_dir = Path.home() / ".inboost" / "bin"
    inboost_bin_dir.mkdir(parents=True, exist_ok=True)
    target_path = inboost_bin_dir / bin_name

    repos = [GITHUB_REPO, "inboost-dev/inboost-longrun", "inboost-dev/inboost-ai-longrun-runtime"]
    repos = list(dict.fromkeys(repos))
    last_err: Exception | None = None

    tag_clean = "0.3.0"
    candidates_urls = []
    for repo in repos:
        candidates_urls.extend([
            f"https://raw.githubusercontent.com/{repo}/v{tag_clean}/bin/{bin_name}",
            f"https://github.com/{repo}/raw/v{tag_clean}/bin/{bin_name}",
            f"https://github.com/{repo}/releases/download/v{tag_clean}/{bin_name}",
            f"https://raw.githubusercontent.com/{repo}/main/bin/{bin_name}",
        ])

    for download_url in candidates_urls:
        sys.stderr.write(f"InBoost LongRun binary not found locally. Downloading from {download_url}...\n")
        try:
            urllib.request.urlretrieve(download_url, str(target_path))
            if os.name != "nt":
                target_path.chmod(target_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            return target_path
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"Failed to download InBoost LongRun binary: {last_err}") from last_err


def main() -> None:
    package_root = Path(__file__).resolve().parent.parent
    raw_args = sys.argv[1:]

    if any(arg in raw_args for arg in ("check", "doctor", "--check")):
        ok = check_system_dependencies(strict=True)
        sys.exit(0 if ok else 1)

    if "init" in raw_args:
        check_system_dependencies(strict=False)
        handle_init(package_root)
        sys.exit(0)

    if os.environ.get("INBOOST_STRICT_DEPS") == "1":
        check_system_dependencies(strict=True)

    ensure_license_installed(package_root)

    try:
        binary_path = find_or_download_binary()
    except (RuntimeError, OSError) as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    args = [str(binary_path)] + raw_args

    # On POSIX, replace process with execv
    if os.name == "posix":
        try:
            os.execv(str(binary_path), args)
        except OSError as e:
            sys.stderr.write(f"Failed to execute {binary_path}: {e}\n")
            sys.exit(1)
    else:
        # On Windows, run via subprocess
        try:
            res = subprocess.run(args, check=False)
            sys.exit(res.returncode)
        except OSError as e:
            sys.stderr.write(f"Execution failed: {e}\n")
            sys.exit(1)


if __name__ == "__main__":
    main()
