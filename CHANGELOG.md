# Changelog

All notable changes to the InBoost LongRun Evaluation Runtime will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.4.0] - 2026-10-25

### Added
- **Complete SWE-bench Verified N=500 Benchmark Milestone**:
  - Reached **90.20% Pass@1 (451 / 500 tasks resolved)** under official SWE-bench Verified Docker evaluation (50 cohorts x 10 tasks) with Google Antigravity (`agy`, Gemini 3.8 Flash High, `--effort low`).
  - Achieved **+9.40% absolute (+11.63% relative)** improvement over Google Antigravity Bare Baseline (**80.80%**, 404 / 500 resolved), rescuing **+47 net tasks**.
  - **100% Elimination of 0-Byte Surrender Diffs**: Reduced agent surrender from 9.40% (47 / 500) to **0.00% (0 / 500)** via Synthesis Ultimatum guardrails.
  - **Zero Regressions**: 0 tasks regressed from Bare Pass to LongRun Fail across all 500 tasks.
- **Turnkey Benchmark Reproducibility & Auditing Tools**:
  - Added `benchmarks/scripts/reproduce_cohort.sh`: Single-command turnkey runner for any cohort (1 to 50) with automatic preflight environment validation, parallel execution, and Docker evaluation.
  - Added `benchmarks/scripts/audit_swebench_500.py`: Instant offline verification tool (<100ms, 0 LLM tokens, 0 Docker containers) performing cross-cohort audit of all 500 predictions, syntax checks, patch lengths, and Docker resolution parity.
  - Added `benchmarks/scripts/export_swebench_submission.py`: Generates official submission bundle (`inboost_longrun_agy_all_preds.jsonl`, `bare_agy_all_preds.jsonl`, and metadata YAMLs) adhering to SWE-bench submission standards (`swebench.com/submit.html`).

### Changed
- **Flat Enterprise Seat Subscription Economics**:
  - Replaced legacy per-ticket synthetic token cost estimations (`MODEL_PRICING`) across all evaluation tools, comparisons, and documentation with flat enterprise seat subscription licensing ($150/developer/month).
  - Emphasized core hardware economics: 100% local CPU execution (<15ms, <50MB RAM) requiring **$0.00 GPU CAPEX**.
- **Benchmark Suite Pruning & Hardening**:
  - Pruned 8 legacy and flaky scripts from `benchmarks/scripts/` (`rerun_flaky_9.py`, `rerun_bare_flaky_9.py`, `sample_random_cohort25.py`, `plan_all_500_cohorts.py`, `pull_all_missing.py`, `capture_agy_telemetry_cohorts.py`, `cohort_manager.py`, `check_exact_task_count.py`).
  - Retained exactly 10 robust, verified evaluation tools and updated documentation in `benchmarks/README.md`.
- **Test Suite Robustness**:
  - Hardened `tests/run_tests.sh` to enforce execution permissions on local binary wrappers across all host configurations.
  - Updated `tests/test_agent_integrations.py` to decouple agent connectivity testing from host-specific ambient user configurations.

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
