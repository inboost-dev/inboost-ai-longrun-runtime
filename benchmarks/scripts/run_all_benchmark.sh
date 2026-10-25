#!/usr/bin/env bash
# ==============================================================================
# InBoost AI LongRun vs Bare: Master Benchmark & Docker Verification Suite
# ==============================================================================
# Evaluates Google Antigravity (`agy`) in Bare mode vs InBoost LongRun
# across SWE-bench Verified cohorts (50 cohorts x 10 tasks = N=500).
#
# Usage:
#   ./run_all_benchmark.sh --audit
#   ./run_all_benchmark.sh --cohort 1 [--dry-run]
#   ./run_all_benchmark.sh --all [--dry-run]
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCHMARKS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_DIR="${BENCHMARKS_DIR}/configs"
RUNS_DIR="${BENCHMARKS_DIR}/runs"
COHORT_CONFIG="${CONFIG_DIR}/swebench_cohort_25_random.json"

SEED="42"
MAX_TASKS=""
DRY_RUN=""
SKIP_RUNS=false
MOCK_DOCKER=""
CHUNK_NUM=""
CUSTOM_CONFIG=""
CUSTOM_PREFIX=""

SEQUENTIAL_DOCKER=false
TIMEOUT="1200"

COHORT_NUM=""
RUN_ALL_COHORTS=false
DO_AUDIT=false

function print_usage() {
    cat <<EOF
Usage: ./run_all_benchmark.sh [OPTIONS]

Options:
  --audit             Run instant offline audit and verification across all 50 cohorts (N=500)
  --all               Execute benchmark pipeline across all 50 cohorts sequentially
  --cohort <1-50>     Run a registered cohort by number (default: 1)
  --config <path>     Path to custom cohort JSON config
  --output-prefix <str> Directory prefix for run outputs (default: cohort_0N)
  --seed <int>        Random seed for cohort sampling (default: 42)
  --max-tasks <int>   Limit execution to N tasks per cohort (e.g. 5, default: all tasks in config)
  --timeout <int>     Per-task timeout in seconds (default: 1200, 20 minutes)
  --dry-run           Execute in synthetic/simulation mode (no API tokens or heavy GPU compute)
  --mock-docker       Force mock/structural Docker verification (useful if docker daemon is restricted)
  --sequential-docker Run Docker verifications sequentially instead of parallel (default: parallel)
  --skip-runs         Skip task execution and jump straight to Docker verification & scorecard
  -h, --help          Show this help message
EOF
}

# Parse command line flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        --audit)
            DO_AUDIT=true
            shift
            ;;
        --all)
            RUN_ALL_COHORTS=true
            shift
            ;;
        --cohort)
            COHORT_NUM="$2"
            shift 2
            ;;
        --chunk)
            CHUNK_NUM="$2"
            shift 2
            ;;
        --config)
            CUSTOM_CONFIG="$2"
            shift 2
            ;;
        --output-prefix)
            CUSTOM_PREFIX="$2"
            shift 2
            ;;
        --seed)
            SEED="$2"
            shift 2
            ;;
        --max-tasks)
            MAX_TASKS="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --mock-docker)
            MOCK_DOCKER="--mock"
            shift
            ;;
        --sequential-docker)
            SEQUENTIAL_DOCKER=true
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

if [ "${DO_AUDIT}" = true ]; then
    echo "Running instant offline audit across all 50 cohorts (N=500)..."
    python3 "${SCRIPT_DIR}/audit_swebench_500.py"
    exit $?
fi

COHORTS_DIR="${BENCHMARKS_DIR}/cohorts"

