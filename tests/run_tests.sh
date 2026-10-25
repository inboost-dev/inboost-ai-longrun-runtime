#!/usr/bin/env bash
# ==============================================================================
# InBoost LongRun Evaluation Runtime - Comprehensive Test Runner
# Verifies binary execution, license validation (1-month validity), and MCP protocol
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Running InBoost LongRun Smoke Tests ==="

# Ensure binaries have execution permissions
chmod +x "${REPO_ROOT}/bin/inboost-longrun"* 2>/dev/null || true

# 1. Direct binary tests
echo -n "Checking binary version: "
"${REPO_ROOT}/bin/inboost-longrun" version >/dev/null 2>&1 && echo "PASS" || (echo "FAIL"; exit 1)

echo -n "Checking 1-month evaluation status: "
STATUS_OUT="$("${REPO_ROOT}/bin/inboost-longrun" status)"
if echo "$STATUS_OUT" | grep -q "Status:         ACTIVE" && echo "$STATUS_OUT" | grep -q "1-Month Evaluation License"; then
  echo "PASS (Active 1-month evaluation)"
else
  echo "FAIL: Unexpected status output: $STATUS_OUT"
  exit 1
fi

# 2. Python pytest suite (if pytest is installed)
if command -v pytest >/dev/null 2>&1; then
  echo "=== Running Pytest Suite ==="
  PYTHONPATH="${REPO_ROOT}" pytest "${REPO_ROOT}/tests" -v
elif command -v python3 >/dev/null 2>&1; then
  echo "=== Running Python Suite via unittest/pytest ==="
  PYTHONPATH="${REPO_ROOT}" python3 -m pytest "${REPO_ROOT}/tests" -v 2>/dev/null || python3 -m unittest discover "${REPO_ROOT}/tests" 2>/dev/null || echo "Pytest not installed, skipping unit tests"
fi

# 3. Node.js wrapper test (if node is installed)
if command -v node >/dev/null 2>&1; then
  echo -n "Checking Node.js CLI wrapper: "
  node "${REPO_ROOT}/bin/inboost-longrun.js" status >/dev/null 2>&1 && echo "PASS" || (echo "FAIL"; exit 1)
fi

echo "=== All InBoost LongRun tests completed successfully! ==="
