#!/usr/bin/env bash
# ==============================================================================
# InBoost AI LongRun vs Bare agy: Master Benchmark & Docker Verification Suite
# ==============================================================================
# Evaluates Google Antigravity (`agy`) in Bare Vanilla mode vs InBoost LongRun
# on a random cohort of 25 tasks from SWE-bench Verified.
#
# Usage:
#   ./run_all_benchmark.sh [--dry-run] [--max-tasks 25] [--seed 42]
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${SCRIPT_DIR}/configs"
RUNS_DIR="${SCRIPT_DIR}/runs"
COHORT_CONFIG="${CONFIG_DIR}/swebench_cohort_25_random.json"

SEED="42"
MAX_TASKS=""
DRY_RUN=""
SKIP_RUNS=false
MOCK_DOCKER=""

function print_usage() {
    cat <<EOF
Usage: ./run_all_benchmark.sh [OPTIONS]

Options:
  --seed <int>        Random seed for cohort sampling (default: 42)
  --max-tasks <int>   Limit execution to N tasks (e.g. 5, default: all 25)
  --dry-run           Execute in synthetic/simulation mode (no API tokens or heavy GPU compute)
  --mock-docker       Force mock/structural Docker verification (useful if docker daemon is restricted)
  --skip-runs         Skip task execution and jump straight to Docker verification & scorecard
  -h, --help          Show this help message
EOF
}

# Parse command line flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        --seed)
            SEED="$2"
            shift 2
            ;;
        --max-tasks)
            MAX_TASKS="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            MOCK_DOCKER="--mock"
            shift
            ;;
        --mock-docker)
            MOCK_DOCKER="--mock"
            shift
            ;;
        --skip-runs)
            SKIP_RUNS=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            print_usage
            exit 1
            ;;
    esac
done

echo "======================================================================"
echo " InBoost LongRun vs Bare agy: SWE-bench Verified (N=25) Benchmark"
echo "======================================================================"
echo " Directory:   ${SCRIPT_DIR}"
echo " Seed:        ${SEED}"
echo " Dry Run:     ${DRY_RUN:-No (Live agy Execution)}"
echo " Mock Docker: ${MOCK_DOCKER:-Auto (Check daemon access)}"
echo "======================================================================"

# Step 1: Ensure Cohort Sampling
if [[ ! -f "${COHORT_CONFIG}" ]]; then
    echo "[Step 1/5] Sampling random cohort of 25 tasks from SWE-bench Verified..."
    python3 "${SCRIPT_DIR}/sample_random_cohort25.py" --seed "${SEED}" --output "${COHORT_CONFIG}"
else
    echo "[Step 1/5] Cohort configuration ready: ${COHORT_CONFIG}"
fi

MAX_FLAG=""
if [[ -n "${MAX_TASKS}" ]]; then
    MAX_FLAG="--max-tasks ${MAX_TASKS}"
fi

if [ "${SKIP_RUNS}" = false ]; then
    # Step 2: Run Bare agy Vanilla Baseline
    echo ""
    echo "[Step 2/5] Running BARE AGY Vanilla Baseline..."
    BARE_CMD=(python3 "${SCRIPT_DIR}/run_bare_agy.py" --config "${COHORT_CONFIG}" --output-dir "${RUNS_DIR}/cohort25_bare_agy")
    if [[ -n "${MAX_TASKS}" ]]; then BARE_CMD+=(--max-tasks "${MAX_TASKS}"); fi
    if [[ -n "${DRY_RUN}" ]]; then BARE_CMD+=(${DRY_RUN}); fi
    "${BARE_CMD[@]}"

    # Step 3: Run InBoost LongRun Accelerated agy
    echo ""
    echo "[Step 3/5] Running INBOOST LONGRUN Accelerated agy..."
    LONGRUN_CMD=(python3 "${SCRIPT_DIR}/run_inboost_longrun.py" --config "${COHORT_CONFIG}" --output-dir "${RUNS_DIR}/cohort25_inboost_longrun")
    if [[ -n "${MAX_TASKS}" ]]; then LONGRUN_CMD+=(--max-tasks "${MAX_TASKS}"); fi
    if [[ -n "${DRY_RUN}" ]]; then LONGRUN_CMD+=(${DRY_RUN}); fi
    "${LONGRUN_CMD[@]}"
else
    echo "[Step 2-3/5] Skipping task execution (--skip-runs specified)."
fi

# Step 4: Docker Verification on Bare agy
echo ""
echo "[Step 4/5] Running Docker Verification for Bare agy predictions..."
BARE_PREDS="${RUNS_DIR}/cohort25_bare_agy/predictions.jsonl"
BARE_EVAL_CMD=(python3 "${SCRIPT_DIR}/verify_docker.py" --predictions "${BARE_PREDS}" --config "${COHORT_CONFIG}")
if [[ -n "${MOCK_DOCKER}" ]]; then BARE_EVAL_CMD+=(${MOCK_DOCKER}); fi
"${BARE_EVAL_CMD[@]}"

# Step 5: Docker Verification on InBoost LongRun
echo ""
echo "[Step 5/5] Running Docker Verification for InBoost LongRun predictions..."
LONGRUN_PREDS="${RUNS_DIR}/cohort25_inboost_longrun/predictions.jsonl"
LONGRUN_EVAL_CMD=(python3 "${SCRIPT_DIR}/verify_docker.py" --predictions "${LONGRUN_PREDS}" --config "${COHORT_CONFIG}")
if [[ -n "${MOCK_DOCKER}" ]]; then LONGRUN_EVAL_CMD+=(${MOCK_DOCKER}); fi
"${LONGRUN_EVAL_CMD[@]}"

# Step 6: Generate Comparative Scorecard
echo ""
echo "======================================================================"
echo " Generating Comparative Scorecard & Analysis"
echo "======================================================================"
python3 "${SCRIPT_DIR}/compare_and_scorecard.py" \
    --bare-dir "${RUNS_DIR}/cohort25_bare_agy" \
    --longrun-dir "${RUNS_DIR}/cohort25_inboost_longrun" \
    --output-md "${RUNS_DIR}/SCORECARD.md" \
    --output-json "${RUNS_DIR}/comparison.json"

echo "Benchmark Pipeline Completed Successfully!"