if [ "${RUN_ALL_COHORTS}" = true ]; then
    echo "======================================================================"
    echo " Executing Full SWE-bench Verified Benchmark Suite (Cohorts 01 - 50)"
    echo "======================================================================"
    for c in $(seq 1 50); do
        echo ">>> Launching Cohort ${c}/50..."
        ARGS=(--cohort "${c}" --timeout "${TIMEOUT}")
        if [[ -n "${DRY_RUN}" ]]; then ARGS+=(${DRY_RUN}); fi
        if [[ -n "${MAX_TASKS}" ]]; then ARGS+=(--max-tasks "${MAX_TASKS}"); fi
        if [[ -n "${MOCK_DOCKER}" ]]; then ARGS+=(${MOCK_DOCKER}); fi
        if [ "${SEQUENTIAL_DOCKER}" = true ]; then ARGS+=(--sequential-docker); fi
        if [ "${SKIP_RUNS}" = true ]; then ARGS+=(--skip-runs); fi
        "${SCRIPT_DIR}/run_all_benchmark.sh" "${ARGS[@]}"
    done
    echo ">>> All 50 cohorts finished! Running master audit..."
    python3 "${SCRIPT_DIR}/audit_swebench_500.py"
    exit 0
fi

if [[ -n "${COHORT_NUM}" ]]; then
    printf -v PADDED_COHORT "%02d" "${COHORT_NUM}"
    COHORT_CONFIG="${COHORTS_DIR}/cohort_${PADDED_COHORT}.json"
    RUN_PREFIX="cohort_${PADDED_COHORT}"
elif [[ -n "${CHUNK_NUM}" ]]; then
    COHORT_CONFIG="${CONFIG_DIR}/cohort50_chunk_${CHUNK_NUM}.json"
    RUN_PREFIX="cohort50_chunk_${CHUNK_NUM}"
elif [[ -n "${CUSTOM_CONFIG}" ]]; then
    COHORT_CONFIG="${CUSTOM_CONFIG}"
    RUN_PREFIX="${CUSTOM_PREFIX:-custom_run}"
else
    # Default to cohort 1 of 50
    COHORT_NUM=1
    printf -v PADDED_COHORT "%02d" "${COHORT_NUM}"
    COHORT_CONFIG="${COHORTS_DIR}/cohort_${PADDED_COHORT}.json"
    RUN_PREFIX="cohort_${PADDED_COHORT}"
    echo "[Info] No cohort specified; defaulting to Cohort 01 (use --cohort <1-50> or --all)."
fi

BARE_OUT="${RUNS_DIR}/${RUN_PREFIX}_bare_agy"
LONGRUN_OUT="${RUNS_DIR}/${RUN_PREFIX}_inboost_longrun"
SCORECARD_OUT_DIR="${RUNS_DIR}/${RUN_PREFIX}"

echo "======================================================================"
echo " InBoost LongRun vs Bare: SWE-bench Verified Benchmark"
echo "======================================================================"
echo " Directory:     ${SCRIPT_DIR}"
echo " Config:        ${COHORT_CONFIG}"
echo " Output Prefix: ${RUN_PREFIX}"
echo " Seed:          ${SEED}"
echo " Dry Run:       ${DRY_RUN:-No (Live agy Execution)}"
echo " Mock Docker:   ${MOCK_DOCKER:-Auto (Check daemon access)}"
echo "======================================================================"

# Step 1: Ensure Cohort Configuration Exists
if [[ ! -f "${COHORT_CONFIG}" ]]; then
    echo "Error: Cohort configuration not found at ${COHORT_CONFIG}"
    exit 1
else
    echo "[Step 1/3] Cohort configuration ready: ${COHORT_CONFIG}"
fi

MAX_FLAG=""
if [[ -n "${MAX_TASKS}" ]]; then
    MAX_FLAG="--max-tasks ${MAX_TASKS}"
fi

