#!/usr/bin/env python3
"""Modular SWE-bench Cohort Management Utility.

Enables incremental cohort planning, generation, and tracking in batches of 10 tasks.
Maintains benchmarks/cohorts/manifest.json registry with Docker image availability.

Commands:
    python3 cohort_manager.py list
    python3 cohort_manager.py add [--size 10] [--prioritize-cached-docker]
    python3 cohort_manager.py check-docker [--cohort N]
    python3 cohort_manager.py status
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("inboost.cohort_manager")

BENCHMARKS_DIR = Path(__file__).resolve().parent.parent
COHORTS_DIR = BENCHMARKS_DIR / "cohorts"
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


def load_manifest() -> dict[str, Any]:
    """Load or initialize benchmarks/cohorts/manifest.json."""
    COHORTS_DIR.mkdir(parents=True, exist_ok=True)
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {
        "version": "1.0",
        "description": "SWE-bench Verified Modular Cohort Registry (10-task increments)",
        "cohorts": [],
    }


def save_manifest(manifest: dict[str, Any]) -> None:
    """Save manifest atomically."""
    COHORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def cmd_list(args: argparse.Namespace) -> int:
    """List all registered cohorts with their Docker image coverage and run status."""
    manifest = load_manifest()
    cached_images = get_cached_docker_images()

    cohorts = manifest.get("cohorts", [])
    if not cohorts:
        logger.info("No cohorts registered yet. Run 'cohort_manager.py init' or 'cohort_manager.py add'.")
        return 0

    print("\n" + "=" * 90)
    print(f"{'COHORT':<10} | {'NAME':<20} | {'TASKS':<10} | {'DOCKER COVERAGE':<18} | {'STATUS':<12} | {'SCORECARD'}")
    print("=" * 90)

    for c in cohorts:
        cid = c["cohort_id"]
        cname = c.get("name", f"Cohort {cid:02d}")
        task_count = c.get("task_count", 0)
        cfg_path = COHORTS_DIR / f"cohort_{cid:02d}.json"

        # Check Docker coverage
        cached_count = 0
        if cfg_path.exists():
            with open(cfg_path, encoding="utf-8") as f:
                tasks = json.load(f)
            cached_count = sum(1 for t in tasks if t["instance_id"] in cached_images)

        docker_cov = f"{cached_count}/{task_count} images"
        status = c.get("status", "PENDING")
        scorecard = c.get("scorecard", "-")

        print(f"{cid:<10} | {cname:<20} | {task_count:<10} | {docker_cov:<18} | {status:<12} | {scorecard}")

    print("=" * 90 + "\n")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    """Add a new cohort of N tasks (default 10) to the registry."""
    manifest = load_manifest()
    cohorts = manifest.get("cohorts", [])
    next_id = len(cohorts) + 1
    chunk_size = args.size

    # Collect existing instance IDs across all cohorts
    existing_ids: set[str] = set()
    total_existing_tasks = 0
    for c in cohorts:
        cfg = COHORTS_DIR / f"cohort_{c['cohort_id']:02d}.json"
        if cfg.exists():
            with open(cfg, encoding="utf-8") as f:
                t_list = json.load(f)
                for item in t_list:
                    existing_ids.add(item["instance_id"])
                    total_existing_tasks += 1

    cached_images = get_cached_docker_images()

    # Load dataset
    try:
        from datasets import load_dataset  # type: ignore

        ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
    except Exception as e:
        logger.error("Failed to load SWE-bench_Verified dataset: %s", e)
        return 1

    # Filter candidates not yet in any cohort
    candidates = [item for item in ds if item["instance_id"] not in existing_ids]

    if args.prioritize_cached_docker and cached_images:
        # Prioritize tasks with local Docker images already downloaded
        with_docker = [c for c in candidates if c["instance_id"] in cached_images]
        without_docker = [c for c in candidates if c["instance_id"] not in cached_images]
        sorted_candidates = with_docker + without_docker
    else:
        sorted_candidates = candidates

    if len(sorted_candidates) < chunk_size:
        logger.warning("Only %d candidates available (requested %d)", len(sorted_candidates), chunk_size)
        selected = sorted_candidates
    else:
        selected = sorted_candidates[:chunk_size]

    if not selected:
        logger.error("No eligible tasks available to create a new cohort.")
        return 1

    # Format selected instances
    formatted_instances = []
    start_index = total_existing_tasks + 1
    for i, inst in enumerate(selected):
        formatted_instances.append({
            "index": start_index + i,
            "cohort": next_id,
            "chunk": next_id,
            "instance_id": inst["instance_id"],
            "repo": inst["repo"],
            "base_commit": inst["base_commit"],
            "title": inst.get("problem_statement", "").split("\n")[0][:100],
            "problem_statement": inst.get("problem_statement", ""),
            "FAIL_TO_PASS": inst.get("FAIL_TO_PASS", "[]"),
            "PASS_TO_PASS": inst.get("PASS_TO_PASS", "[]"),
            "test_patch": inst.get("test_patch", ""),
            "version": inst.get("version", ""),
        })

    new_cfg_file = COHORTS_DIR / f"cohort_{next_id:02d}.json"
    with open(new_cfg_file, "w", encoding="utf-8") as f:
        json.dump(formatted_instances, f, indent=2, ensure_ascii=False)

    docker_cov = sum(1 for inst in formatted_instances if inst["instance_id"] in cached_images)

    cohort_entry = {
        "cohort_id": next_id,
        "name": f"Cohort {next_id:02d}",
        "task_count": len(formatted_instances),
        "config_file": f"cohorts/cohort_{next_id:02d}.json",
        "indices": [start_index, start_index + len(formatted_instances) - 1],
        "cached_docker_images": docker_cov,
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scorecard": None,
    }

    cohorts.append(cohort_entry)
    manifest["cohorts"] = cohorts
    save_manifest(manifest)

    logger.info(
        "Successfully added Cohort %02d with %d tasks (Indices %d..%d). Docker coverage: %d/%d.",
        next_id,
        len(formatted_instances),
        start_index,
        start_index + len(formatted_instances) - 1,
        docker_cov,
        len(formatted_instances),
    )
    logger.info("Saved configuration to: %s", new_cfg_file)
    return 0


def cmd_check_docker(args: argparse.Namespace) -> int:
    """Check Docker daemon and image availability for all cohorts."""
    cached_images = get_cached_docker_images()
    manifest = load_manifest()

    print("\n--- Docker Verification Readiness ---")
    print(f"Total Local Docker Images Cached: {len(cached_images)}")

    cohorts = manifest.get("cohorts", [])
    if args.cohort:
        cohorts = [c for c in cohorts if c["cohort_id"] == args.cohort]

    for c in cohorts:
        cid = c["cohort_id"]
        cfg = COHORTS_DIR / f"cohort_{cid:02d}.json"
        if not cfg.exists():
            continue
        with open(cfg, encoding="utf-8") as f:
            tasks = json.load(f)

        present = []
        missing = []
        for t in tasks:
            iid = t["instance_id"]
            if iid in cached_images:
                present.append(iid)
            else:
                missing.append(iid)

        print(f"\nCohort {cid:02d}: {len(present)}/{len(tasks)} Docker images ready")
        if missing:
            print("  Missing images (will need to pull during live verification):")
            for m in missing:
                print(f"    - {m}")
        else:
            print("  All 10/10 Docker images pre-cached! 100% Zero pull overhead.")

    print("")
    return 0


def cmd_init_from_existing(args: argparse.Namespace) -> int:
    """Initialize benchmarks/cohorts from existing cohort50_chunk_1..5.json configs."""
    configs_dir = BENCHMARKS_DIR / "configs"
    COHORTS_DIR.mkdir(parents=True, exist_ok=True)
    cached_images = get_cached_docker_images()

    cohorts = []
    for i in range(1, 6):
        src_file = configs_dir / f"cohort50_chunk_{i}.json"
        dst_file = COHORTS_DIR / f"cohort_{i:02d}.json"
        if not src_file.exists():
            continue

        with open(src_file, encoding="utf-8") as f:
            tasks = json.load(f)

        # Update metadata keys
        for t in tasks:
            t["cohort"] = i

        with open(dst_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

        start_idx = tasks[0]["index"]
        end_idx = tasks[-1]["index"]
        docker_cov = sum(1 for t in tasks if t["instance_id"] in cached_images)

        # Check if already completed (e.g. chunk 1)
        runs_dir = BENCHMARKS_DIR / "runs" / f"cohort50_chunk_{i}"
        status = "COMPLETED" if (runs_dir / "SCORECARD.md").exists() else "PENDING"
        scorecard = str(runs_dir / "SCORECARD.md") if status == "COMPLETED" else None

        cohorts.append({
            "cohort_id": i,
            "name": f"Cohort {i:02d}",
            "task_count": len(tasks),
            "config_file": f"cohorts/cohort_{i:02d}.json",
            "indices": [start_idx, end_idx],
            "cached_docker_images": docker_cov,
            "status": status,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "scorecard": scorecard,
        })

    manifest = {
        "version": "1.0",
        "description": "SWE-bench Verified Modular Cohort Registry (10-task increments)",
        "cohorts": cohorts,
    }
    save_manifest(manifest)
    logger.info("Initialized %d cohorts into %s", len(cohorts), COHORTS_DIR)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Modular SWE-bench Cohort Management")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    subparsers.add_parser("list", help="List registered cohorts and Docker status")

    # add
    add_parser = subparsers.add_parser("add", help="Add next 10-task cohort")
    add_parser.add_argument("--size", type=int, default=10, help="Number of tasks per cohort (default: 10)")
    add_parser.add_argument(
        "--prioritize-cached-docker",
        action="store_true",
        default=True,
        help="Prioritize instances with pre-cached Docker images",
    )

    # check-docker
    check_parser = subparsers.add_parser("check-docker", help="Check Docker coverage for cohorts")
    check_parser.add_argument("--cohort", type=int, default=None, help="Specific cohort ID to inspect")

    # init
    subparsers.add_parser("init", help="Initialize registry from existing chunks")

    args = parser.parse_args()

    if args.command == "list":
        return cmd_list(args)
    if args.command == "add":
        return cmd_add(args)
    if args.command == "check-docker":
        return cmd_check_docker(args)
    if args.command == "init":
        return cmd_init_from_existing(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
