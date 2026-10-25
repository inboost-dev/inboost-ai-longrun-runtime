# Getting Started & Interactive Examples
## InBoost LongRun Evaluation Runtime (`inboost-longrun`)

> **Purpose:** 2-minute quickstart, host CPU offload tools (0 tokens billed), MCP server for Claude Code, Cursor, and Antigravity, and live reproduction of SWE-bench Verified gold-standard tasks.  
> **Official Domain:** `https://inboost.pro` • **License:** [InBoost LongRun Evaluation License](LICENSE)

---

## ⚡ 2-Minute Quickstart (Zero-Friction Setup)

InBoost LongRun runs directly on your local workstation and requires no external orchestration:

### Option A. Instant Initialization via `npx` (No Pre-Installation)
```bash
# Automatically configure agent rules for Claude Code, Cursor, and Antigravity
npx @inboost-pro/inboost-longrun init

# Verify host environment, system tool dependencies, and evaluation license
npx @inboost-pro/inboost-longrun doctor
```

### Option B. Installation via Python pip or npm
```bash
# Via Python pip
pip install inboost-longrun
inboost-longrun init
inboost-longrun doctor

# Or via global npm
npm install -g @inboost-pro/inboost-longrun
inboost-longrun init
inboost-longrun doctor
```

The `init` command automatically:
1. Registers optimization directives in `~/.claude/rules/inboost_longrun.md` and `.cursorrules`.
2. Connects the `inboost-longrun` MCP server inside `.cursor/mcp.json`.
3. Establishes surgical diff budgets ($\le 180$ lines) and AST Guard syntax integrity directives.

---

## 🎮 Example 1: Reproducing SWE-bench Verified Solution (`pydata__xarray-7229`)

Execute automated turnkey A/B evaluation of `pydata__xarray-7229` comparing Bare Agent vs InBoost-accelerated Agent in a single command (works out of the box on Linux & macOS):

```bash
# Run with default agent (agy):
bash examples/eval_ab.sh

# Or specify any agent CLI (e.g. claude, agy):
bash examples/eval_ab.sh claude
# Or via explicit flag:
bash examples/eval_ab.sh --agent claude
```

| Metric / Behavior | Bare Vanilla Agent | Agent with InBoost LongRun |
| :--- | :--- | :--- |
| **Total Prompt Tokens** | 21,733 tokens (verbose exploratory reads) | **3,225 tokens (6.7x token compression)** |
| **GPU Occupancy / Latency** | 112.8 seconds | **35.0 seconds (3.2x faster)** |
| **Host CPU Token Crusher** | 0 tokens crushed | **28,400 tokens crushed locally (< 1 ms)** |
| **Verification Test Suite** | ❌ FAILED | ✅ **PASSED (100% test assertions green in 0.7s)** |

---

## 🎮 Example 2: IDE & Agent Integration (Cursor, Claude Code, Antigravity)

### Cursor IDE Integration
The MCP server is registered automatically in `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "inboost-longrun": {
      "command": "inboost-longrun",
      "args": ["mcp"]
    }
  }
}
```

### Claude Code CLI Integration
Configure Claude Code rules in `~/.claude/rules/inboost_longrun.md`:
```markdown
# InBoost LongRun Operating Rules
1. Zero Context Bloat: Before reading source files (>100 lines), ALWAYS invoke l0_view_outline.
2. AST Symbol Pinpoint: Use l0_read_symbol to inspect targeted methods without reading whole files.
3. Surgical Diff Budget: Keep patch surgical (<20 lines churn, max 180 lines).
4. Syntax Pre-Validation: Validate AST with l0_verify_syntax before generating patch.
5. Traceback Offload: Filter test failures via TracebackCrusher (<15ms host CPU).
```

---

## 🔗 Related Documentation
- 📊 **[Benchmark Publication Guidelines](BENCHMARKS.md)**: Zero-hallucination standards, Docker CI scoring, and official scorecards across 500 tasks.
- 📜 **[Evaluation License Agreement](LICENSE)**: Evaluation license terms and non-commercial evaluation boundaries.
- 🌐 **[Official Platform Portal](https://inboost.pro)**: Product downloads and commercial enterprise licenses.
