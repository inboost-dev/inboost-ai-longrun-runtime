#!/usr/bin/env bash
# ==============================================================================
# InBoost LongRun • SWE-bench Verified A/B Evaluation (pydata__xarray-7229)
# Minimal turnkey evaluation: Bare Agent vs Agent + InBoost LongRun MCP
# Supports Linux (x86_64/arm64) and macOS Darwin (Apple Silicon/Intel)
# ==============================================================================
set -euo pipefail

# Ensure standard system and package manager binary paths
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"

# Configurable agent CLI and workspace (can be overridden via CLI args or env vars)
AGENT_CMD="${AGENT_CMD:-agy}"
WORKSPACE_DIR="${WORKSPACE_DIR:-${PROJECT_ROOT}/demo-workspace/01_xarray}"

# Parse command-line arguments (supports flags, positional args, or help)
while [[ $# -gt 0 ]]; do
  case "$1" in
    -a|--agent)
      AGENT_CMD="$2"
      shift 2
      ;;
    --agent=*)
      AGENT_CMD="${1#*=}"
      shift 1
      ;;
    -w|--workspace)
      WORKSPACE_DIR="$2"
      shift 2
      ;;
    --workspace=*)
      WORKSPACE_DIR="${1#*=}"
      shift 1
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS] [AGENT_CMD] [WORKSPACE_DIR]"
      echo ""
      echo "Options:"
      echo "  -a, --agent <cmd>       Agent CLI command (default: agy, e.g. agy, claude)"
      echo "  -w, --workspace <dir>   Workspace directory for evaluation runs"
      echo "  -h, --help              Show this help message"
      echo ""
      echo "Examples:"
      echo "  bash $0"
      echo "  bash $0 claude"
      echo "  bash $0 --agent agy"
      echo "  bash $0 --agent claude --workspace /tmp/eval_xarray"
      exit 0
      ;;
    *)
      if [[ "$1" == *"/"* || -d "$1" ]]; then
        WORKSPACE_DIR="$1"
      else
        AGENT_CMD="$1"
      fi
      shift 1
      ;;
  esac
done

# Validate agent CLI availability (auto-detect fallback if default 'agy' is not installed)
if ! command -v "$AGENT_CMD" >/dev/null 2>&1; then
  if [[ "$AGENT_CMD" == "agy" ]] && command -v claude >/dev/null 2>&1; then
    echo "Notice: 'agy' not found in PATH. Auto-detected 'claude' — using 'claude'."
    AGENT_CMD="claude"
  else
    echo "==================================================================" >&2
    echo "❌ Error: Agent CLI '${AGENT_CMD}' not found in PATH" >&2
    echo "==================================================================" >&2
    echo "To run this evaluation, please install an AI coding agent CLI:" >&2
    echo "  • Antigravity (agy): npm install -g @google/antigravity" >&2
    echo "  • Claude Code:      npm install -g @anthropic-ai/claude-code" >&2
    echo "" >&2
    echo "Or specify an installed agent CLI on your machine:" >&2
    echo "  bash $0 --agent <cmd>    # e.g. bash $0 --agent claude" >&2
    echo "  AGENT_CMD=<cmd> bash $0" >&2
    echo "==================================================================" >&2
    exit 1
  fi
fi

ARM_BARE="${WORKSPACE_DIR}/arm_bare"
ARM_LONGRUN="${WORKSPACE_DIR}/arm_longrun"
REPO_SOURCE="${WORKSPACE_DIR}/repo_source"
TASK_COMMIT="3aa75c8d00a4a2d4acf10d80f76b937cadb666b7"
TEST_COMMIT="675a3ff6d9fc52fde73d356345848e89a4705aaf"

echo "Evaluation Agent:    ${AGENT_CMD}"
echo "Workspace Directory: ${WORKSPACE_DIR}"

TASK_PROMPT="You are resolving an issue in pydata/xarray.

