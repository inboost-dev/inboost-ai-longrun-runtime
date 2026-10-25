# Agent Operating Guidelines & Rules (AGENTS.md)
**Scope:** Repository-wide (`inboost-ai-longrun-runtime`)  
**Target:** AI Assistants, Antigravity, OpenHands, Claude, Cursor

---

## 1. Repository Purpose
`inboost-ai-longrun-runtime` is the standalone distribution repository for the evaluation edition of InBoost LongRun. It provides:
- Pre-compiled universal binaries (Linux amd64/arm64 static, macOS arm64/amd64, Windows amd64).
- Installation automation (`install.sh`, `install.ps1`).
- Agent MCP manifests and configuration templates.
- Evaluation license agreement and sample evaluation keys.

---

## 2. Invariants
1. **Zero Proprietary Source Exposure:** Do not commit proprietary engine source code or private signing keys into this repository.
2. **Privacy Guarantees:** Preserve the core privacy commitment: *"InBoost LongRun runs locally on CPU and never transmits code externally."*
3. **Commit Sign-Off:** Always sign off all commits using `git commit -s`.
4. **Platform Parity:** Ensure installer scripts maintain parity across Linux, macOS, and Windows.