# ======================================================================
# Phase 1: Clean Dual-Arm Prediction Generation (Zero Docker Contention)
# ======================================================================
if [ "${SKIP_RUNS}" = false ]; then
    echo ""
    echo "[Phase 1/3 - Step 1/2] Generating BARE Predictions..."
    BARE_CMD=(python3 "${SCRIPT_DIR}/run_bare_agy.py" --config "${COHORT_CONFIG}" --output-dir "${BARE_OUT}" --timeout "${TIMEOUT}")
    if [[ -n "${MAX_TASKS}" ]]; then BARE_CMD+=(--max-tasks "${MAX_TASKS}"); fi
    if [[ -n "${DRY_RUN}" ]]; then BARE_CMD+=(${DRY_RUN}); fi
    "${BARE_CMD[@]}"

    echo ""
    echo "[Phase 1/3 - Step 2/2] Generating INBOOST LONGRUN Accelerated Predictions..."
    LONGRUN_CMD=(python3 "${SCRIPT_DIR}/run_inboost_longrun_agy.py" --config "${COHORT_CONFIG}" --output-dir "${LONGRUN_OUT}" --timeout "${TIMEOUT}")
    if [[ -n "${MAX_TASKS}" ]]; then LONGRUN_CMD+=(--max-tasks "${MAX_TASKS}"); fi
    if [[ -n "${DRY_RUN}" ]]; then LONGRUN_CMD+=(${DRY_RUN}); fi
    "${LONGRUN_CMD[@]}"

    echo ""
    echo "✓ Phase 1 Complete: Both candidate patch sets generated & immutable predictions sealed."
else
    echo "[Phase 1/3] Skipping patch generation (--skip-runs specified)."
fi

# ======================================================================
# Phase 2: Docker Test Verification (Equal 20-min Timeout)
# ======================================================================
echo ""
echo "======================================================================"
echo " [Phase 2/3] Docker Test Verification (Timeout: ${TIMEOUT}s / $((${TIMEOUT} / 60)) min)"
echo "======================================================================"
BARE_PREDS="${BARE_OUT}/predictions.jsonl"
LONGRUN_PREDS="${LONGRUN_OUT}/predictions.jsonl"

BARE_EVAL_CMD=(python3 "${SCRIPT_DIR}/verify_docker.py" --predictions "${BARE_PREDS}" --config "${COHORT_CONFIG}" --timeout "${TIMEOUT}")
if [[ -n "${MOCK_DOCKER}" ]]; then BARE_EVAL_CMD+=(${MOCK_DOCKER}); fi

LONGRUN_EVAL_CMD=(python3 "${SCRIPT_DIR}/verify_docker.py" --predictions "${LONGRUN_PREDS}" --config "${COHORT_CONFIG}" --timeout "${TIMEOUT}")
if [[ -n "${MOCK_DOCKER}" ]]; then LONGRUN_EVAL_CMD+=(${MOCK_DOCKER}); fi

if [ "${SEQUENTIAL_DOCKER}" = true ]; then
    echo "Running sequential Docker verification..."
    echo "[Bare Validation]"
    "${BARE_EVAL_CMD[@]}"
    echo ""
    echo "[InBoost LongRun Validation]"
    "${LONGRUN_EVAL_CMD[@]}"
else
    echo "Running PARALLEL Docker verification for Bare and InBoost LongRun..."
    "${BARE_EVAL_CMD[@]}" > "${BARE_OUT}/docker_eval.log" 2>&1 &
    PID_BARE=$!
    "${LONGRUN_EVAL_CMD[@]}" > "${LONGRUN_OUT}/docker_eval.log" 2>&1 &
    PID_LONGRUN=$!

    echo "  -> Bare Docker worker launched (PID: ${PID_BARE})"
    echo "  -> InBoost LongRun Docker worker launched (PID: ${PID_LONGRUN})"
    echo "Waiting for both Docker evaluations to complete..."
    wait "${PID_BARE}"
    wait "${PID_LONGRUN}"

    echo ""
    echo "--- Bare Docker Verification Results ---"
    cat "${BARE_OUT}/docker_eval.log"
    echo ""
    echo "--- InBoost LongRun Docker Verification Results ---"
    cat "${LONGRUN_OUT}/docker_eval.log"
fi

# Step 6: Generate Comparative Scorecard
echo ""
echo "======================================================================"
echo " Generating Comparative Scorecard & Analysis"
echo "======================================================================"
mkdir -p "${SCORECARD_OUT_DIR}"
python3 "${SCRIPT_DIR}/compare_and_scorecard.py" \
    --bare-dir "${BARE_OUT}" \
    --longrun-dir "${LONGRUN_OUT}" \
    --output-md "${SCORECARD_OUT_DIR}/SCORECARD.md" \
    --output-json "${SCORECARD_OUT_DIR}/comparison.json"

echo "Benchmark Pipeline Completed Successfully for ${RUN_PREFIX}!"
