# SWE-bench Verified ($N=500$) Master Evaluation Scorecard

**Target Architecture:** Google Antigravity (`agy`) Bare Baseline vs `agy` + InBoost LongRun Accelerated  
**Benchmark Suite:** SWE-bench Verified (50 Stratified Cohorts $\times$ 10 Tasks = $N=500$ Tasks)  
**Evaluation Standard:** Official Docker Test Verification (`FAIL_TO_PASS` + `PASS_TO_PASS`, Docker v5.0.2)  
**Data Integrity:** Verified Run Artifacts & Container Logs (Zero Hallucination Policy)

---

## 1. Executive Summary & Master KPI Deltas ($N=500$)

> [!IMPORTANT]
> **Key Finding:** InBoost LongRun elevates Google Antigravity (`agy`) across the full 500-task suite of SWE-bench Verified to **90.20% Pass@1 (451 / 500 tasks resolved)** versus **80.80% (404 / 500)** on the bare baseline. It completely eliminates empty-patch surrender failures (**0.00% vs 9.40%**), records **zero regressions across all 500 tasks**, cuts session token context load by **-61.9% (2.63x lower token load)**, saves **5.2 hours of latency (-34.9%)**, and operates under a predictable flat subscription model with zero host CAPEX ($0.00).

| Metric / KPI | Google Antigravity Bare Baseline | `agy` + InBoost LongRun | Official Impact Delta |
| :--- | :---: | :---: | :---: |
| **Total Benchmark Tasks** | **500** (50 cohorts $\times$ 10) | **500** (50 cohorts $\times$ 10) | **Full $N=500$ Coverage** |
| **Docker Resolve Rate (Pass@1)** | `80.80%` (404 / 500) | **`90.20%` (451 / 500)** 🏆 | **🟢 +9.40% absolute (+47 tasks net)** |
| **Empty Patch Surrenders (0 bytes)** | `9.40%` (47 / 500) | **`0.00%` (0 / 500)** | **🛡️ 100% elimination (47 rescued)** |
| **Patch Apply Errors (Syntax/Hunk)** | `0.60%` (3 / 500) | **`0.00%` (0 / 500)** | **100% valid syntax via AST Guard** |
| **Unresolved Container Tests** | `9.20%` (46 / 500) | **`9.80%` (49 / 500)*** | **All 47 surrendered tasks evaluated** |
| **Regressions (Bare Pass $\to$ LR Fail)**| — | **0 tasks (0.0%)** | **0 regressions across 500 tasks** |
| **Context Token Reduction** | 1.0x (10,414,523) | **0.381x (3,966,438, -61.9%)** | **⚡ 2.63x lower context load** |
| **Coding Session Rate-Limit Runway** | 1.0x (Baseline) | **2.63x** | **2.63x longer before 429 limits** |
| **Agent Wall-Clock Latency** | 53,943.2s | **35,113.3s (-34.9%)** | **⏱️ 5.2 hours saved** |
| **Host Infrastructure CAPEX** | `$0.00` | **`$0.00`** | **100% Local CPU (<15 ms, <50MB RAM)** |

*\*Note on unresolved test count:* InBoost LongRun forced all 47 instances abandoned with empty patches by the bare baseline into full code synthesis and verification in Docker. Of those 47 rescued tasks, 42 passed all tests, while 5 failed functional assertions, raising evaluated test attempts.

---

## 2. Repository Distribution Breakdown ($N=500$)

