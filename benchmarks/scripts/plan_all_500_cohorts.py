#!/usr/bin/env python3
"""SWE-bench Verified 500-Task Stratified Cohort Planner.

Generates 50 uniform cohorts of 10 tasks each from princeton-nlp/SWE-bench_Verified (500 tasks):
- Cohort 01 is preserved (tasks 1..10, 10/10 Docker cached).
- Cohorts 02..50 are generated using optimal biproportional apportionment (Max-Flow).
- Uniform stratified repository representation across all 50 cohorts:
    * 4 or 5 django/django tasks per cohort
    * 1 or 2 sympy/sympy tasks per cohort
    * 0 or 1 task for each other repo (sphinx, matplotlib, scikit-learn, astropy, xarray, pytest, pylint, requests, seaborn, flask)
- Pre-cached local Docker images are prioritized into earlier cohorts so they can run immediately.
- Outputs individual cohort configs (cohort_01.json .. cohort_50.json),
  a unified master file (swebench_verified_500_all_cohorts.json), and manifest.json.
"""

from __future__ import annotations

import collections
import json
import logging
import shutil
import subprocess
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("inboost.plan_500_cohorts")

BENCHMARKS_DIR = Path(__file__).resolve().parent.parent
COHORTS_DIR = BENCHMARKS_DIR / "cohorts"
MANIFEST_FILE = COHORTS_DIR / "manifest.json"
MASTER_FILE = COHORTS_DIR / "swebench_verified_500_all_cohorts.json"


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


