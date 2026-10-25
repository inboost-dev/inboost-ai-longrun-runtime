# Benchmark Publication Guidelines & Standards
## InBoost LongRun Evaluation Runtime (`inboost-longrun`)

> **Status:** Official verification standards and publication rules for empirical benchmarks  
> **Scope:** Repository `inboost-ai-longrun`, SWE-bench reports, documentation, and external releases  
> **Official Domain:** `https://inboost.pro` • **License:** [InBoost LongRun Evaluation License](LICENSE)

---

## 1. Zero Hallucination Policy

All performance and reliability metrics published for **InBoost LongRun** must adhere to rigorous empirical testing standards:

1. **No Synthetic Projections:** Extrapolated, modeled, or projected results are strictly prohibited without direct Docker CI test logs.
2. **Docker Reproducibility:** Every claimed metric must be reproducible in the official evaluation harness (`swebench.harness` $\ge 5.0.2$).
3. **Primary Artifact Retention:** Every scored run must retain:
   - Candidate model diffs (`model_patch.diff`);
   - Intercepted and crushed logs from `TracebackCrusher`;
   - Complete verification container output (`docker_eval.log`) with isolated `FAIL_TO_PASS` and `PASS_TO_PASS` breakdowns.

---

## 2. Decoupled Metric Accounting

In adherence to the SWE-bench evaluation methodology (Princeton NLP / ICLR 2024), agent generation time and test harness execution time are strictly decoupled:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   PHASE 1: AGENT WALL-CLOCK LATENCY                    │
│               Agent Wall-Clock Latency (Time-to-Patch)                 │
│  • Time from prompt receipt until final candidate patch generation     │
│  • Includes LLM token generation and InBoost LongRun Host acceleration │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   PHASE 2: DOCKER CI VERIFICATION                      │
│                  Docker CI Overhead (Test Execution)                   │
│  • Container provisioning, environment setup, and test suite execution │
│  • Completely decoupled from agent generation speed                    │
└────────────────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Selection Bias Prevention:**  
> Failing agents that surrender with an empty diff (0 bytes) exit Docker containers in < 1 second because no tests run. Conversely, agents with working code trigger extensive regression suites (30 to 90 seconds).  
> **Invariant:** Agent generation speed (`Time-to-Patch`) is evaluated strictly prior to launching the verification container.

---

## 3. Benchmark Resolution Criteria

A benchmark task is classified as **`RESOLVED`** only when all conditions are met simultaneously:

1. **`FAIL_TO_PASS`:** All targeted bug reproduction tests transition to `PASSED`.
2. **`PASS_TO_PASS`:** Pre-existing regression tests remain green (0 regressions).
3. **Non-Zero Diff Size:** Patches of 0 bytes are classified as **`UNRESOLVED`** (Empty Patch Failure).
4. **AST Syntax Integrity:** The diff applies cleanly via `git apply` and compiles cleanly in the target language AST parser without `SyntaxError`.
5. **Churn Budget:** Diff churn must not exceed the ceiling limit ($\le 180$ lines).

---

## 4. Officially Verified Baselines

Public releases and technical papers must cite the following verified baselines:

### Baseline 1. Full SWE-bench Verified ($N=500$, Google Antigravity / Gemini Engine)
* **Scope:** Full 500-task suite of SWE-bench Verified (50 cohorts $\times$ 10 tasks).
* **Environment:** `Google Antigravity (agy)` (DeepMind runtime with `gemini-3.8-flash-high` and `gemini-4-argon`, `--effort low`) + `InBoost LongRun L0 Offload Engine`.
* **Baseline:** Google Antigravity (`agy`) Bare Baseline (same engine and effort level).
* **Independent Audit Tool:** `python3 benchmarks/scripts/audit_swebench_500.py` (see [Reproducibility Guide](benchmarks/REPRODUCE.md)).

| Metric | Vanilla `agy` Baseline | `agy` + InBoost LongRun | Official Delta |
| :--- | :---: | :---: | :---: |
| **Pass@1 Resolve Rate** | `80.80%` (404 / 500) | **`90.20%` (451 / 500)** | **🟢 +9.40% absolute (+47 rescued tasks net)** |
| **Empty Patches (0 bytes)** | `9.40%` (47 / 500) | **`0.00%` (0 / 500)** | **🛡️ 100% elimination of 0-byte surrender (47 rescued)** |
| **Patch Apply Errors** | `0.60%` (3 / 500) | **`0.00%` (0 / 500)** | **100% valid syntax via AST Guard** |
| **Regressions (Bare Pass $\to$ LR Fail)** | — | **0 tasks (0.0%)** | **0 regressions across all 500 tasks** |
| **Agent Wall-Clock Latency** | 53,943.2s | **35,113.3s (-34.9%)** | **⏱️ 5.2 hours saved** |
| **Session Token Reduction** | 1.0x (Baseline) | **-61.9% tokens** | **⚡ 2.63x lower context load** |

---

### Baseline 2. Ecosystem & Repository Breakdown ($N=500$)
* **Distribution:** Comprehensive evaluation across 12 major Python ecosystems in SWE-bench Verified.

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

## 5. 100% Local Privacy Guarantee

All offload algorithms in InBoost LongRun operate under strict local execution guarantees:

> *"InBoost LongRun executes 100% locally on the developer workstation CPU. Proprietary source code, configuration files, test suites, and git patches are never transmitted to external InBoost servers."*

All tools (`TracebackCrusher`, `l0_clean_test_log`, `l0_view_outline`, `l0_verify_syntax`) require $< 50$ MB RAM with response times $< 15$ ms.

---

## 6. Reproducible Benchmark Execution Protocol

```bash
# 1. Verify environment readiness and license
inboost-longrun doctor

# 2. Run benchmark cohort execution (e.g. Cohort 01)
python3 benchmarks/scripts/run_cohort.py 1

# 3. Verify candidate patches in official SWE-bench Docker harness
python3 benchmarks/scripts/verify_docker.py \
  --predictions benchmarks/export/inboost_longrun_agy_all_preds.jsonl
```

---

## 7. Pre-Release Publication Checklist

- [ ] Results obtained on reproducible task sets and recorded in `benchmarks/runs/`.
- [ ] Pure agent latency (`Time-to-Patch`) is isolated from Docker testing time.
- [ ] Task resolution counts verified via strict `FAIL_TO_PASS` + `PASS_TO_PASS` assertions.
- [ ] Patches confirmed free of syntax errors and empty diffs.
- [ ] Local privacy preserved: zero API keys or private credentials present in logs.
- [ ] Commits formatted per Conventional Commits and signed off (`git commit -s`).
- [ ] All documentation, code comments, and READMEs strictly in professional English.
