# SWE-bench Verified Full Benchmark Report ($N=500$): Bare vs InBoost LongRun

[![SWE-bench Verified](https://img.shields.io/badge/SWE--bench-Verified%20(N=500)-blue.svg)](https://www.swebench.com/)
[![Resolve Rate](https://img.shields.io/badge/Resolve%20Rate-90.20%25%20vs%2080.80%25-brightgreen.svg)](#1-executive-summary--key-findings)
[![Empty Diffs Eliminated](https://img.shields.io/badge/Empty%20Diffs-0%20(0.00%25)-brightgreen.svg)](#1-executive-summary--key-findings)
[![Context Reduction](https://img.shields.io/badge/Context%20Bloat--61.9%25-brightgreen.svg)](#1-executive-summary--key-findings)
[![Zero Regressions](https://img.shields.io/badge/Regressions-0%20(0.0%25)-brightgreen.svg)](#1-executive-summary--key-findings)
[![Verification Engine](https://img.shields.io/badge/Verification-Official%20Docker%20Harness%20v5.0.2-orange.svg)](#4-docker-verification-methodology--metric-isolation)

---

## 1. Executive Summary & Key Findings

> [!IMPORTANT]
> **Key Conclusion:** Across the entire 500-task suite of **SWE-bench Verified** (50 stratified cohorts $\times$ 10 tasks = $N=500$), accelerating **Google Antigravity (`agy`)** with **InBoost LongRun** breaks the 90% resolution barrier, achieving **90.20% Pass@1 (451 / 500 tasks resolved)** versus **80.80% (404 / 500 tasks)** on the bare baseline.
>
> InBoost LongRun delivers **+47 net rescued tasks (+9.40% absolute gain, +11.63% relative improvement)**, **completely eliminates 0-byte surrender failures (from 47 down to 0)**, achieves **zero regressions across all 500 tasks**, cuts session token context load by **-61.9% (2.63x context runway)**, saves **5.2 hours of agent latency (-34.9%)**, and operates under a predictable flat subscription model with zero host CAPEX ($0.00).

### Official 500-Task Master Scorecard

| Metric / KPI | Google Antigravity Bare Baseline | `agy` + InBoost LongRun Accelerated | Official Impact Delta |
| :--- | :---: | :---: | :---: |
| **Total Benchmark Tasks** | **500** (50 cohorts $\times$ 10) | **500** (50 cohorts $\times$ 10) | **Full $N=500$ Coverage** |
| **Docker Resolve Rate (Pass@1)** | `80.80%` (404 / 500) | **`90.20%` (451 / 500)** 🏆 | **🟢 +9.40% absolute (+47 tasks net)** |
| **Empty Patch Surrenders (0 bytes)** | `9.40%` (47 / 500) | **`0.00%` (0 / 500)** | **🛡️ 100% elimination (47 rescued)** |
| **Patch Apply Errors (Syntax/Hunk)** | `0.60%` (3 / 500) | **`0.00%` (0 / 500)** | **100% syntax validity via AST Guard** |
| **Unresolved Container Tests** | `9.20%` (46 / 500) | **`9.80%` (49 / 500)*** | **All 47 surrendered tasks evaluated** |
| **Regressions (Bare Pass $\to$ LR Fail)**| — | **0 tasks (0.0%)** | **0 regressions across 500 tasks** |
| **Context Token Reduction** | 1.0x (10,414,523) | **0.381x (3,966,438, -61.9%)** | **⚡ 2.63x lower context load** |
| **Coding Session Rate-Limit Runway** | 1.0x (Baseline) | **2.63x** | **2.63x longer before 429 limits** |
| **Agent Wall-Clock Latency** | 53,943.2s | **35,113.3s (-34.9%)** | **⏱️ 5.2 hours saved** |
| **Host Infrastructure CAPEX** | `$0.00` | **`$0.00`** | **100% Local CPU (<15 ms, <50MB RAM)** |

*\*Note on unresolved test count:* InBoost LongRun forced all 47 instances abandoned with empty patches by the bare baseline into full code synthesis and verification in Docker. Of those 47 rescued tasks, 42 passed all tests, while 5 failed functional assertions, raising evaluated test attempts.

---

## 2. Repository Distribution & Impact Breakdown ($N=500$)

The 500 tasks in SWE-bench Verified span 12 major Python ecosystems. InBoost LongRun demonstrated positive net rescue across repositories without a single regression:

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

## 3. Failure Taxonomy & Root-Cause Elimination

```
BARE BASELINE FAILURE MODES ($N=500$):
404 Resolved (80.8%) ──┬── 47 Empty 0-byte Surrenders (9.4%) ── [Context bloat & turn exhaustion]
                       ├── 3 Corrupted Diffs / Apply Errors (0.6%) ── [AST offset drift]
                       └── 46 Unresolved Docker Tests (9.2%)

INBOOST LONGRUN RESCUE PIPELINE:
451 Resolved (90.2%) ──┬── 0 Empty Patches (0.0%) ── [Synthesis Ultimatum enforces compilable patch]
                       ├── 0 Apply Errors (0.0%) ── [AST Guard validates diff syntax on CPU]
                       └── 49 Unresolved Docker Tests (9.8%)
```

### Key Failure Drivers Addressed:
1. **0-Byte Empty Diffs (Context Exhaustion):**  
   Vanilla agents stall in repetitive exploration loops or dump thousands of lines of raw test framework logs into prompt context. Once hourly rate limits or turn limits approach, the agent gives up without emitting code edits.  
   *InBoost Fix:* **Synthesis Ultimatum Guardrails** intercept turn budget exhaustion and force the agent into structured patch synthesis from its edit history.
2. **Apply Errors (Patch Corruption):**  
   Vanilla agents frequently miss context indentation or corrupt hunk headers in unified diffs.  
   *InBoost Fix:* **AST Guard** validates syntax trees and validates unified diff offsets locally prior to patch emission.
3. **Traceback Context Pollution:**  
   Raw pytest stack traces consume up to 50,000 tokens per turn.  
   *InBoost Fix:* **TracebackCrusher (<15 ms CPU)** strips 95% of noise on the host CPU, pinpointing the failing AST lines directly.

---

## 4. Docker Verification Methodology & Metric Isolation

All 500 instances were scored in the official **SWE-bench Docker v5.0.2 evaluation harness**:

1. **Decoupled Metric Accounting:** In strict accordance with the SWE-bench evaluation standard (Princeton NLP / ICLR 2024), **Agent Wall-Clock Latency (Time-to-Patch)** is decoupled from **Docker CI Verification Overhead**. Failing agents that surrender with 0-byte patches exit Docker containers in <1s, whereas passing agents run hundreds of regression tests. Decoupling eliminates artificial speed penalties on successful runs.
2. **Dual-Condition Verification:** A task is marked `RESOLVED` only if:
   - All `FAIL_TO_PASS` bug reproduction tests pass (`PASS`).
   - All `PASS_TO_PASS` existing regression tests remain green (0 regressions).
   - The diff compiles cleanly with zero syntax errors.
3. **Artifact Retention Policy:** Every run preserves candidate patches (`predictions.jsonl`), crushed telemetry logs, and raw container evaluation outputs (`eval/test_logs/<instance_id>.eval.log`).

---

## 5. Cohort Registry & Verification Data Structure

The benchmark suite is partitioned into 50 stratified cohorts of 10 tasks each, ensuring balanced repository and difficulty representation:

* **Master Cohort Registry:** [`cohorts/manifest.json`](cohorts/manifest.json) (50 cohorts, 500 tasks, 78 cached Docker images).
* **Cohort Configs:** [`cohorts/cohort_01.json`](cohorts/cohort_01.json) through [`cohorts/cohort_50.json`](cohorts/cohort_50.json).
* **Execution Runs & Docker Test Logs:** [`runs/cohort_01/`](runs/cohort_01/) through [`runs/cohort_50/`](runs/cohort_50/) (each containing `comparison.json`, `SCORECARD.md`, and `eval/report.json`).
* **Complete Task Dataset:** [`cohorts/swebench_verified_500_all_cohorts.json`](cohorts/swebench_verified_500_all_cohorts.json) (all 500 instances with task descriptors, base commits, problem statements, and test patches).
* **Official Leaderboard Submission Bundle:** [`export/`](export/) (consolidated `all_preds.jsonl` and `metadata.yaml`).
* **Detailed Audit & Reproduction Guide:** [`REPRODUCE.md`](REPRODUCE.md).

---

## 6. How to Reproduce & Audit (< 100 ms)

You can audit the entire dataset offline, inspect pre-computed telemetry, or execute end-to-end Docker verification:

```bash
# 1. Instant offline audit across all 50 cohorts (< 100 ms, 0 tokens):
python3 benchmarks/scripts/audit_swebench_500.py

# 2. Shorthand helper for cohort reproduction & audit:
./benchmarks/scripts/reproduce_cohort.sh --audit

# 3. Re-verify Docker tests on existing predictions for Cohort 01 (0 tokens):
./benchmarks/scripts/reproduce_cohort.sh 1 --skip-runs

# 4. Run turnkey A/B evaluation on a single representative live task:
bash examples/eval_ab.sh

# 5. Run official evaluation via SWE-bench harness:
python -m swebench.harness.run_evaluation \
    --dataset_name SWE-bench/SWE-bench_Verified \
    --predictions_path benchmarks/export/inboost_longrun_agy_all_preds.jsonl \
    --max_workers 8 \
    --run_id inboost_longrun_500_eval
```

👉 **[Read the Full Reproduction & Auditor Verification Guide (REPRODUCE.md) →](REPRODUCE.md)**

---

*Official evaluation conducted under strict Zero-Hallucination Policy with Docker v5.0.2 container isolation. Documentation and scorecards published under the [InBoost LongRun Evaluation License](LICENSE).*
