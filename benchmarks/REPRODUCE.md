# SWE-bench Verified ($N=500$) Benchmark Reproduction & Audit Guide

This guide provides complete, step-by-step instructions for auditors, skeptics, and researchers to verify the empirical benchmarks of **Google Antigravity (`agy`)** in **Bare Baseline** mode versus **`agy` + InBoost LongRun** across the full 500-task suite of **SWE-bench Verified**.

---

## 🔍 Verification Levels (Fastest to Deepest)

| Level | Scope | Tokens / Cost | Time | What It Verifies |
| :--- | :--- | :---: | :---: | :--- |
| **Level 0: Instant Offline Audit** | Full $N=500$ (50 cohorts) | **0 tokens ($0.00)** | **< 100 ms** | Parses all 50 on-disk cohorts, checks raw predictions and Docker reports, verifies 0 regressions, and validates exact numbers. |
| **Level 1: Container CI Verification** | 1 Cohort (10 tasks) | **0 tokens ($0.00)** | **~5-10 min** | Executes official SWE-bench Docker containers on saved prediction patches to verify test pass/fail states independently. |
| **Level 2: Live Single-Task A/B Demo** | 1 Task (`requests` or `django`) | **Live API tokens** | **~2 min** | Runs a live end-to-end task comparing Bare vs InBoost LongRun turn-by-turn. |
| **Level 3: Full Cohort Live Generation** | 10 Tasks (1 Cohort) | **Live API tokens** | **~30 min** | Runs `agy` from scratch on 10 tasks, generates diffs, and evaluates in Docker containers. |

---

## ⚡ Level 0: Instant Offline Audit (< 100 ms, 0 Tokens, 0 Dependencies)

Verify all 50 cohorts, all 500 tasks, all token counts, and all Docker reports directly from the raw on-disk artifacts without needing API keys or a running Docker daemon:

```bash
# Run master audit tool (standard Python 3 only)
python3 benchmarks/scripts/audit_swebench_500.py
```

*Or via the reproduction helper:*
```bash
./benchmarks/scripts/reproduce_cohort.sh --audit
```

*For Markdown output matching repository documentation:*
```bash
python3 benchmarks/scripts/audit_swebench_500.py --markdown
```

*For machine-readable JSON output:*
```bash
python3 benchmarks/scripts/audit_swebench_500.py --json
```

*To inspect an individual cohort (e.g. Cohort 01):*
```bash
python3 benchmarks/scripts/audit_swebench_500.py --cohort 1
```

### What Level 0 Audits on Disk:
1. Verifies that all 50 cohort configs (`cohorts/cohort_01.json` ... `cohort_50.json`) contain exactly 10 tasks each with no duplicate instance IDs (500 unique tasks).
2. Verifies that all 50 cohort run directories (`runs/cohort_01/` ... `runs/cohort_50/`) contain valid `comparison.json`, `SCORECARD.md`, and sealed `predictions.jsonl`.
3. Verifies that the candidate patch set in `_bare_agy` and `_inboost_longrun` matches container execution logs in `eval/report.json`.
4. Calculates the mathematical set differences between resolved instance IDs to verify that **zero regressions occurred (Bare Pass $\to$ LongRun Fail = 0)**.

---

## 🐳 Level 1: Container CI Test Verification (0 Tokens, Docker Only)

### Option A: Standalone Docker Verification (Zero pip dependencies)
To verify that the generated patches pass official SWE-bench Verified test suites inside isolated Docker containers without installing heavy Python dependencies:

```bash
# Verify Cohort 01 InBoost LongRun patches in official Docker containers:
python3 benchmarks/scripts/verify_docker.py \
    --predictions benchmarks/runs/cohort_01_inboost_longrun/predictions.jsonl \
    --config benchmarks/cohorts/cohort_01.json \
    --timeout 1200
```

*Or via the shorthand wrapper:*
```bash
./benchmarks/scripts/reproduce_cohort.sh 1 --skip-runs
```

This runner:
1. Spawns official SWE-bench Docker containers (`swebench/sweb.eval.x86_64.<inst_id>:latest`).
2. Applies the candidate unified diff via `git apply`.
3. Runs the targeted `FAIL_TO_PASS` bug reproduction tests.
4. Runs the targeted `PASS_TO_PASS` regression tests.
5. Emits `eval/report.json` and per-instance container execution logs in `eval/test_logs/<instance_id>.eval.log`.

---