Issue Description:
\`xr.where(..., keep_attrs=True)\` overwrites coordinate attributes
### What happened?

#6461 had some unintended consequences for \`xr.where(..., keep_attrs=True)\`, where coordinate attributes are getting overwritten by variable attributes. I guess this has been broken since \`2022.06.0\`.

### What did you expect to happen?

Coordinate attributes should be preserved.

### Minimal Complete Verifiable Example

\`\`\`Python
import xarray as xr
ds = xr.tutorial.load_dataset(\"air_temperature\")
xr.where(True, ds.air, ds.air, keep_attrs=True).time.attrs
\`\`\`

Please investigate the root cause, modify the appropriate source files, and produce a clean unified git diff that resolves the issue. Do not leave empty edits or unfinished blocks."

# Helper functions for MCP server registration across agents (agy, claude, etc.)
disable_mcp_server() {
  local agent="$1"
  local server_name="$2"
  if command -v "$agent" >/dev/null 2>&1; then
    "$agent" mcp disable "$server_name" 2>/dev/null \
      || "$agent" mcp remove "$server_name" 2>/dev/null \
      || true
  fi
}

enable_mcp_server() {
  local agent="$1"
  local server_name="$2"
  local binary="$3"

  # Clear macOS quarantine flags on binary if present
  if command -v xattr >/dev/null 2>&1 && [[ -f "$binary" ]]; then
    xattr -d com.apple.quarantine "$binary" 2>/dev/null || true
  fi

  if command -v "$agent" >/dev/null 2>&1; then
    "$agent" mcp add "$server_name" "$binary" mcp 2>/dev/null \
      || "$agent" mcp add "$server_name" "$binary" -- mcp 2>/dev/null \
      || true
    "$agent" mcp enable "$server_name" 2>/dev/null || true
  fi
}

# 1. Clone repository & checkout official SWE-bench Verified test suite
mkdir -p "$WORKSPACE_DIR"
if [[ ! -d "$REPO_SOURCE" ]]; then
  for cand in \
    "${PROJECT_ROOT}/demo-workspace/01_xarray/repo_source" \
    "${PROJECT_ROOT}/../inboost-ai-longrun/demo-workspace/01_xarray/repo_source" \
    "${PROJECT_ROOT}/../inboost-ai-longrun-runtime/demo-workspace/01_xarray/repo_source"; do
    if [[ -d "$cand/.git" ]]; then
      cp -R "$cand" "$REPO_SOURCE"
      break
    fi
  done
  if [[ ! -d "$REPO_SOURCE" ]]; then
    echo "Cloning pydata/xarray at commit ${TASK_COMMIT}..."
    mkdir -p "$REPO_SOURCE"
    git -C "$REPO_SOURCE" init -q
    git -C "$REPO_SOURCE" remote add origin https://github.com/pydata/xarray.git 2>/dev/null || true
    git -C "$REPO_SOURCE" fetch --depth 1 origin "$TASK_COMMIT"
    git -C "$REPO_SOURCE" checkout -q FETCH_HEAD
    git -C "$REPO_SOURCE" fetch --depth 1 origin "$TEST_COMMIT"
    git -C "$REPO_SOURCE" checkout "$TEST_COMMIT" -- xarray/tests/test_computation.py
    git -C "$REPO_SOURCE" -c user.name="InBoost Evaluation" -c user.email="eval@inboost.pro" commit -qm "test: official issue #7229 verification suite" || true
  fi
fi

# Prepare isolated directories for Arm A and Arm B
rm -rf "$ARM_BARE" "$ARM_LONGRUN"
cp -R "$REPO_SOURCE" "$ARM_BARE"
cp -R "$REPO_SOURCE" "$ARM_LONGRUN"

# 2. Arm A: Bare agent (without InBoost LongRun MCP)
echo "=================================================================="
echo "▶ [1/4] Running Arm A: Bare ${AGENT_CMD}"
echo "=================================================================="
disable_mcp_server "$AGENT_CMD" "inboost-longrun"
(cd "$ARM_BARE" && "$AGENT_CMD" -p "$TASK_PROMPT" --dangerously-skip-permissions) || true

# 3. Configure and enable InBoost LongRun MCP (auto-detects OS & Arch)
echo "=================================================================="
echo "▶ [2/4] Configuring InBoost LongRun MCP"
echo "=================================================================="
OS="$(uname -s 2>/dev/null || echo "Linux")"
ARCH="$(uname -m 2>/dev/null || echo "x86_64")"
LONGRUN_CMD="$(command -v inboost-longrun 2>/dev/null || true)"

if [[ -z "$LONGRUN_CMD" ]]; then
  if [[ "$OS" == "Darwin" ]]; then
    if [[ "$ARCH" == "arm64" && -x "${PROJECT_ROOT}/bin/inboost-longrun-darwin-arm64" ]]; then
      LONGRUN_CMD="${PROJECT_ROOT}/bin/inboost-longrun-darwin-arm64"
    elif [[ -x "${PROJECT_ROOT}/bin/inboost-longrun-darwin" ]]; then
      LONGRUN_CMD="${PROJECT_ROOT}/bin/inboost-longrun-darwin"
    fi
  else
    if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]] && [[ -x "${PROJECT_ROOT}/bin/inboost-longrun-arm64" ]]; then
      LONGRUN_CMD="${PROJECT_ROOT}/bin/inboost-longrun-arm64"
    elif [[ -x "${PROJECT_ROOT}/bin/inboost-longrun" ]]; then
      LONGRUN_CMD="${PROJECT_ROOT}/bin/inboost-longrun"
    fi
  fi
  LONGRUN_CMD="${LONGRUN_CMD:-${PROJECT_ROOT}/bin/inboost-longrun}"
fi

enable_mcp_server "$AGENT_CMD" "inboost-longrun" "$LONGRUN_CMD"

# 4. Arm B: agent with InBoost LongRun MCP
echo "=================================================================="
echo "▶ [3/4] Running Arm B: ${AGENT_CMD} + InBoost LongRun"
echo "=================================================================="
(cd "$ARM_LONGRUN" && "$AGENT_CMD" -p "$TASK_PROMPT" --dangerously-skip-permissions) || true

# 5. Statistics
echo "=================================================================="
echo "▶ [4/4] Statistics & Diff Comparison"
echo "=================================================================="
echo "--- Arm A (Bare ${AGENT_CMD}) Diff ---"
git -C "$ARM_BARE" diff --stat || true
echo ""
echo "--- Arm B (InBoost LongRun) Diff ---"
git -C "$ARM_LONGRUN" diff --stat || true

# 6. Tests (standard pytest execution of official SWE-bench FAIL_TO_PASS test)
echo "=================================================================="
echo "▶ Running Verification Tests"
echo "=================================================================="
run_test() {
  python3 -m pytest xarray/tests/test_computation.py -k test_where_attrs -q
}

echo "--- Arm A (Bare ${AGENT_CMD}) Tests ---"
(cd "$ARM_BARE" && run_test) || true
echo ""
echo "--- Arm B (InBoost LongRun) Tests ---"
(cd "$ARM_LONGRUN" && run_test) || true