| Library / Repository Ecosystem | Total Benchmark Tasks | Bare `agy` Resolved | InBoost LongRun Resolved | Net Rescued Tasks | Regressions |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`django/django`** | 231 | 153 (66.2%) | **196 (84.8%)** | **+43 tasks net** | 0 (0.0%) |
| **`sympy/sympy`** | 75 | 73 (97.3%) | **74 (98.7%)** | **+1 tasks net** | 0 (0.0%) |
| **`sphinx-doc/sphinx`** | 44 | 39 (88.6%) | **39 (88.6%)** | 0 tasks | 0 (0.0%) |
| **`matplotlib/matplotlib`** | 34 | 33 (97.1%) | **34 (100.0%)** | **+1 tasks net** | 0 (0.0%) |
| **`scikit-learn/scikit-learn`** | 32 | 31 (96.9%) | **31 (96.9%)** | 0 tasks | 0 (0.0%) |
| **`astropy/astropy`** | 22 | 21 (95.5%) | **21 (95.5%)** | 0 tasks | 0 (0.0%) |
| **`pydata/xarray`** | 22 | 22 (100.0%) | **22 (100.0%)** | 0 tasks | 0 (0.0%) |
| **`pytest-dev/pytest`** | 19 | 17 (89.5%) | **17 (89.5%)** | 0 tasks | 0 (0.0%) |
| **`pylint-dev/pylint`** | 10 | 7 (70.0%) | **8 (80.0%)** | **+1 tasks net** | 0 (0.0%) |
| **`psf/requests`** | 8 | 6 (75.0%) | **7 (87.5%)** | **+1 tasks net** | 0 (0.0%) |
| **`mwaskom/seaborn`** | 2 | 1 (50.0%) | **1 (50.0%)** | 0 tasks | 0 (0.0%) |
| **`pallets/flask`** | 1 | 1 (100.0%) | **1 (100.0%)** | 0 tasks | 0 (0.0%) |
| **TOTAL** | **500** | **404 (80.80%)** | **451 (90.20%)** | **+47 tasks net** | **0 (0.0%)** |

---

## 3. Why Bare Agents Fail vs How InBoost LongRun Rescues Them

```
BARE (VANILLA FAILURE MODE):
404 Resolved (80.8%) ──┬── 47 Empty 0-byte Surrenders (9.4%) ── [Context bloat & turn exhaustion]
                       ├── 3 Corrupted Diffs / Apply Errors (0.6%) ── [AST offset drift]
                       └── 46 Unresolved Docker Tests (9.2%)

INBOOST LONGRUN RESCUE PIPELINE:
451 Resolved (90.2%) ──┬── 0 Empty Patches (0.0%) ── [Synthesis Ultimatum enforces compilable patch]
                       ├── 0 Apply Errors (0.0%) ── [AST Guard validates diff syntax on CPU]
                       └── 49 Unresolved Docker Tests (9.8%)
```

### Mechanisms of Action:
1. **TracebackCrusher (L0 Host CPU):** Filters 95% of pytest, unittest, and vitest log noise in <15 ms, preventing context exhaustion.
2. **AST Symbol Pinpointing:** Pinpoints exact function and class coordinates so the agent never scans entire source trees blindly.
3. **Synthesis Ultimatum Guardrail:** Forbids empty diff generation on closing steps, enforcing compilable patch emission.
4. **Pre-Commit AST Validator:** Prevents syntax errors and malformed hunk headers from corrupting output patches.

---

## 4. Evaluation Methodology & Metric Isolation (SWE-bench Standard)

> [!NOTE]
> **Decoupled Metric Accounting:** In strict accordance with the official SWE-bench evaluation methodology (Princeton NLP / ICLR 2024), **Agent Wall-Clock Latency (Time-to-Patch)** is decoupled from **Docker CI Verification Overhead**:
> 1. **User-Perceived Speed:** In production IDEs (Claude Code, Cursor, `agy`), the developer waits for the agent to emit a functional unified diff. CI test suites run asynchronously post-commit.
> 2. **Selection Bias Prevention:** Empty 0-byte patches skip test execution in <1s, whereas passing patches execute 100+ tests in 60-180s. Blending CI verification duration into agent turnaround time would penalize agents that produce working code.

---

## 5. Artifact Verification & Reproducibility Links

* **Audit & Reproducibility Guide:** [`REPRODUCE.md`](REPRODUCE.md)
* **Instant Offline Audit Script:** [`scripts/audit_swebench_500.py`](scripts/audit_swebench_500.py)
* **Leaderboard Submission Bundle:** [`export/`](export/) (contains consolidated `all_preds.jsonl` and `metadata.yaml`)
* **Master Cohort Registry:** [`cohorts/manifest.json`](cohorts/manifest.json)
* **All 500 Tasks Dataset:** [`cohorts/swebench_verified_500_all_cohorts.json`](cohorts/swebench_verified_500_all_cohorts.json)
* **Per-Cohort Telemetry & Scorecards:** [`runs/cohort_01/`](runs/cohort_01/) through [`runs/cohort_50/`](runs/cohort_50/)
* **Turnkey Single-Task Evaluation:** [`examples/eval_ab.sh`](../examples/eval_ab.sh)
