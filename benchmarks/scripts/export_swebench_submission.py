#!/usr/bin/env python3
"""Export full SWE-bench Verified (N=500) predictions for official leaderboard submission.

Bundles all 50 cohorts into consolidated `all_preds.jsonl` files compatible with:
1. Official SWE-bench evaluation harness: `python -m swebench.harness.run_evaluation`
2. Official SWE-bench Cloud CLI: `sb-cli submit`
3. Official Leaderboard PR repository: `github.com/SWE-bench/experiments`

Usage:
    python3 benchmarks/scripts/export_swebench_submission.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def export_submission() -> None:
    benchmarks_dir = Path(__file__).resolve().parent.parent
    runs_dir = benchmarks_dir / "runs"
    export_dir = benchmarks_dir / "export"
    export_dir.mkdir(parents=True, exist_ok=True)

    arms = [
        ("inboost_longrun_agy", "inboost_longrun"),
        ("bare_agy", "bare_agy"),
    ]

    for arm_label, dir_suffix in arms:
        out_file = export_dir / f"{arm_label}_all_preds.jsonl"
        all_preds: list[dict[str, Any]] = []
        seen_instances: set[str] = set()

        can_rebuild = True
        for cid in range(1, 51):
            cohort_name = f"cohort_{cid:02d}"
            pred_file = runs_dir / f"{cohort_name}_{dir_suffix}" / "predictions.jsonl"
            if not pred_file.exists():
                can_rebuild = False
                break

        if not can_rebuild:
            if out_file.exists():
                with out_file.open("r", encoding="utf-8") as f:
                    preds_count = sum(1 for line in f if line.strip())
                if preds_count == 500:
                    print(f"✓ Found existing verified submission bundle: {out_file} (500 instances)")
                    continue
            raise FileNotFoundError(
                f"Missing prediction files in {runs_dir} and {out_file} not found. "
                "Per-cohort scratch runs are required when building from scratch."
            )

        for cid in range(1, 51):
            cohort_name = f"cohort_{cid:02d}"
            pred_file = runs_dir / f"{cohort_name}_{dir_suffix}" / "predictions.jsonl"

            with pred_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    iid = item["instance_id"]
                    if iid in seen_instances:
                        raise ValueError(f"Duplicate instance {iid} in {pred_file}")
                    seen_instances.add(iid)
                    all_preds.append({
                        "instance_id": iid,
                        "model_name_or_path": item.get("model_name_or_path", arm_label),
                        "model_patch": item.get("model_patch", ""),
                    })

        if len(all_preds) != 500:
            raise ValueError(f"Expected 500 instances for {arm_label}, found {len(all_preds)}")

        with out_file.open("w", encoding="utf-8") as f:
            for pred in all_preds:
                f.write(json.dumps(pred) + "\n")

        print(f"✓ Exported {len(all_preds)} instances to {out_file}")

    # Generate metadata.yaml for InBoost LongRun submission
    metadata_longrun = (
        "name: \"Google Antigravity (agy) + InBoost LongRun\"\n"
        "org: \"InBoost\"\n"
        "site: \"https://inboost.pro\"\n"
        "oss: false\n"
        "model: \"gemini-3.8-flash-high / gemini-4-argon\"\n"
        "model_org: \"Google DeepMind\"\n"
        "agent: \"Google Antigravity (agy) + InBoost LongRun L0 Offload Engine\"\n"
        "agent_org: \"InBoost & Google DeepMind\"\n"
        "system:\n"
        "  attempts: 1\n"
        "info: \"https://inboost.pro\"\n"
    )
    (export_dir / "inboost_longrun_metadata.yaml").write_text(metadata_longrun, encoding="utf-8")

    # Generate metadata.yaml for Bare AGY baseline
    metadata_bare = (
        "name: \"Google Antigravity (agy) Bare Baseline\"\n"
        "org: \"Google DeepMind\"\n"
        "site: \"https://deepmind.google\"\n"
        "oss: false\n"
        "model: \"gemini-3.8-flash-high / gemini-4-argon\"\n"
        "model_org: \"Google DeepMind\"\n"
        "agent: \"Google Antigravity (agy)\"\n"
        "agent_org: \"Google DeepMind\"\n"
        "system:\n"
        "  attempts: 1\n"
    )
    (export_dir / "bare_agy_metadata.yaml").write_text(metadata_bare, encoding="utf-8")

    # Generate README instructions for official harness and leaderboard
    readme_content = """# Official SWE-bench Verified Submission Bundle (N=500)

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
python -m swebench.harness.run_evaluation \\
    --dataset_name SWE-bench/SWE-bench_Verified \\
    --predictions_path benchmarks/export/inboost_longrun_agy_all_preds.jsonl \\
    --max_workers 8 \\
    --run_id inboost_longrun_500_eval

# 3. Run official evaluation on Bare Baseline predictions:
python -m swebench.harness.run_evaluation \\
    --dataset_name SWE-bench/SWE-bench_Verified \\
    --predictions_path benchmarks/export/bare_agy_all_preds.jsonl \\
    --max_workers 8 \\
    --run_id bare_agy_500_eval
```

---

## ☁️ Running Evaluation via SWE-bench Cloud CLI (`sb-cli`)

```bash
# Submit predictions to SWE-bench evaluation server:
sb-cli submit swe-bench_verified test \\
    --predictions_path benchmarks/export/inboost_longrun_agy_all_preds.jsonl \\
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
"""
    (export_dir / "README.md").write_text(readme_content, encoding="utf-8")
    print(f"✓ Created submission metadata and instructions in {export_dir}")


if __name__ == "__main__":
    export_submission()
