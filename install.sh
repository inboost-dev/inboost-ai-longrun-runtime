#!/usr/bin/env bash
# ==============================================================================
# InBoost LongRun Evaluation Runtime - Universal Installer
# Supports: Linux (x86_64 & arm64 static), macOS (Apple Silicon & Intel)
# Privacy:  Runs 100% locally on your machine. Does not transmit code externally.
# ==============================================================================
set -euo pipefail

COLOR_RESET="\033[0m"
COLOR_CYAN="\033[1;36m"
COLOR_GREEN="\033[1;32m"
COLOR_YELLOW="\033[1;33m"
COLOR_RED="\033[1;31m"
COLOR_BOLD="\033[1m"

VERSION="${INBOOST_LONGRUN_VERSION:-0.3.0-eval}"
GITHUB_REPO="inboost-dev/inboost-ai-longrun-runtime"

echo -e "${COLOR_CYAN}┌────────────────────────────────────────────────────────┐${COLOR_RESET}"
echo -e "${COLOR_CYAN}│     InBoost LongRun Evaluation Runtime Installer       │${COLOR_RESET}"
echo -e "${COLOR_CYAN}│     Local Offload & Verification Engine for AI Agents  │${COLOR_RESET}"
echo -e "${COLOR_CYAN}│     Privacy: 100% Local Execution                      │${COLOR_RESET}"
echo -e "${COLOR_CYAN}└────────────────────────────────────────────────────────┘${COLOR_RESET}"

# 1. Detect OS
OS_RAW="$(uname -s 2>/dev/null || echo "unknown")"
case "$(echo "$OS_RAW" | tr '[:upper:]' '[:lower:]')" in
  darwin*)
    OS_NAME="macos"
    OS_FAMILY="darwin"
    ;;
  linux*)
    OS_NAME="linux"
    OS_FAMILY="linux"
    ;;
  *)
    echo -e "${COLOR_RED}Error: Unsupported operating system: ${OS_RAW}${COLOR_RESET}"
    echo "For Windows, please use the PowerShell installer (install.ps1)."
    exit 1
    ;;
esac

# 2. Detect Architecture
ARCH_RAW="$(uname -m 2>/dev/null || echo "unknown")"
case "$ARCH_RAW" in
  x86_64|amd64)
    ARCH_NAME="amd64"
    ARCH_LABEL="x86_64 / Intel / AMD"
    ;;
  arm64|aarch64)
    ARCH_NAME="arm64"
    ARCH_LABEL="Apple Silicon / ARM64"
    ;;
  *)
    echo -e "${COLOR_RED}Error: Unsupported architecture: ${ARCH_RAW}${COLOR_RESET}"
    exit 1
    ;;
esac

echo -e "Platform detected: ${COLOR_GREEN}${OS_NAME}${COLOR_RESET} (${ARCH_LABEL})"

# 3. Pre-flight dependency check for Local Offload
echo -e "\n${COLOR_BOLD}Checking system dependencies for Local Offload:${COLOR_RESET}"

MANDATORY_TOOLS=("find" "grep" "diff" "patch" "git" "python3")
MISSING_MANDATORY=()

map_to_packages() {
  local pkgs=()
  for t in "$@"; do
    case "$t" in
      find) pkgs+=("findutils") ;;
      diff) pkgs+=("diffutils") ;;
      *) pkgs+=("$t") ;;
    esac
  done
  echo "${pkgs[*]}"
}

for tool in "${MANDATORY_TOOLS[@]}"; do
  if command -v "$tool" >/dev/null 2>&1; then
    TOOL_PATH="$(command -v "$tool")"
    echo -e "  [${COLOR_GREEN}✓${COLOR_RESET}] ${tool} (${TOOL_PATH})"
  else
    echo -e "  [${COLOR_RED}✗${COLOR_RESET}] ${tool} (missing)"
    MISSING_MANDATORY+=("$tool")
  fi
done

RECOMMENDED_TOOLS=("ast-grep:sg" "ruff" "biome" "docker")
for item in "${RECOMMENDED_TOOLS[@]}"; do
  IFS=":" read -r primary fallback <<< "$item"
  if command -v "$primary" >/dev/null 2>&1; then
    echo -e "  [${COLOR_GREEN}✓${COLOR_RESET}] ${primary} ($(command -v "$primary")) [recommended acceleration]"
  elif [ -n "${fallback:-}" ] && command -v "$fallback" >/dev/null 2>&1; then
    echo -e "  [${COLOR_GREEN}✓${COLOR_RESET}] ${primary} (via ${fallback}: $(command -v "$fallback")) [recommended acceleration]"
  else
    echo -e "  [${COLOR_YELLOW}○${COLOR_RESET}] ${primary} (optional, recommended for <2ms local linting)"
  fi
done

echo -e "\n${COLOR_BOLD}Checking AI Coding Agents & IDEs:${COLOR_RESET}"
AGENTS=("Claude Code:claude:claude mcp add inboost-longrun -- inboost-longrun serve" \
        "Google Antigravity:agy:agy mcp add inboost-longrun inboost-longrun serve" \
        "Cursor IDE:cursor:inboost-longrun init (configures .cursor/mcp.json)" \
        "VS Code:code:add to .vscode/mcp.json or workspace rules")

