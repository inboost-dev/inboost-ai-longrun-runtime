# Official SWE-bench Verified Submission Bundle (N=500)

This directory contains consolidated prediction files formatted for the official **SWE-bench evaluation harness** and leaderboard submissions (per [https://www.swebench.com/submit.html](https://www.swebench.com/submit.html)).

## 📦 Files

- `inboost_longrun_agy_all_preds.jsonl`: Full 500-task predictions for `Google Antigravity (agy)` + InBoost LongRun.
- `bare_agy_all_preds.jsonl`: Full 500-task predictions for `Google Antigravity (agy)` Bare Baseline.
- `inboost_longrun_metadata.yaml`: Leaderboard entry metadata for InBoost LongRun.
- `bare_agy_metadata.yaml`: Leaderboard entry metadata for Bare Baseline.

---

## 🚀 Running Official Evaluation via `swebench.harness`

You can verify the entire 500-task suite using the official `swebench` python package:

```bash
# 1. Install official SWE-bench evaluation harness
pip install swebench

# 2. Run official evaluation on InBoost LongRun predictions:
python -m swebench.harness.run_evaluation \
    --dataset_name SWE-bench/SWE-bench_Verified \
    --predictions_path benchmarks/export/inboost_longrun_agy_all_preds.jsonl \
    --max_workers 8 \
    --run_id inboost_longrun_500_eval

# 3. Run official evaluation on Bare Baseline predictions:
python -m swebench.harness.run_evaluation \
    --dataset_name SWE-bench/SWE-bench_Verified \
    --predictions_path benchmarks/export/bare_agy_all_preds.jsonl \
    --max_workers 8 \
    --run_id bare_agy_500_eval
```

---

## ☁️ Running Evaluation via SWE-bench Cloud CLI (`sb-cli`)

```bash
# Submit predictions to SWE-bench evaluation server:
sb-cli submit swe-bench_verified test \
    --predictions_path benchmarks/export/inboost_longrun_agy_all_preds.jsonl \
    --run_id inboost_longrun_500_eval
```

---

## 🏆 Submitting to Official Leaderboard (`SWE-bench/experiments`)

To submit these results to the official public leaderboard:
1. Fork `https://github.com/SWE-bench/experiments`.
2. Create folder: `evaluation/verified/20261022_inboost_longrun_agy/`
3. Copy:
   - `inboost_longrun_agy_all_preds.jsonl` -> `all_preds.jsonl`
   - `inboost_longrun_metadata.yaml` -> `metadata.yaml`
   - The resulting `report.json` / `results.json` from `run_evaluation`
4. Open a Pull Request on `SWE-bench/experiments`.
