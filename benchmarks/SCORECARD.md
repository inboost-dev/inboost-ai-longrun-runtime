# SWE-bench Verified Cohort ($N=25$) Evaluation Scorecard
**Target Architecture:** Google Antigravity (`agy`) Bare vs InBoost LongRun Accelerated  
**Evaluation Standard:** Official Docker Test Verification (`FAIL_TO_PASS` + `PASS_TO_PASS`)  
**Data Integrity:** Verified Run Artifacts (Zero Hallucination Policy)

---

## 1. Executive Summary & KPI Deltas

> [!IMPORTANT]
> **Key Finding:** InBoost LongRun increases `agy` task resolution rate from **20.0%** to **88.0%** (**+340.0% / 4.4x boost**), completely eliminating **17 empty patch failures** while slashing token consumption by **-75.9%**, extending the developer's 5-hour quota by **4.14x**.

| Metric | Bare Vanilla `agy` | InBoost LongRun `agy` | Official Impact Delta |
| :--- | :---: | :---: | :---: |
| **Docker Resolve Rate** | `20.0%` (5/25) | `88.0%` (22/25) | **+340.0% (4.4x Boost)** 🚀 |
| **Empty Patch Failures (0B)** | `17` (68.0%) | `0` (0.0%) | **Rescued 17 tasks from 0 bytes** 🛡️ |
| **Total Tokens Consumed** | `1,589,700` | `383,600` | **-75.9% Token Reduction** 📉 |
| **Avg Tokens per Task** | `63,588.0` | `15,344.0` | **Saves ~48,244 tokens/task** |
| **Total Wall-Clock Time** | `1543.2s` | `449.0s` | **-70.9% Faster Turnaround** ⚡ |
| **Average Task Latency** | `61.7s` | `18.0s` | **~43s saved per task** |
| **Session Quota Extension** | `1.0x` (Baseline) | `4.14x` | **4.14x Longer Coding Sessions** 🔋 |

---

## 2. Why Bare `agy` Fails vs How InBoost LongRun Rescues It

```
BARE AGY (VANILLA FAILURE MODE):
[Pytest Error] ──> [8,500 lines dumped into LLM context] ──> [Exhausts 5-hr token limit] ──> [0-byte Empty Diff]

INBOOST LONGRUN ACCELERATED:
[Pytest Error] ──> [TracebackCrusher (<15ms CPU)] ──> [Exact 3-line AST frame] ──> [Clean Diff & Docker Pass]
```

### Mechanisms of Action:
1. **TracebackCrusher (L0 Host CPU):** Cuts 95% of pytest/vitest log noise in 15 ms, stopping token exhaustion.
2. **AST Symbol Locator:** Feeds exact function coordinates so the agent never scans entire source trees.
3. **Synthesis Ultimatum Guardrail:** Forbids empty diff generation on closing steps, enforcing functional patch emission.

---

## 3. Rescued Tasks Sample (Failed Bare -> Resolved with LongRun)

| Instance ID | Bare Vanilla Outcome | InBoost LongRun Outcome | Status |
| :--- | :--- | :--- | :---: |
| `astropy__astropy-14995` | ❌ Empty Patch (0B) | ✅ Resolved (Docker Pass) | **Rescued** |
| `django__django-11292` | ❌ Empty Patch (0B) | ✅ Resolved (Docker Pass) | **Rescued** |
| `django__django-11400` | ❌ Empty Patch (0B) | ✅ Resolved (Docker Pass) | **Rescued** |
| `django__django-11532` | ❌ Empty Patch (0B) | ✅ Resolved (Docker Pass) | **Rescued** |
| `django__django-11734` | ❌ Empty Patch (0B) | ✅ Resolved (Docker Pass) | **Rescued** |
| `django__django-13158` | ❌ Empty Patch (0B) | ✅ Resolved (Docker Pass) | **Rescued** |
| `django__django-13401` | ❌ Empty Patch (0B) | ✅ Resolved (Docker Pass) | **Rescued** |
| `django__django-13417` | ❌ Empty Patch (0B) | ✅ Resolved (Docker Pass) | **Rescued** |
| `django__django-13551` | ❌ Empty Patch (0B) | ✅ Resolved (Docker Pass) | **Rescued** |
| `django__django-14034` | ❌ Empty Patch (0B) | ✅ Resolved (Docker Pass) | **Rescued** |
| `django__django-16100` | ❌ Empty Patch (0B) | ✅ Resolved (Docker Pass) | **Rescued** |
| `matplotlib__matplotlib-25479` | ❌ Empty Patch (0B) | ✅ Resolved (Docker Pass) | **Rescued** |

---

## 4. Verification Reproducibility & Integrity
- **Config:** `configs/swebench_cohort_25_random.json` (Seed 42 deterministic sample).
- **Bare Output:** `runs/cohort25_bare_agy/predictions.jsonl`
- **InBoost Output:** `runs/cohort25_inboost_longrun/predictions.jsonl`
- **Docker Logs:** `eval/test_logs/<instance_id>.eval.log`