### Option B: Official SWE-bench Harness & Leaderboard Bundle (per swebench.com/submit.html)
For external auditors who require running the official `swebench` python package as specified in the official [SWE-bench Submission Guidelines](https://www.swebench.com/submit.html):

```bash
# 1. Export consolidated N=500 prediction bundles and metadata:
python3 benchmarks/scripts/export_swebench_submission.py

# 2. Install official SWE-bench evaluation harness:
pip install swebench

# 3. Execute official SWE-bench evaluation harness across all 500 tasks:
python -m swebench.harness.run_evaluation \
    --dataset_name SWE-bench/SWE-bench_Verified \
    --predictions_path benchmarks/export/inboost_longrun_agy_all_preds.jsonl \
    --max_workers 8 \
    --run_id inboost_longrun_500_eval

# 4. (Optional) Run official evaluation on Bare Baseline predictions:
python -m swebench.harness.run_evaluation \
    --dataset_name SWE-bench/SWE-bench_Verified \
    --predictions_path benchmarks/export/bare_agy_all_preds.jsonl \
    --max_workers 8 \
    --run_id bare_agy_500_eval
```

*Or submit via the official SWE-bench Cloud CLI:*
```bash
sb-cli submit swe-bench_verified test \
    --predictions_path benchmarks/export/inboost_longrun_agy_all_preds.jsonl \
    --run_id inboost_longrun_500_eval
```

---

## 🧪 Level 2: Live Single-Task A/B Evaluation

To run an end-to-end interactive comparison on a single standardized task from SWE-bench Verified (`psf__requests-1724` or `django__django-12774`):

```bash
bash examples/eval_ab.sh
```

This runs:
1. **Arm A (Vanilla Baseline):** Executes the bare agent on the target task.
2. **Arm B (InBoost LongRun):** Executes the agent accelerated by InBoost L0 CPU offload tools (`inboost-local`, `TracebackCrusher`, `AST Guard`).
3. Compares turnaround speed, token consumption, diff size, and test pass rate.

---

## 🚀 Level 3: Live Cohort Benchmark Execution

To execute live LLM inference across an entire 10-task cohort:

```bash
# Run Cohort 01 live with Google Antigravity (agy)
./benchmarks/scripts/reproduce_cohort.sh 1

# Or with custom timeout per task (e.g. 15 minutes)
./benchmarks/scripts/reproduce_cohort.sh 1 --timeout 900
```

*To run in simulation / dry-run mode (validates tool orchestration without burning LLM tokens):*
```bash
./benchmarks/scripts/reproduce_cohort.sh 1 --dry-run
```

---

## 🛡️ Skeptic FAQ & Methodology Verification

### Q1: "How do I know the claims are not cherry-picked?"
**Answer:** The benchmark covers the complete 500-task suite of SWE-bench Verified ($N=500$), partitioned into 50 stratified cohorts. No instances are omitted or excluded. All 500 raw runs and predictions are preserved on disk.

### Q2: "How do I know there are 0 regressions?"
**Answer:** Run `python3 benchmarks/scripts/audit_swebench_500.py`. It computes `regressions = len(b_resolved_ids - lr_resolved_ids)` across every cohort. Across all 500 tasks, every single instance resolved by the bare baseline was also resolved by InBoost LongRun ($0$ regressions).

### Q3: "How does InBoost LongRun achieve +46 net rescued tasks?"
**Answer:**
1. **Empty 0-Byte Diff Elimination:** On the bare baseline, 47 tasks (9.40%) were abandoned because vanilla agents hit context limits or turn limits during exploration loops, yielding 0-byte patches. InBoost LongRun's **Synthesis Ultimatum Guardrail** intercepts turn exhaustion and synthesizes compilable code from edit history (47 rescued from 0 bytes, of which 42 passed all Docker tests).
2. **Syntax Corruption Prevention:** 3 tasks failed on the bare baseline due to corrupt hunk headers or indentation mismatches. InBoost LongRun's **AST Guard** intercepted syntax errors locally, ensuring 0 apply errors.
3. **Traceback Crushing:** Vanilla agents ingest up to 50,000 tokens of raw pytest output per turn. **TracebackCrusher (<15 ms CPU)** strips 95% of framework noise, pinpointing the failing AST lines directly and preventing context thrashing.

### Q4: "Is Docker container execution time mixed into agent speed?"
**Answer:** **No.** In strict compliance with official SWE-bench evaluation methodology (Princeton NLP / ICLR 2024), **Agent Wall-Clock Latency (Time-to-Patch)** is decoupled from **Docker CI Verification Overhead**. Failing agents that emit 0-byte empty diffs exit Docker containers in < 1 second because no tests run. Conversely, working patches run 50-100 regression tests (60-180 seconds). Conflating CI time with agent generation time would artificially penalize agents that write functional code.

### Q5: "How does `verify_docker.py` relate to the official `swebench.harness` package?"
**Answer:** `verify_docker.py` executes **identical container operations** in the **exact same official Docker images** (`swebench/sweb.eval.x86_64.*:latest`), applying the candidate diff and running the official `FAIL_TO_PASS` and `PASS_TO_PASS` suites. It exists so that developers and CI runners can verify results instantly without configuring heavy Hugging Face datasets or GitPython dependencies. Furthermore, running `python3 benchmarks/scripts/export_swebench_submission.py` outputs standard `all_preds.jsonl` files that can be fed directly to `python -m swebench.harness.run_evaluation` or submitted to the official leaderboard via PR to `SWE-bench/experiments` as specified on [https://www.swebench.com/submit.html](https://www.swebench.com/submit.html).