for agent_def in "${AGENTS[@]}"; do
  IFS=":" read -r name cmd hint <<< "$agent_def"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo -e "  [${COLOR_GREEN}✓${COLOR_RESET}] ${name} ($(command -v "$cmd"))\n       Integration: ${hint}"
  elif [ "$cmd" = "cursor" ] && ([ -d "${HOME}/.cursor" ] || [ -d "./.cursor" ]); then
    echo -e "  [${COLOR_GREEN}✓${COLOR_RESET}] ${name} (detected via .cursor/ directory)\n       Integration: ${hint}"
  else
    echo -e "  [${COLOR_YELLOW}○${COLOR_RESET}] ${name} (optional, not found in PATH)"
  fi
done

if [ ${#MISSING_MANDATORY[@]} -gt 0 ]; then
  SUGGESTED_PKGS="$(map_to_packages "${MISSING_MANDATORY[@]}")"
  echo -e "\n${COLOR_RED}Error: Required tools missing for InBoost LongRun Local Offload: ${MISSING_MANDATORY[*]}${COLOR_RESET}"
  echo "InBoost LongRun requires these tools locally to inspect outlines, calculate AST diffs, and filter test traces."
  echo "Please install the missing packages before proceeding:"
  if [ "$OS_NAME" = "macos" ]; then
    echo -e "  ${COLOR_CYAN}brew install ${SUGGESTED_PKGS}${COLOR_RESET}"
  elif command -v apt-get >/dev/null 2>&1; then
    echo -e "  ${COLOR_CYAN}sudo apt-get update && sudo apt-get install -y ${SUGGESTED_PKGS}${COLOR_RESET}"
  elif command -v dnf >/dev/null 2>&1; then
    echo -e "  ${COLOR_CYAN}sudo dnf install -y ${SUGGESTED_PKGS}${COLOR_RESET}"
  elif command -v apk >/dev/null 2>&1; then
    echo -e "  ${COLOR_CYAN}sudo apk add ${SUGGESTED_PKGS}${COLOR_RESET}"
  elif command -v pacman >/dev/null 2>&1; then
    echo -e "  ${COLOR_CYAN}sudo pacman -S ${SUGGESTED_PKGS}${COLOR_RESET}"
  elif command -v zypper >/dev/null 2>&1; then
    echo -e "  ${COLOR_CYAN}sudo zypper install -y ${SUGGESTED_PKGS}${COLOR_RESET}"
  else
    echo -e "  Install packages: ${SUGGESTED_PKGS}"
  fi

  if [ "${INBOOST_IGNORE_MISSING_DEPS:-0}" != "1" ]; then
    echo -e "\n${COLOR_YELLOW}To bypass this check (not recommended), set INBOOST_IGNORE_MISSING_DEPS=1${COLOR_RESET}"
    exit 1
  else
    echo -e "\n${COLOR_YELLOW}Proceeding anyway (INBOOST_IGNORE_MISSING_DEPS=1 is set)...${COLOR_RESET}"
  fi
else
  echo -e "${COLOR_GREEN}✓ All core offload tools verified.${COLOR_RESET}\n"
fi

# 4. Determine install destination
if [ "${EUID:-$(id -u)}" -eq 0 ] || [ -w "/usr/local/bin" ]; then
  INSTALL_DIR="/usr/local/bin"
else
  INSTALL_DIR="${HOME}/.local/bin"
  mkdir -p "$INSTALL_DIR"
fi
TARGET_BIN="${INSTALL_DIR}/inboost-longrun"

# Prepare config and license directory
INBOOST_HOME="${HOME}/.inboost"
mkdir -p "$INBOOST_HOME"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"
SOURCE_BIN=""

# Check if running from cloned repository
if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/bin" ]; then
  if [ "$OS_FAMILY" = "darwin" ]; then
    CANDIDATE="$SCRIPT_DIR/bin/inboost-longrun-darwin-${ARCH_NAME}"
  else
    CANDIDATE="$SCRIPT_DIR/bin/inboost-longrun-linux-${ARCH_NAME}"
  fi

  if [ -f "$CANDIDATE" ]; then
    SOURCE_BIN="$CANDIDATE"
    echo -e "Found local binary: ${COLOR_CYAN}${SOURCE_BIN}${COLOR_RESET}"
  fi
fi

# If no local binary found, download archive
if [ -z "$SOURCE_BIN" ]; then
  echo -e "Downloading pre-compiled binary for ${OS_NAME}-${ARCH_NAME}..."
  TMP_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t 'inboost')"
  trap 'rm -rf "$TMP_DIR"' EXIT

  ARCHIVE_NAME=""
  if [ "$OS_FAMILY" = "darwin" ]; then
    ARCHIVE_NAME="inboost-longrun-macos.tar.gz"
  elif [ "$ARCH_NAME" = "amd64" ]; then
    ARCHIVE_NAME="inboost-longrun-linux-x86_64.tar.gz"
  else
    ARCHIVE_NAME="inboost-longrun-linux-arm64.tar.gz"
  fi

  DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/releases/download/v${VERSION}/${ARCHIVE_NAME}"
  ARCHIVE_PATH="${TMP_DIR}/${ARCHIVE_NAME}"

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$DOWNLOAD_URL" -o "$ARCHIVE_PATH" || {
      echo -e "${COLOR_RED}Failed to download from ${DOWNLOAD_URL}${COLOR_RESET}"
      exit 1
    }
  elif command -v wget >/dev/null 2>&1; then
    wget -q "$DOWNLOAD_URL" -O "$ARCHIVE_PATH" || {
      echo -e "${COLOR_RED}Failed to download from ${DOWNLOAD_URL}${COLOR_RESET}"
      exit 1
    }
  else
    echo -e "${COLOR_RED}Error: Neither curl nor wget was found.${COLOR_RESET}"
    exit 1
  fi

  tar -xzf "$ARCHIVE_PATH" -C "$TMP_DIR"
  if [ "$OS_FAMILY" = "darwin" ]; then
    SOURCE_BIN="${TMP_DIR}/inboost-longrun-darwin-${ARCH_NAME}"
  else
    SOURCE_BIN="${TMP_DIR}/inboost-longrun-linux-${ARCH_NAME}"
  fi

  # Copy license if packaged inside archive
  if [ -f "${TMP_DIR}/inboost.lic" ]; then
    cp -f "${TMP_DIR}/inboost.lic" "${INBOOST_HOME}/inboost.lic"
  fi
