# InBoost LongRun Evaluation Runtime

[![npm version](https://img.shields.io/npm/v/inboost-longrun?color=blue&logo=npm)](https://www.npmjs.com/package/inboost-longrun)
[![PyPI version](https://img.shields.io/pypi/v/inboost-longrun?color=blue&logo=pypi)](https://pypi.org/project/inboost-longrun/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-blue.svg)](#supported-platforms)
[![Architecture](https://img.shields.io/badge/arch-x86__64%20%7C%20ARM64-blue.svg)](#supported-platforms)
[![License](https://img.shields.io/badge/license-Evaluation%20License-orange.svg)](LICENSE_EVALUATION.md)
[![Privacy](https://img.shields.io/badge/privacy-100%25%20Local%20CPU-brightgreen.svg)](#privacy--data-security)
[![Tests](https://img.shields.io/badge/tests-25%20passed-brightgreen.svg)](#testing--verification)

> **Local context conservation, rate-limit extension, and verification engine for AI coding agents.**  
> *(Universal Multi-Platform Binary & Script Distribution Runtime)*.  
> Compatible with **Claude Code**, **Google Antigravity (`agy`)**, **Cursor**, **Windsurf**, and **OpenHands**.

---

## 💡 Developer Advantages

Autonomous coding agents burn through token budgets and model rate limits quickly when inspecting unfamiliar codebases and iterating on failing test suites. **InBoost LongRun** operates as a local intelligence filter and verification layer right on your machine, keeping your agent's context clean, focused, and economical.

* **Extended Rate-Limit Runway:** Stay productive longer and prevent hitting hourly message caps or quota exhaustion walls during deep refactoring and long-running agent tasks.
* **Lower Token Consumption & Costs:** Prevent agents from ingesting thousands of redundant tokens from full file dumps and verbose framework test logs.
* **Faster Turnaround & Latency:** Significantly decrease time-to-first-token and overall turn completion times by maintaining lean context windows.
* **Elimination of Wasted Repair Loops:** Local syntax and scope verification intercepts broken edits on your CPU before files are saved, eliminating expensive multi-turn roundtrips to fix trivial mistakes.
* **100% Local Privacy Guarantee:** All analysis, verification, and filtering routines run entirely on your local CPU. Your code, diffs, and prompts never leave your workstation.

---

## 📚 Documentation & Guides

- [**Getting Started & Interactive Examples**](GETTING_STARTED.md): 2-minute quickstart, host CPU offload tools, MCP server for Claude Code/Cursor/Antigravity, and SWE-bench task walkthrough.
- [**Benchmark Publication Guidelines & Standards**](BENCHMARKS.md): Full $N=500$ SWE-bench Verified results (+9.40% net rescue rate, 47 / 500 tasks), decoupled Docker accounting, and DeepSeek-V4.1 / Gemini 4 Argon validation.
- [**Evaluation License Agreement**](LICENSE): Terms of use for the InBoost LongRun Evaluation Edition.

---

## 📊 SWE-bench Verified Benchmarks ($N=500$ Full Suite)

Official evaluation of **Google Antigravity (`agy`)** accelerated with InBoost LongRun across the complete 500-task suite of **SWE-bench Verified** (50 cohorts $\times$ 10 tasks) under strict Docker CI execution (Docker v5.0.2):

* **🟢 +9.40% Absolute Resolve Boost:** Solves **451 / 500 tasks (90.20%)** vs 404 / 500 tasks (80.80%) on bare baseline (+47 net rescued tasks, +11.63% relative gain).
* **🛡️ 100% Elimination of Empty Diffs:** Zero 0-byte surrender failures (**0.00% vs 9.40% / 47 tasks on bare baseline**).
* **⚡️ 2.63x Lower Context Load:** **-61.9% tokens** consumed per session by crushing framework test noise and eliminating redundant file reads on CPU.
* **⏱️ 5.2 Hours Saved in Latency:** Accelerates time-to-patch by **-34.9%** (35,113s vs 53,943s) under a predictable flat subscription with zero host CAPEX.
* **🎯 Zero Regressions:** 0 regressions across all 500 tasks (0 tasks where bare passed and LongRun failed).

| Metric | Vanilla `agy` Baseline | `agy` + InBoost LongRun | Official Delta |
| :--- | :---: | :---: | :---: |
| **Pass@1 Resolve Rate** | `80.80%` (404 / 500) | **`90.20%` (451 / 500)** 🏆 | **🟢 +9.40% absolute (+47 tasks net)** |
| **Empty Patches (0 bytes)** | `9.40%` (47 / 500) | **`0.00%` (0 / 500)** | **🛡️ 100% elimination (47 rescued)** |
| **Patch Apply Errors** | `0.60%` (3 / 500) | **`0.00%` (0 / 500)** | **100% valid syntax via AST Guard** |
| **Regressions (Bare Pass $\to$ LR Fail)** | — | **0 tasks (0.0%)** | **0 regressions across 500 tasks** |
| **Agent Wall-Clock Latency** | 53,943.2s | **35,113.3s (-34.9%)** | **⏱️ 5.2 hours saved** |
| **Session Token Reduction** | 1.0x (Baseline) | **-61.9% tokens** | **⚡ 2.63x lower context load** |

👉 **[View Complete Benchmark Methodology, Per-Cohort Docker Logs & Scorecards →](benchmarks/README.md)**  
👉 **[Independent Auditor & Skeptic Reproduction Guide →](benchmarks/REPRODUCE.md)**

---

## 📦 Packages & Distribution

InBoost LongRun is distributed across official package registries and standalone binaries:

| Registry | Primary Package | Alias / Scoped Packages | Description |
| :--- | :--- | :--- | :--- |
| **npm** | [`inboost-longrun`](https://www.npmjs.com/package/inboost-longrun) | [`inboost-ai-longrun`](https://www.npmjs.com/package/inboost-ai-longrun)<br>[`@inboost-pro/inboost-longrun`](https://www.npmjs.com/package/@inboost-pro/inboost-longrun)<br>[`@inboost-pro/inboost-ai-longrun`](https://www.npmjs.com/package/@inboost-pro/inboost-ai-longrun) | Universal Node.js CLI & npx runner |
| **PyPI** | [`inboost-longrun`](https://pypi.org/project/inboost-longrun/) | [`inboost-ai-longrun`](https://pypi.org/project/inboost-ai-longrun/) | Python CLI wrapper with native acceleration |
| **Binary Releases** | [GitHub Releases](https://github.com/inboost-dev/inboost-ai-longrun-runtime/releases) | Linux (x86_64, ARM64), macOS (Apple Silicon, Intel), Windows | Universal standalone binaries (0 dependencies) |

---

## 🚀 Quick Install

### ⚡️ 2-Line Zero-Friction Setup (Recommended)

Install globally and run `init` to automatically configure rules and MCP servers across Claude Code, Cursor, and Antigravity:

```bash
npm install -g @inboost-pro/inboost-longrun
inboost-longrun init
```

*Or run instantly with zero installation via `npx`:*
```bash
npx @inboost-pro/inboost-longrun init
```

The `init` command automatically:
1. Copies optimization directives to global `~/.claude/rules/inboost_longrun.md` and `~/.agents/rules/inboost_longrun.md`.
2. Configures project directives in `.cursorrules` and `.claude/rules/inboost_longrun.md`.
3. Registers the `inboost-longrun` MCP server inside `.cursor/mcp.json`.
4. Runs a non-blocking diagnostic of host tools and detected AI agents.

### 🩺 System Diagnostics (`doctor` / `check`)

Verify that your system has all required offload tools and detect available AI agents:

```bash
inboost-longrun doctor
# Or via npx:
npx inboost-longrun doctor
```

The diagnostic verifies:
- **Core Offload Utilities:** `find`, `grep`, `diff`, `patch`, `git`, `python3` (with automated package manager guidance on Linux, macOS `brew`, and Windows `winget`).
- **Acceleration Linters:** `ast-grep` (<2ms AST search), `ruff` (<2ms Python lint), `biome` (<2ms JS/TS), `docker`.
- **Target AI Agents & IDEs:** Automatically discovers `Claude Code`, `Google Antigravity` (`agy`), `Cursor IDE`, and `VS Code` with ready-to-run setup commands.

---

### Option 1: Instant Execution via `npx`

Run directly with zero pre-installation:

```bash
# Check evaluation status and remaining runway
npx inboost-longrun status

# Start Model Context Protocol (MCP) server
npx inboost-longrun serve
```

Or install globally via npm:

```bash
npm install -g inboost-longrun
inboost-longrun status
```

*(You can also use the alias package `npx inboost-ai-longrun` or organization packages `npx @inboost-pro/inboost-longrun` / `npx @inboost-pro/inboost-ai-longrun`).*

### Option 2: Python (`pip`)

```bash
pip install inboost-longrun
inboost-longrun status
inboost-longrun serve
```

*(Alias package `pip install inboost-ai-longrun` is also available).*

### Option 3: One-Line Standalone Shell Installers

**Linux & macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/inboost-dev/inboost-ai-longrun-runtime/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/inboost-dev/inboost-ai-longrun-runtime/main/install.ps1 | iex
```

### Option 4: Local Repository Build

```bash
git clone https://github.com/inboost-dev/inboost-ai-longrun-runtime.git
cd inboost-ai-longrun-runtime
./install.sh
```

---

## 🛠 Model Context Protocol (MCP) Tools

InBoost LongRun integrates seamlessly into your AI assistant or IDE through the standard **Model Context Protocol (MCP)**, providing local tools designed to maximize context economy and coding accuracy:

| Tool | Purpose & Developer Advantage |
| :--- | :--- |
| **`l0_view_outline`** | **Structural Code Inspection:** Gives your AI assistant a clear map of symbols, functions, and definitions without spending thousands of tokens reading full file bodies. |
| **`l0_clean_test_log`** | **Noise-Free Error Isolation:** Strips framework noise from test logs (pytest, unittest, jest) to expose the root-cause failure, preventing context pollution. |
| **`l0_verify_syntax`** | **Instant Syntax Guardrail:** Verifies code correctness on your local CPU before saving, preventing wasted prompt turns on syntax errors. |
| **`l0_verify_edit_scope`** | **Targeted Change Guardrail:** Keeps code modifications focused and within budget, stopping runaway diffs before they happen. |
| **`l0_run_test`** | **Compact Test Execution:** Runs local test suites and returns clean, signal-dense output tailored for agent decision-making. |
| **`l0_savings_report`** | **Savings & Quota Ledger:** Reports cumulative tokens conserved, quota windows extended, and syntax errors intercepted during your active session. |

---

## 🤖 AI Agent Setup

### 1. Claude Code

Add the MCP server to Claude Code:
```bash
claude mcp add inboost-longrun -- inboost-longrun serve
```

Add optimization directives to `.claude/rules/inboost_longrun.md` (or `CLAUDE.md`):
```markdown
# InBoost LongRun Optimization Directives

1. Context Conservation: Before reading large files, use l0_view_outline to inspect declarations and structure.
2. Test Failure Isolation: Filter test logs and runtime exceptions via l0_clean_test_log to eliminate noise and isolate failing lines.
3. Syntax Integrity: Validate all code modifications with l0_verify_syntax prior to finalizing changes.
4. Edit Scope Compliance: Ensure edits remain focused and within budget. Verify with l0_verify_edit_scope.
5. Execution Optimization: Run test commands via l0_run_test for compact results. Check session economy with l0_savings_report.
```

### 2. Google Antigravity (`agy`)

Add the MCP server to Antigravity CLI:
```bash
agy mcp add inboost-longrun inboost-longrun serve
```

Rules are automatically loaded from `.agents/rules/inboost_longrun.md`.

### 3. Cursor

Add `inboost-longrun` to your project's `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "inboost-longrun": {
      "command": "inboost-longrun",
      "args": ["serve"]
    }
  }
}
```

---

## 📦 Supported Platforms

All binaries are standalone, statically compiled or native executables with zero external runtime dependencies:

* **Linux:** `x86_64` & `arm64` (Universal Static ELF, zero libc dependencies, runs on Ubuntu, Debian, Alpine, CentOS, Arch, Docker)
* **macOS:** Apple Silicon (`arm64`, M1–M4) & Intel (`x86_64`) (Native Mach-O)
* **Windows:** `x86_64` (Native Console PE32+)

---

## 🔒 Privacy & Data Security

> **InBoost LongRun executes 100% locally on your machine and never transmits code externally.**

All analysis, verification, and filtering routines run exclusively on your workstation's CPU. The engine makes zero network connections, sends no telemetry, and requires no external API keys.

---

## 🧪 Testing & Verification

Run the automated test suite to verify binary integrity, Ed25519 license validity, and MCP protocol compliance:

```bash
./tests/run_tests.sh
```

Or via pytest:
```bash
pytest tests/ -v
```

---

## ⚖️ Evaluation License Terms

Usage of this distribution is subject to the [INBOOST LONGRUN EVALUATION LICENSE AGREEMENT](LICENSE_EVALUATION.md):
* **Evaluation Purpose Only:** Licensed exclusively for evaluation and non-production testing.
* **Term Limit:** Access is limited to the active evaluation period. Use must cease upon expiration.
* **Disclaimer:** Provided "AS IS" with no warranties; all liability is disclaimed to the maximum extent permitted by law.
* **Public Benchmarks:** Publication of benchmark results requires prior written consent from InBoost.
* **Contact:** For licensing questions or extended enterprise pilots, contact **inbound@inboost.pro**.