def main() -> int:
    logger.info("==================================================")
    logger.info("SWE-bench Verified 500-Task Stratified Cohort Planner")
    logger.info("Target: 50 Cohorts x 10 Tasks (100% Uniform Coverage)")
    logger.info("==================================================")

    cached_docker_ids = get_cached_docker_images()
    logger.info("Local Docker cached images found: %d", len(cached_docker_ids))

    COHORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load existing Cohort 01 if available
    c1_file = COHORTS_DIR / "cohort_01.json"
    if not c1_file.exists():
        legacy_c1 = BENCHMARKS_DIR / "configs" / "cohort50_chunk_1.json"
        if legacy_c1.exists():
            c1_file.write_text(legacy_c1.read_text(encoding="utf-8"), encoding="utf-8")

    if not c1_file.exists():
        logger.error("Cohort 01 file not found at %s", c1_file)
        return 1

    with open(c1_file, encoding="utf-8") as f:
        cohort_01_tasks = json.load(f)

    # Ensure index and cohort metadata for Cohort 1
    for idx, t in enumerate(cohort_01_tasks, 1):
        t["index"] = idx
        t["cohort"] = 1
        t["chunk"] = 1

    c1_ids = set(t["instance_id"] for t in cohort_01_tasks)
    logger.info("Cohort 01 preserved: %d tasks (IDs: %s)", len(cohort_01_tasks), sorted(list(c1_ids))[:3])

    # 2. Load dataset from HF
    try:
        from datasets import load_dataset  # type: ignore

        ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
        all_instances = list(ds)
    except Exception as e:
        logger.error("Failed to load SWE-bench_Verified dataset: %s", e)
        return 1

    logger.info("Total SWE-bench Verified instances in dataset: %d", len(all_instances))
    assert len(all_instances) == 500, f"Expected 500 instances, got {len(all_instances)}"

    # 3. Filter out Cohort 01 instances
    remaining_instances = [inst for inst in all_instances if inst["instance_id"] not in c1_ids]
    assert len(remaining_instances) == 490, f"Expected 490 remaining instances, got {len(remaining_instances)}"

    # 4. Group remaining instances by repo
    by_repo: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for inst in remaining_instances:
        by_repo[inst["repo"]].append(inst)

    # Sort each repo queue so that cached Docker images come first, followed by deterministic instance_id
    for r in by_repo:
        by_repo[r].sort(key=lambda x: (0 if x["instance_id"] in cached_docker_ids else 1, x["instance_id"]))

    repo_counts = {r: len(by_repo[r]) for r in by_repo}
    logger.info("Remaining repository counts across 49 cohorts:")
    for r, count in sorted(repo_counts.items(), key=lambda kv: kv[1], reverse=True):
        logger.info("  %s: %d", r, count)

    # 5. Determine base and remainder allocations for Cohorts 2..50 (49 cohorts)
    num_cohorts = 49
    repo_base = {r: count // num_cohorts for r, count in repo_counts.items()}
    repo_rem = {r: count % num_cohorts for r, count in repo_counts.items()}

    # Base: django=4, sympy=1. Sum of base = 5 per cohort.
    assert sum(repo_base.values()) == 5
    assert sum(repo_rem.values()) == 245  # 49 * 5 = 245

    # 6. Distribute remainders using Edmonds-Karp Max Flow
    source = "source"
    sink = "sink"
    repos = list(repo_rem.keys())
    cohort_nums = list(range(2, 51))  # Cohorts 2 to 50

    capacity: dict[tuple[str, Any], int] = {}
    adj: dict[str | int, list[str | int]] = {}

    def add_edge(u: str | int, v: str | int, cap: int) -> None:
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)
        capacity[(u, v)] = cap
        capacity[(v, u)] = 0

    for r in repos:
        add_edge(source, r, repo_rem[r])
        for c in cohort_nums:
            add_edge(r, c, 1)

    for c in cohort_nums:
        add_edge(c, sink, 5)

    flow: dict[tuple[str | int, str | int], int] = collections.defaultdict(int)

    total_flow = 0
    while True:
        parent: dict[str | int, str | int] = {}
        queue: deque[str | int] = deque([source])
        while queue:
            u = queue.popleft()
            if u == sink:
                break
            for v in adj[u]:
                if v not in parent and capacity.get((u, v), 0) - flow.get((u, v), 0) > 0:
                    parent[v] = u
                    queue.append(v)
        if sink not in parent:
            break

        curr = sink
        bottleneck = float("inf")
        while curr != source:
            p = parent[curr]
            bottleneck = min(bottleneck, capacity[(p, curr)] - flow[(p, curr)])
            curr = p
        curr = sink
        while curr != source:
            p = parent[curr]
            flow[(p, curr)] += int(bottleneck)
            flow[(curr, p)] -= int(bottleneck)
            curr = p
        total_flow += int(bottleneck)

    assert total_flow == 245, f"Expected 245 max flow, got {total_flow}"
    logger.info("Biproportional apportionment solved: exactly 245 remainder slots allocated.")

    # 7. Assemble all 50 cohorts
    all_cohorts_dict: dict[int, list[dict[str, Any]]] = {1: cohort_01_tasks}
    current_global_index = 11

    for c_id in cohort_nums:
        tasks_for_cohort: list[dict[str, Any]] = []

        # 1. Base tasks (django=4, sympy=1)
        for r, b_count in repo_base.items():
            for _ in range(b_count):
                tasks_for_cohort.append(by_repo[r].pop(0))

        # 2. Remainder tasks from max flow (5 tasks)
        for r in repos:
            if flow[(r, c_id)] > 0:
                tasks_for_cohort.append(by_repo[r].pop(0))

        assert len(tasks_for_cohort) == 10, f"Cohort {c_id} has {len(tasks_for_cohort)} tasks, expected 10"

        # Format tasks
        formatted_tasks = []
        for t in tasks_for_cohort:
            formatted_tasks.append({
                "index": current_global_index,
                "cohort": c_id,
                "chunk": c_id,
                "instance_id": t["instance_id"],
                "repo": t["repo"],
                "base_commit": t["base_commit"],
                "title": t.get("problem_statement", "").split("\n")[0][:100],
                "problem_statement": t.get("problem_statement", ""),
                "FAIL_TO_PASS": t.get("FAIL_TO_PASS", "[]") if isinstance(t.get("FAIL_TO_PASS"), str) else json.dumps(t.get("FAIL_TO_PASS", [])),
                "PASS_TO_PASS": t.get("PASS_TO_PASS", "[]") if isinstance(t.get("PASS_TO_PASS"), str) else json.dumps(t.get("PASS_TO_PASS", [])),
                "test_patch": t.get("test_patch", ""),
                "version": t.get("version", ""),
            })
            current_global_index += 1

        all_cohorts_dict[c_id] = formatted_tasks

    # Verify all queues are empty
    for r in by_repo:
        assert len(by_repo[r]) == 0, f"Repo {r} has {len(by_repo[r])} unassigned tasks"

    logger.info("All 500 instances successfully partitioned across 50 cohorts.")

    # 8. Write individual cohort files and master file
    master_list: list[dict[str, Any]] = []
    manifest_cohorts: list[dict[str, Any]] = []

    for c_id in range(1, 51):
        c_tasks = all_cohorts_dict[c_id]
        master_list.extend(c_tasks)

        out_path = COHORTS_DIR / f"cohort_{c_id:02d}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(c_tasks, f, indent=2, ensure_ascii=False)

        docker_cov = sum(1 for t in c_tasks if t["instance_id"] in cached_docker_ids)
        repos_breakdown = dict(collections.Counter(t["repo"] for t in c_tasks))

        runs_dir = BENCHMARKS_DIR / "runs" / f"cohort_{c_id:02d}"
        legacy_runs_dir = BENCHMARKS_DIR / "runs" / f"cohort50_chunk_{c_id}"
        status = "PENDING"
        scorecard = None

        if (runs_dir / "SCORECARD.md").exists():
            status = "COMPLETED"
            scorecard = str(runs_dir / "SCORECARD.md")
        elif (legacy_runs_dir / "SCORECARD.md").exists():
            status = "COMPLETED"
            scorecard = str(legacy_runs_dir / "SCORECARD.md")

        manifest_cohorts.append({
            "cohort_id": c_id,
            "name": f"Cohort {c_id:02d}",
            "task_count": len(c_tasks),
            "indices": [c_tasks[0]["index"], c_tasks[-1]["index"]],
            "config_file": f"cohorts/cohort_{c_id:02d}.json",
            "cached_docker_images": docker_cov,
            "repo_distribution": repos_breakdown,
            "status": status,
            "scorecard": scorecard,
        })

    # Save master file
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(master_list, f, indent=2, ensure_ascii=False)
    logger.info("Saved 500-task master file to: %s", MASTER_FILE)

    # Save manifest
    manifest_data = {
        "version": "2.0",
        "description": "SWE-bench Verified Complete 500-Task Stratified Cohort Registry (50 Cohorts x 10 Tasks)",
        "total_tasks": len(master_list),
        "total_cohorts": len(manifest_cohorts),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_docker_cached_images": sum(c["cached_docker_images"] for c in manifest_cohorts),
        "cohorts": manifest_cohorts,
    }

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    logger.info("Saved manifest with 50 cohorts to: %s", MANIFEST_FILE)

    logger.info("==================================================")
    logger.info("Successfully planned all 50 cohorts (500 tasks total)!")
    logger.info("==================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
