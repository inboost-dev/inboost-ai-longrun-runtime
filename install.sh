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

VERSION="${INBOOST_LONGRUN_VERSION:-0.1.0-eval}"
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

# 3. Determine install destination
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

# 4. Copy and set executable permissions
echo -e "Installing binary to ${COLOR_CYAN}${TARGET_BIN}${COLOR_RESET}..."
cp -f "$SOURCE_BIN" "$TARGET_BIN"
chmod 755 "$TARGET_BIN"

# 5. License installation
if [ -f "${SCRIPT_DIR}/inboost.lic" ]; then
  cp -f "${SCRIPT_DIR}/inboost.lic" "${INBOOST_HOME}/inboost.lic"
  chmod 644 "${INBOOST_HOME}/inboost.lic"
  echo -e "License installed to ${COLOR_CYAN}${INBOOST_HOME}/inboost.lic${COLOR_RESET}"
fi

# 6. Verify PATH
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

# 7. Verification test
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
echo -e "Binary path:  ${COLOR_BOLD}${TARGET_BIN}${COLOR_RESET}"
echo -e "License path: ${COLOR_BOLD}${INBOOST_HOME}/inboost.lic${COLOR_RESET}"
echo -e "Privacy:      ${COLOR_GREEN}InBoost LongRun выполняется локально и не передает код вовне.${COLOR_RESET}"
echo ""
echo -e "To integrate with your AI agent:"
echo -e "  • Claude Code:  claude mcp add inboost-longrun -- inboost-longrun serve"
echo -e "  • Antigravity:  agy mcp add inboost-longrun inboost-longrun serve"
echo -e "  • Cursor:       Add inboost-longrun to .cursor/mcp.json"
if [ "$PATH_UPDATED" -eq 1 ]; then
  echo ""
  echo -e "${COLOR_YELLOW}Note: Restart your terminal session or run: export PATH=\"\$PATH:${INSTALL_DIR}\"${COLOR_RESET}"
fi