fi

# 5. Copy and set executable permissions
echo -e "Installing binary to ${COLOR_CYAN}${TARGET_BIN}${COLOR_RESET}..."
cp -f "$SOURCE_BIN" "$TARGET_BIN"
chmod 755 "$TARGET_BIN"

# 6. License installation
if [ -f "${SCRIPT_DIR}/inboost.lic" ]; then
  cp -f "${SCRIPT_DIR}/inboost.lic" "${INBOOST_HOME}/inboost.lic"
  chmod 644 "${INBOOST_HOME}/inboost.lic"
  echo -e "License installed to ${COLOR_CYAN}${INBOOST_HOME}/inboost.lic${COLOR_RESET}"
fi

# 7. Verify PATH
PATH_UPDATED=0
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
  echo -e "${COLOR_YELLOW}Warning: ${INSTALL_DIR} is not in your current PATH.${COLOR_RESET}"
  for RC_FILE in "${HOME}/.bashrc" "${HOME}/.zshrc" "${HOME}/.profile"; do
    if [ -f "$RC_FILE" ]; then
      if ! grep -q "$INSTALL_DIR" "$RC_FILE" 2>/dev/null; then
        echo "export PATH=\"\$PATH:${INSTALL_DIR}\"" >> "$RC_FILE"
        PATH_UPDATED=1
        echo -e "Added ${INSTALL_DIR} to ${COLOR_CYAN}${RC_FILE}${COLOR_RESET}"
      fi
    fi
  done
fi

# 8. Verification test
echo -e "\n${COLOR_BOLD}Verifying installation:${COLOR_RESET}"
if "$TARGET_BIN" version >/dev/null 2>&1; then
  "$TARGET_BIN" version
  echo -e "${COLOR_GREEN}✓ InBoost LongRun binary verified successfully!${COLOR_RESET}\n"
else
  echo -e "${COLOR_RED}✗ Verification failed for ${TARGET_BIN}${COLOR_RESET}"
  exit 1
fi

echo -e "${COLOR_GREEN}========================================================${COLOR_RESET}"
echo -e "${COLOR_GREEN}Installation completed successfully!${COLOR_RESET}"
echo -e "${COLOR_GREEN}========================================================${COLOR_RESET}"
echo -e "Binary path:   ${COLOR_BOLD}${TARGET_BIN}${COLOR_RESET}"
echo -e "License path:  ${COLOR_BOLD}${INBOOST_HOME}/inboost.lic${COLOR_RESET}"
echo -e "Offload Tools: ${COLOR_GREEN}find, grep, diff, patch, git, python3 (Ready)${COLOR_RESET}"
echo -e "Privacy:       ${COLOR_GREEN}InBoost LongRun выполняется локально и не передает код вовне.${COLOR_RESET}"
echo ""
echo -e "To integrate with your AI agent:"
echo -e "  • Claude Code:  claude mcp add inboost-longrun -- inboost-longrun serve"
echo -e "  • Antigravity:  agy mcp add inboost-longrun inboost-longrun serve"
echo -e "  • Cursor:       Add inboost-longrun to .cursor/mcp.json"
if [ "$PATH_UPDATED" -eq 1 ]; then
  echo ""
  echo -e "${COLOR_YELLOW}Note: Restart your terminal session or run: export PATH=\"\$PATH:${INSTALL_DIR}\"${COLOR_RESET}"
fi
