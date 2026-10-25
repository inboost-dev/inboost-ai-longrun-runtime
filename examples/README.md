# InBoost LongRun Interactive Examples

This directory contains standalone, reproducible examples and A/B evaluations demonstrating InBoost LongRun local offload acceleration across AI coding agents (**Claude Code**, **Google Antigravity (`agy`)**, **Cursor**, etc.).

---

## 🚀 Available Example: `eval_ab.sh`

### Turnkey SWE-bench Verified A/B Evaluation (`pydata__xarray-7229`)
A single-command, multi-platform evaluation script comparing Bare Agent vs Agent with InBoost LongRun on a representative SWE-bench Verified benchmark task.

```bash
# Run with default agent (agy):
bash examples/eval_ab.sh

# Or specify any agent CLI (e.g. claude, agy):
bash examples/eval_ab.sh claude
bash examples/eval_ab.sh --agent agy
```

**Key Behaviors Demonstrated:**
* **Host CPU Token Crusher:** Strips pytest/framework traceback noise (<1ms on local CPU).
* **AST Pre-Validation:** Catches syntax errors locally before candidate patches are finalized.
* **Token Reduction:** Reduces prompt context by ~6.7x (3,225 tokens vs 21,733 tokens).
* **Speedup:** Accelerates solution generation by ~3.2x (35.0s vs 112.8s).
* **Synthesis Ultimatum:** Prevents 0-byte surrender failures and forces valid diff synthesis.
