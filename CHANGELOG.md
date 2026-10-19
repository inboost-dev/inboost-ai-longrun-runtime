# Changelog

All notable changes to the InBoost LongRun Evaluation Runtime will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] - 2026-10-19

### Added
- **Pre-Flight System Dependency Diagnostics (`doctor` / `check`)**:
  - Automated pre-flight validation of essential offload utilities (`find`, `grep`, `diff`, `patch`, `git`, `python3`).
  - Native package manager installation hints for missing tools across macOS (`brew`), Debian/Ubuntu (`apt`), RHEL/Fedora (`dnf`), Alpine (`apk`), Arch Linux (`pacman`), openSUSE (`zypper`), and Windows (`winget install --id Git.Git`).
  - Non-blocking discovery of AI Coding Agents (`Claude Code`, `Google Antigravity`, `Cursor`, `VS Code`).
  - Support for `INBOOST_IGNORE_MISSING_DEPS=1` bypass flag.
- **Claude Code 2.1.x & Google Antigravity Certification**:
  - Full compatibility and integration testing with **Claude Code 2.1.296** via MCP (`claude mcp add -s user inboost-longrun -- inboost-longrun serve`).
  - Full compatibility and integration testing with **Google Antigravity (`agy` 1.4.2)**.
  - Added dedicated integration test suite `tests/test_agent_integrations.py` validating MCP handshake, tool discovery, and runtime execution.
- **L0 Local AST Syntax Verification (`l0_verify_syntax`)**:
  - Pre-save Python AST validation (`ast.parse`) running entirely on local CPU (<1ms).
  - Intercepts syntax errors, unclosed delimiters, and broken indentation before files are saved or passed to Docker test runners.
- **Traceback Noise Elimination (`l0_clean_test_log`)**:
  - Crushes verbose test framework outputs (-90% prompt noise) while isolating root cause assertions and failing AST lines.
- **Benchmark Scaling & Docker Verification**:
  - Scaled uniform stratified SWE-bench Verified benchmark runner up to 300 tasks (Cohorts 1–30).
  - Full parity evaluation under isolated official SWE-bench Docker containers.

### Changed
- Bumped runtime version to `0.3.0` across npm (`inboost-longrun`, `inboost-ai-longrun`), PyPI (`inboost-longrun`, `inboost-ai-longrun`), and standalone distribution binaries.
- Updated installation scripts (`install.sh`, `install.ps1`) with hardened dependency verification and automatic `PATH` persistence.

### Security & Privacy
- **100% Local CPU Execution**: All outline inspection, syntax parsing, and trace filtering routines run on local CPU without external network transmission.
- **Zero Secret Exposure**: Automatic sanitization of credentials, sensitive tokens, and proprietary paths.

---

## [0.2.1] - 2026-10-18

### Added
- Initial public evaluation release of InBoost LongRun multi-platform runtime.
- Multi-architecture binary distribution for Linux (x86_64, ARM64), macOS (Apple Silicon, Intel), and Windows.
- Standard 6-tool Model Context Protocol (MCP) server interface (`l0_view_outline`, `l0_clean_test_log`, `l0_verify_syntax`, `l0_verify_edit_scope`, `l0_run_test`, `l0_savings_report`).
- Support for Claude Code and Cursor IDE rules injection (`inboost-longrun init`).
