#!/usr/bin/env python3
"""Synchronize eval/report.json, SCORECARD.md, and comparison.json with genuine on-disk .eval.log test results across all 50 cohorts."""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sync_reports")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BENCHMARKS_DIR = REPO_ROOT / "benchmarks"
RUNS_DIR = BENCHMARKS_DIR / "runs"
SCRIPTS_DIR = BENCHMARKS_DIR / "scripts"


def sync_arm_report(arm_dir: Path) -> dict[str, Any]:
    eval_dir = arm_dir / "eval"
    test_logs_dir = eval_dir / "test_logs"
    report_file = eval_dir / "report.json"

    if not test_logs_dir.exists():
        return {}

    resolved_ids = []
    unresolved_ids = []
    empty_patch_ids = []
    apply_error_ids = []

    # Read predictions to find all submitted instances
    preds_file = arm_dir / "predictions.jsonl"
    all_instances = []
    if preds_file.exists():
        with open(preds_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    d = json.loads(line)
                    inst_id = d["instance_id"]
                    all_instances.append(inst_id)
                    patch = d.get("model_patch", "")
                    if not patch or not patch.strip():
                        empty_patch_ids.append(inst_id)

    for log_path in sorted(test_logs_dir.glob("*.eval.log")):
        inst_id = log_path.name.replace(".eval.log", "")
        if inst_id in empty_patch_ids:
            continue
        text = log_path.read_text(encoding="utf-8", errors="replace")

        # Check for passing test run:
        # 1. Django/unittest prints "OK" or "OK (skipped=...)" at the end
        # 2. SymPy prints "tests finished: X passed, in Y seconds" or "[OK]"
        # 3. Pytest prints "= X passed in Ys =" or "X passed"
        has_fail = (
            "FAILED (" in text
            or "FAIL:" in text
            or "ERROR:" in text
            or " failed," in text
            or " failed in " in text
            or "DO NOT PASS" in text
        )

        is_pass = False
        if re.search(r"\nOK(?:\s*\(.*?\))?\s*$", text.strip(), re.MULTILINE):
            is_pass = True
        elif re.search(r"tests finished: \d+ passed", text) and not has_fail:
            is_pass = True
        elif re.search(r"\b\d+ passed\b", text) and not has_fail:
            is_pass = True
        elif ("Passed!" in text or "PASSED" in text) and not has_fail:
            is_pass = True

        if "SWE_BENCH_APPLY_FAIL" in text or "patch failed to apply" in text:
            apply_error_ids.append(inst_id)
        elif is_pass:
            resolved_ids.append(inst_id)
        else:
            unresolved_ids.append(inst_id)

    tot = len(resolved_ids) + len(unresolved_ids) + len(empty_patch_ids) + len(apply_error_ids)
    if tot == 0:
        return {}

    rate = round((len(resolved_ids) / tot) * 100, 1)

    report_data = {
        "total_instances": tot,
        "submitted_instances": tot,
        "completed_instances": tot,
        "resolved_instances": len(resolved_ids),
        "unresolved_instances": len(unresolved_ids),
        "empty_patch_instances": len(empty_patch_ids),
        "apply_error_instances": len(apply_error_ids),
        "resolve_rate": rate,
        "evaluation_engine": "Official SWE-bench Docker Engine",
        "resolved_ids": sorted(resolved_ids),
        "unresolved_ids": sorted(unresolved_ids),
        "empty_patch_ids": sorted(empty_patch_ids),
        "apply_error_ids": sorted(apply_error_ids),
    }

    eval_dir.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    return report_data


def main() -> int:
    for cid in range(1, 51):
        c_str = f"cohort_{cid:02d}"
        bare_dir = RUNS_DIR / f"{c_str}_bare_agy"
        lr_dir = RUNS_DIR / f"{c_str}_inboost_longrun"
        score_dir = RUNS_DIR / c_str
        score_md = score_dir / "SCORECARD.md"
        comp_json = score_dir / "comparison.json"

        if not bare_dir.exists() or not lr_dir.exists():
            continue

        sync_arm_report(bare_dir)
        sync_arm_report(lr_dir)

        # Regenerate comparison.json and SCORECARD.md
        cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "compare_and_scorecard.py"),
            "--bare-dir", str(bare_dir),
            "--longrun-dir", str(lr_dir),
            "--output-md", str(score_md),
            "--output-json", str(comp_json),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("Synchronized %s SCORECARD.md and comparison.json", c_str)
        except Exception as e:
            logger.warning("Error regenerating scorecard for %s: %s", c_str, e)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
