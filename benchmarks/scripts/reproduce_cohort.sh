#!/usr/bin/env bash
# ==============================================================================
# InBoost LongRun: Cohort Reproduction & Verification Helper
# ==============================================================================
# Provides a simple, turnkey CLI for verifying or reproducing SWE-bench Verified
# cohorts (01 to 50) and running offline data audits.
#
# Examples:
#   ./reproduce_cohort.sh --audit           # Master audit of all 50 cohorts (N=500)
#   ./reproduce_cohort.sh 1                 # Run Cohort 01 full pipeline
#   ./reproduce_cohort.sh 1 --dry-run       # Run Cohort 01 in simulation mode
#   ./reproduce_cohort.sh 1 --skip-runs     # Run Docker verification only on existing patches
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <cohort_number_1_to_50 | --audit> [options]"
    echo ""
    echo "Examples:"
    echo "  $0 --audit             Audit all 50 cohorts offline (<1s, zero tokens)"
    echo "  $0 1                   Reproduce Cohort 01 live"
    echo "  $0 1 --dry-run         Simulate Cohort 01 (zero tokens/API)"
    echo "  $0 1 --skip-runs       Re-run Docker verification on existing patches"
    exit 1
fi

if [[ "$1" == "--audit" ]]; then
    python3 "${SCRIPT_DIR}/audit_swebench_500.py"
    exit $?
fi

# If first arg is a number, treat as cohort
COHORT_ID="$1"
shift

"${SCRIPT_DIR}/run_all_benchmark.sh" --cohort "${COHORT_ID}" "$@"
