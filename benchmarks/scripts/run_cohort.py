#!/usr/bin/env python3
"""Antigravity (agy) Cohort Benchmark Runner: InBoost AI LongRun vs Bare.

Executes a full 10-task SWE-bench Verified cohort evaluation by cohort number:
1. Validates cohort configuration (benchmarks/cohorts/cohort_{N:02d}.json).
2. Verifies local Docker daemon image availability (10/10 pre-cached).
3. Phase 1: Generates candidate predictions for Bare and InBoost LongRun.
4. Phase 2: Runs parallel Docker container verification with official SWE-bench Verified methodology (1200s timeout).
5. Phase 3: Computes comparative scorecards (SCORECARD.md and comparison.json).
6. Updates benchmarks/cohorts/manifest.json registry with COMPLETED status.
7. Prints the completed markdown scorecard directly to stdout.

Usage:
    python3 benchmarks/scripts/run_cohort.py 3
    python3 benchmarks/scripts/run_cohort.py 3 --timeout 1200 --sequential-docker
    ./run_cohort.sh 3
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("inboost.run_cohort")

BENCHMARKS_DIR = Path(__file__).resolve().parent.parent
COHORTS_DIR = BENCHMARKS_DIR / "cohorts"
RUNS_DIR = BENCHMARKS_DIR / "runs"
SCRIPTS_DIR = BENCHMARKS_DIR / "scripts"
MANIFEST_FILE = COHORTS_DIR / "manifest.json"


def get_cached_docker_images() -> set[str]:
    """Scan local Docker daemon for pre-pulled SWE-bench evaluation images."""
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return set()
    try:
        res = subprocess.run(
            [docker_bin, "images", "--format", "{{.Repository}}"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if res.returncode != 0:
            return set()
        images = set()
        for line in res.stdout.splitlines():
            line = line.strip()
            if line.startswith("swebench/sweb.eval.x86_64."):
                inst_id = line.replace("swebench/sweb.eval.x86_64.", "").replace("_1776_", "__")
                images.add(inst_id)
        return images
    except Exception as e:  # noqa: BLE001
        logger.debug("Failed to list Docker images: %s", e)
        return set()


def get_agy_quota() -> dict[str, Any] | None:
    """Fetch live Antigravity quota and remaining limits via agy CLI."""
    agy_bin = shutil.which("agy")
    if not agy_bin:
        return None
    try:
        res = subprocess.run(
            [agy_bin, "-p", "/usage", "--output-format", "json", "--dangerously-skip-permissions"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if res.returncode != 0:
            return None
        data = json.loads(res.stdout)
        groups = data.get("command", {}).get("data", {}).get("groups", [])
        quota_summary = {}
        for grp in groups:
            grp_name = grp.get("name", "")
            for b in grp.get("buckets", []):
                key = f"{grp_name}: {b.get('name', '')}"
                quota_summary[key] = {
                    "group": grp_name,
                    "name": b.get("name", ""),
                    "remaining_pct": round(b.get("remaining_fraction", 1.0) * 100, 1),
                    "reset_time": b.get("reset_time", ""),
                    "window": b.get("window", ""),
                }
        return quota_summary
    except Exception as e:  # noqa: BLE001
        logger.debug("Failed to query agy quota: %s", e)
        return None


def update_manifest_cohort(cohort_id: int, scorecard_rel_path: str) -> None:
    """Update status and scorecard path for cohort in manifest.json."""
    if not MANIFEST_FILE.exists():
        logger.warning("Manifest file not found at %s", MANIFEST_FILE)
        return

    try:
        with open(MANIFEST_FILE, encoding="utf-8") as f:
            manifest = json.load(f)

        updated = False
        for c in manifest.get("cohorts", []):
            if c.get("cohort_id") == cohort_id:
                c["status"] = "COMPLETED"
                c["scorecard"] = scorecard_rel_path
                updated = True
                break

        if updated:
            with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            logger.info("Updated manifest.json: Cohort %02d marked COMPLETED", cohort_id)
        else:
            logger.warning("Cohort %d not found in manifest cohorts array", cohort_id)
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to update manifest.json: %s", e)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Antigravity (agy) InBoost LongRun vs Bare Cohort Benchmark Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("cohort", type=int, help="Cohort number to execute (e.g. 1, 2, 3..50)")
    parser.add_argument("--timeout", type=int, default=1200, help="Per-container Docker timeout in seconds (20 min)")
    parser.add_argument("--sequential-docker", action="store_true", help="Run Docker verification sequentially")
    parser.add_argument("--skip-runs", action="store_true", help="Skip Phase 1 prediction generation (use existing runs)")
    parser.add_argument("--syntax-only", action="store_true", help="Perform syntax check only without running Docker containers")

    args = parser.parse_args()

    cohort_num = args.cohort
    cohort_str = f"cohort_{cohort_num:02d}"
    cohort_config = COHORTS_DIR / f"{cohort_str}.json"

    if not cohort_config.exists():
        logger.error("Cohort config not found: %s", cohort_config)
        logger.error("Available cohorts can be found under %s", COHORTS_DIR)
        return 1

    with open(cohort_config, encoding="utf-8") as f:
        tasks = json.load(f)

    print("\n" + "=" * 78)
    print(f" InBoost AI LongRun vs Bare — Cohort {cohort_num:02d} Benchmark")
    print("=" * 78)
    print(f" Cohort File:     {cohort_config.relative_to(BENCHMARKS_DIR.parent)}")
    print(f" Total Tasks:     {len(tasks)} SWE-bench Verified tasks")
    print(f" Docker Timeout:  {args.timeout}s ({args.timeout // 60} minutes)")
    print(f" Execution Mode:  {'Evaluate Existing Predictions' if args.skip_runs else 'Live agy CLI'}")
    print(f" Docker Engine:   {'Syntax Only (Offline)' if args.syntax_only else 'Live Docker Container Evaluation'}")
    print("=" * 78)

    # Step 1: Query live agy quota snapshot
    initial_quota = get_agy_quota()
    if initial_quota:
        print("\n[Step 1/5] Live Antigravity (agy) Quota Snapshot:")
        for k, v in initial_quota.items():
            print(f"  • {k}: {v['remaining_pct']}% remaining (Resets: {v['reset_time']})")
    else:
        print("\n[Step 1/5] Antigravity Quota Telemetry: agy CLI offline.")

    # Step 2: Check Docker image availability
    cached_images = get_cached_docker_images()
    cached_count = sum(1 for t in tasks if t["instance_id"] in cached_images)
    print(f"\n[Step 2/5] Docker Image Cache Audit: {cached_count}/{len(tasks)} images pre-cached.")
    if cached_count < len(tasks) and not args.syntax_only:
        missing = [t["instance_id"] for t in tasks if t["instance_id"] not in cached_images]
        logger.warning("Some images are not pre-cached locally: %s", missing)

    # Directories
    bare_out = RUNS_DIR / f"{cohort_str}_bare_agy"
    longrun_out = RUNS_DIR / f"{cohort_str}_inboost_longrun"
    scorecard_out_dir = RUNS_DIR / cohort_str
    scorecard_out_dir.mkdir(parents=True, exist_ok=True)

    # Phase 1: Prediction generation
    if not args.skip_runs:
        print("\n" + "-" * 78)
        print(" [Phase 1/3] Generating Candidate Predictions for Bare and InBoost LongRun")
        print("-" * 78)

        # 1.1 Bare
        print(f"\n>>> Running Bare baseline for {cohort_str}...")
        cmd_bare = [
            sys.executable,
            str(SCRIPTS_DIR / "run_bare_agy.py"),
            "--config", str(cohort_config),
            "--output-dir", str(bare_out),
            "--timeout", str(args.timeout),
        ]
        subprocess.run(cmd_bare, check=True)

        # 1.2 InBoost LongRun
        print(f"\n>>> Running InBoost LongRun accelerated agent for {cohort_str}...")
        cmd_longrun = [
            sys.executable,
            str(SCRIPTS_DIR / "run_inboost_longrun_agy.py"),
            "--config", str(cohort_config),
            "--output-dir", str(longrun_out),
            "--timeout", str(args.timeout),
        ]
        subprocess.run(cmd_longrun, check=True)

        print("\n✓ Phase 1 Complete: Candidate patches generated and sealed.")
    else:
        print("\n[Phase 1/3] Skipping prediction generation (--skip-runs specified).")

    # Phase 2: Docker Verification
    print("\n" + "-" * 78)
    print(f" [Phase 2/3] Official Docker Test Verification (Timeout: {args.timeout}s / {args.timeout // 60}m per task)")
    print("-" * 78)

    bare_preds = bare_out / "predictions.jsonl"
    longrun_preds = longrun_out / "predictions.jsonl"

    if not bare_preds.exists() or not longrun_preds.exists():
        logger.error("Missing prediction files. Bare: %s, LongRun: %s", bare_preds.exists(), longrun_preds.exists())
        return 1

    cmd_verify_bare = [
        sys.executable,
        str(SCRIPTS_DIR / "verify_docker.py"),
        "--predictions", str(bare_preds),
        "--config", str(cohort_config),
        "--timeout", str(args.timeout),
    ]
    if args.syntax_only:
        cmd_verify_bare.append("--syntax-only")

    cmd_verify_longrun = [
        sys.executable,
        str(SCRIPTS_DIR / "verify_docker.py"),
        "--predictions", str(longrun_preds),
        "--config", str(cohort_config),
        "--timeout", str(args.timeout),
    ]
    if args.syntax_only:
        cmd_verify_longrun.append("--syntax-only")

    if args.sequential_docker:
        print("Executing Docker evaluations sequentially...")
        print("\n--- [1/2] Bare Docker Verification ---")
        subprocess.run(cmd_verify_bare, check=True)
        print("\n--- [2/2] InBoost LongRun Docker Verification ---")
        subprocess.run(cmd_verify_longrun, check=True)
    else:
        print("Launching PARALLEL Docker verification workers for Bare and InBoost LongRun...")
        bare_log_path = bare_out / "docker_eval.log"
        longrun_log_path = longrun_out / "docker_eval.log"

        with open(bare_log_path, "w", encoding="utf-8") as fb, open(longrun_log_path, "w", encoding="utf-8") as fl:
            p_bare = subprocess.Popen(cmd_verify_bare, stdout=fb, stderr=subprocess.STDOUT)
            p_longrun = subprocess.Popen(cmd_verify_longrun, stdout=fl, stderr=subprocess.STDOUT)

            print(f"  -> Bare Docker worker launched (PID: {p_bare.pid}, log: {bare_log_path.name})")
            print(f"  -> InBoost LongRun Docker worker launched (PID: {p_longrun.pid}, log: {longrun_log_path.name})")
            print("  Waiting for container evaluations to finish...")

            p_bare.wait()
            p_longrun.wait()

        print("\n--- Bare Docker Evaluation Summary ---")
        if bare_log_path.exists():
            print(bare_log_path.read_text(encoding="utf-8"))

        print("\n--- InBoost LongRun Docker Evaluation Summary ---")
        if longrun_log_path.exists():
            print(longrun_log_path.read_text(encoding="utf-8"))

    # Phase 3: Scorecard & Analysis
    print("\n" + "-" * 78)
    print(" [Phase 3/3] Generating Comparative Scorecard & Analysis")
    print("-" * 78)

    # Snapshot final quota and calculate session delta
    final_quota = get_agy_quota()
    quota_snapshot = {
        "initial": initial_quota,
        "final": final_quota,
    }
    quota_file = scorecard_out_dir / "quota_snapshot.json"
    with open(quota_file, "w", encoding="utf-8") as f:
        json.dump(quota_snapshot, f, indent=2)

    scorecard_md = scorecard_out_dir / "SCORECARD.md"
    comparison_json = scorecard_out_dir / "comparison.json"

    cmd_scorecard = [
        sys.executable,
        str(SCRIPTS_DIR / "compare_and_scorecard.py"),
        "--bare-dir", str(bare_out),
        "--longrun-dir", str(longrun_out),
        "--output-md", str(scorecard_md),
        "--output-json", str(comparison_json),
        "--quota-file", str(quota_file),
    ]
    subprocess.run(cmd_scorecard, check=True)

    # Phase 4: Manifest Update
    rel_scorecard = f"benchmarks/runs/{cohort_str}/SCORECARD.md"
    update_manifest_cohort(cohort_num, rel_scorecard)

    # Phase 5: Display Scorecard to stdout
    print("\n" + "=" * 78)
    print(f" OFFICIAL SCORECARD: COHORT {cohort_num:02d}")
    print("=" * 78 + "\n")
    if scorecard_md.exists():
        print(scorecard_md.read_text(encoding="utf-8"))

    print("\n✓ Cohort run complete! Scorecard saved to: " + str(scorecard_md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
