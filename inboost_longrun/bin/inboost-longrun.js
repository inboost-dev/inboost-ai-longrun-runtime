#!/usr/bin/env node

/**
 * InBoost LongRun Evaluation Runtime — Universal Node CLI & npx Wrapper
 * 
 * Supports:
 *   npx inboost-longrun
 *   npx inboost-longrun status
 *   npx inboost-longrun init
 *   npx inboost-longrun serve
 *   npm install -g inboost-longrun
 */

const { spawn, spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const os = require("os");
const https = require("https");

const VERSION = "0.3.0-eval";
const GITHUB_REPO = "inboost-dev/inboost-longrun";

const RULES_CONTENT = `# InBoost LongRun Optimization Rules

1. **Context Conservation**: Before reading large files, use \`l0_view_outline\` to inspect declarations and structure.
2. **Test Failure Isolation**: Filter test logs and runtime exceptions via \`l0_clean_test_log\` to eliminate noise and isolate failing lines.
3. **Syntax Integrity**: Validate all code modifications and diffs with \`l0_verify_syntax\` prior to finalizing changes.
4. **Edit Scope Compliance**: Ensure edits remain focused and within budget. Verify with \`l0_verify_edit_scope\`.
5. **Execution Optimization**: Run test commands via \`l0_run_test\` for compact results. Check session economy with \`l0_savings_report\`.
`;

function getBinaryName() {
  const platform = process.platform;
  const arch = process.arch;

  if (platform === "linux") {
    if (arch === "x64") return "inboost-longrun-linux-amd64";
    if (arch === "arm64") return "inboost-longrun-linux-arm64";
  } else if (platform === "darwin") {
    if (arch === "arm64") return "inboost-longrun-darwin-arm64";
    if (arch === "x64") return "inboost-longrun-darwin-amd64";
  } else if (platform === "win32") {
    if (arch === "x64") return "inboost-longrun-windows-amd64.exe";
  }

  throw new Error(`Unsupported platform: ${platform} ${arch}`);
}

function ensureLicenseInstalled(packageDir) {
  const inboostHome = path.join(os.homedir(), ".inboost");
  if (!fs.existsSync(inboostHome)) {
    try { fs.mkdirSync(inboostHome, { recursive: true }); } catch (e) {}
  }
  const targetLic = path.join(inboostHome, "inboost.lic");
  if (!fs.existsSync(targetLic)) {
    const candidates = [
      path.join(packageDir, "inboost.lic"),
      path.join(packageDir, "..", "inboost.lic"),
      path.join(packageDir, "bin", "inboost.lic"),
    ];
    for (const c of candidates) {
      if (fs.existsSync(c)) {
        try {
          fs.copyFileSync(c, targetLic);
          break;
        } catch (e) {}
      }
    }
  }
}

function runInit(packageDir) {
  const userHome = os.homedir();
  const cwd = process.cwd();

  // 1. Копирует правило в глобальный ~/.claude/rules/inboost_longrun.md и ~/.agents/rules/inboost_longrun.md
  try {
    const globalClaudeDir = path.join(userHome, ".claude", "rules");
    fs.mkdirSync(globalClaudeDir, { recursive: true });
    fs.writeFileSync(path.join(globalClaudeDir, "inboost_longrun.md"), RULES_CONTENT, "utf-8");
  } catch (err) {}

  try {
    const globalAgentsDir = path.join(userHome, ".agents", "rules");
    fs.mkdirSync(globalAgentsDir, { recursive: true });
    fs.writeFileSync(path.join(globalAgentsDir, "inboost_longrun.md"), RULES_CONTENT, "utf-8");
  } catch (err) {}

  // 2. Копирует правило в текущий ./.cursorrules или ./.claude/rules/ или ./.agents/rules/
  try {
    const localClaudeDir = path.join(cwd, ".claude", "rules");
    fs.mkdirSync(localClaudeDir, { recursive: true });
    fs.writeFileSync(path.join(localClaudeDir, "inboost_longrun.md"), RULES_CONTENT, "utf-8");
  } catch (err) {}

  try {
    const localAgentsDir = path.join(cwd, ".agents", "rules");
    fs.mkdirSync(localAgentsDir, { recursive: true });
    fs.writeFileSync(path.join(localAgentsDir, "inboost_longrun.md"), RULES_CONTENT, "utf-8");
  } catch (err) {}

  try {
    const cursorrulesPath = path.join(cwd, ".cursorrules");
    let existing = "";
    if (fs.existsSync(cursorrulesPath)) {
      existing = fs.readFileSync(cursorrulesPath, "utf-8");
    }
    if (!existing.includes("InBoost LongRun Optimization Rules")) {
      const glue = existing.trim() ? "\n\n" : "";
      fs.writeFileSync(cursorrulesPath, existing + glue + RULES_CONTENT, "utf-8");
    }
  } catch (err) {}

  // 3. Добавляет в .cursor/mcp.json (если файл существует или создает его)
  try {
    const cursorDir = path.join(cwd, ".cursor");
    fs.mkdirSync(cursorDir, { recursive: true });
    const mcpPath = path.join(cursorDir, "mcp.json");
    let mcpJson = { mcpServers: {} };
    if (fs.existsSync(mcpPath)) {
      try {
        mcpJson = JSON.parse(fs.readFileSync(mcpPath, "utf-8"));
        if (!mcpJson.mcpServers || typeof mcpJson.mcpServers !== "object") {
          mcpJson.mcpServers = {};
        }
      } catch (e) {
        mcpJson = { mcpServers: {} };
      }
    }
    mcpJson.mcpServers["inboost-longrun"] = {
      command: "inboost-longrun",
      args: ["serve"]
    };
    fs.writeFileSync(mcpPath, JSON.stringify(mcpJson, null, 2) + "\n", "utf-8");
  } catch (err) {}

  // Ensure license is also verified and installed to ~/.inboost/inboost.lic
  ensureLicenseInstalled(packageDir);

  process.stdout.write("✓ InBoost LongRun rules & skills successfully configured for Claude Code and Cursor!\n");
  process.exit(0);
}

function findBinary(packageDir) {
  const binName = getBinaryName();
  const repoRoot = path.join(packageDir, "..");

  const candidates = [
    path.join(packageDir, "bin", binName),
    path.join(packageDir, binName),
    path.join(repoRoot, "bin", binName),
    path.join(repoRoot, "bin", "inboost-longrun"),
    path.join(os.homedir(), ".local", "bin", "inboost-longrun"),
    "/usr/local/bin/inboost-longrun",
    path.join(os.homedir(), ".inboost", "bin", binName),
  ];

  for (const c of candidates) {
    if (fs.existsSync(c)) {
      if (process.platform !== "win32") {
        try { fs.chmodSync(c, 0o755); } catch (e) {}
      }
      return c;
    }
  }

  // Check PATH
  const cmd = process.platform === "win32" ? "where" : "which";
  try {
    const res = spawnSync(cmd, ["inboost-longrun"], { encoding: "utf-8" });
    if (res.status === 0 && res.stdout.trim()) {
      return res.stdout.trim().split("\n")[0].trim();
    }
  } catch (e) {}

  return null;
}

function downloadBinary(binName) {
  return new Promise((resolve, reject) => {
    const targetDir = path.join(os.homedir(), ".inboost", "bin");
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }
    const targetPath = path.join(targetDir, binName);
    const downloadUrl = `https://github.com/${GITHUB_REPO}/releases/download/v${VERSION}/${binName}`;

    process.stderr.write(`InBoost LongRun binary not found locally. Downloading from ${downloadUrl}...\n`);

    const file = fs.createWriteStream(targetPath);
    function getUrl(url) {
      https.get(url, (res) => {
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          return getUrl(res.headers.location);
        }
        if (res.statusCode !== 200) {
          file.close();
          try { fs.unlinkSync(targetPath); } catch (e) {}
          return reject(new Error(`Download failed with status ${res.statusCode}`));
        }
        res.pipe(file);
        file.on("finish", () => {
          file.close(() => {
            if (process.platform !== "win32") {
              try { fs.chmodSync(targetPath, 0o755); } catch (e) {}
            }
            resolve(targetPath);
          });
        });
      }).on("error", (err) => {
        try { fs.unlinkSync(targetPath); } catch (e) {}
        reject(err);
      });
    }
    getUrl(downloadUrl);
  });
}

function checkSystemDependencies(isStrict = false) {
  const isWin = process.platform === "win32";
  const isMac = process.platform === "darwin";

  function findWindowsGitTool(tool) {
    if (!isWin) return null;
    const candidates = [
      process.env.ProgramFiles || "C:\\Program Files",
      process.env["ProgramFiles(x86)"] || "C:\\Program Files (x86)",
      process.env.LOCALAPPDATA ? path.join(process.env.LOCALAPPDATA, "Programs") : null,
      process.env.ProgramW6432 || "C:\\Program Files",
    ].filter(Boolean);

    for (const base of candidates) {
      const toolPath = path.join(base, "Git", "usr", "bin", `${tool}.exe`);
      if (fs.existsSync(toolPath)) {
        return toolPath;
      }
    }
    return null;
  }

  function which(cmd) {
    try {
      const lookup = isWin ? `where ${cmd}` : `command -v ${cmd}`;
      const res = spawnSync(isWin ? "cmd.exe" : "sh", [isWin ? "/c" : "-c", lookup], {
        encoding: "utf-8",
        stdio: ["pipe", "pipe", "ignore"],
      });
      if (res.status === 0 && res.stdout) {
        return res.stdout.trim().split(/\r?\n/)[0] || null;
      }
    } catch (e) {}
    return null;
  }

  process.stdout.write("\nChecking system dependencies for Local Offload:\n");

  const mandatoryTools = ["find", "grep", "diff", "patch", "git", "python3"];
  const missingMandatory = [];

  for (const tool of mandatoryTools) {
    let p = which(tool);
    if (!p && isWin && tool === "python3") {
      p = which("python") || which("py");
    }
    if (isWin) {
      if (tool === "find") {
        if (p && p.toLowerCase().includes("system32")) {
          p = null;
        }
        if (!p) {
          p = findWindowsGitTool("find");
        }
      } else if (!p && ["diff", "patch", "grep"].includes(tool)) {
        p = findWindowsGitTool(tool);
      }
    }
    if (p) {
      process.stdout.write(`  [\x1b[1;32m✓\x1b[0m] ${tool} (${p})\n`);
    } else {
      process.stdout.write(`  [\x1b[1;31m✗\x1b[0m] ${tool} (missing)\n`);
      missingMandatory.push(tool);
    }
  }

  const recommendedTools = [
    { name: "ast-grep", fallbacks: ["sg"] },
    { name: "ruff", fallbacks: [] },
    { name: "biome", fallbacks: [] },
    { name: "docker", fallbacks: [] },
  ];

  for (const item of recommendedTools) {
    let found = which(item.name);
    if (!found) {
      for (const fb of item.fallbacks) {
        found = which(fb);
        if (found) break;
      }
    }
    if (found) {
      process.stdout.write(`  [\x1b[1;32m✓\x1b[0m] ${item.name} (${found}) [recommended acceleration]\n`);
    } else {
      process.stdout.write(`  [\x1b[1;33m○\x1b[0m] ${item.name} (optional, recommended for <2ms local linting)\n`);
    }
  }

  // Target AI Coding Agents & IDEs
  process.stdout.write("\nChecking AI Coding Agents & IDEs:\n");
  const agentTools = [
    { name: "Claude Code", cmd: "claude", hint: "claude mcp add inboost-longrun -- inboost-longrun serve" },
    { name: "Google Antigravity", cmd: "agy", hint: "agy mcp add inboost-longrun inboost-longrun serve" },
    { name: "Cursor IDE", cmd: "cursor", hint: "inboost-longrun init (configures .cursor/mcp.json)" },
    { name: "VS Code", cmd: "code", hint: "add to .vscode/mcp.json or workspace rules" },
  ];

  for (const agent of agentTools) {
    let foundAgent = which(agent.cmd);
    if (!foundAgent && isWin) {
      foundAgent = which(`${agent.cmd}.cmd`) || which(`${agent.cmd}.exe`);
    }
    if (!foundAgent && agent.cmd === "cursor") {
      if (fs.existsSync(path.join(process.cwd(), ".cursor")) || fs.existsSync(path.join(os.homedir(), ".cursor"))) {
        foundAgent = "detected via .cursor/ directory";
      }
    }
    if (foundAgent) {
      process.stdout.write(`  [\x1b[1;32m✓\x1b[0m] ${agent.name} (${foundAgent})\n       Integration: ${agent.hint}\n`);
    } else {
      process.stdout.write(`  [\x1b[1;33m○\x1b[0m] ${agent.name} (optional, not found in PATH)\n`);
    }
  }

  if (missingMandatory.length > 0) {
    const pkgList = missingMandatory.map((t) => (t === "find" ? "findutils" : t === "diff" ? "diffutils" : t)).join(" ");
    process.stderr.write(`\n\x1b[1;31mError: Required tools missing for InBoost LongRun Local Offload: ${missingMandatory.join(", ")}\x1b[0m\n`);
    process.stderr.write("InBoost LongRun requires these tools locally to inspect outlines, calculate AST diffs, and filter test traces.\n");
    process.stderr.write("Please install the missing packages before proceeding:\n");
    if (isMac) {
      process.stderr.write(`  \x1b[1;36mbrew install ${pkgList}\x1b[0m\n\n`);
    } else if (isWin) {
      process.stderr.write(`  \x1b[1;36mwinget install --id Git.Git\x1b[0m (provides find, grep, diff, patch)\n\n`);
    } else {
      process.stderr.write(`  Debian/Ubuntu: \x1b[1;36msudo apt-get update && sudo apt-get install -y ${pkgList}\x1b[0m\n`);
      process.stderr.write(`  RHEL/Fedora:   \x1b[1;36msudo dnf install -y ${pkgList}\x1b[0m\n`);
      process.stderr.write(`  Alpine:        \x1b[1;36msudo apk add ${pkgList}\x1b[0m\n`);
      process.stderr.write(`  Arch Linux:    \x1b[1;36msudo pacman -S ${pkgList}\x1b[0m\n\n`);
    }

    if (isStrict && process.env.INBOOST_IGNORE_MISSING_DEPS !== "1") {
      process.exit(1);
    }
    return false;
  } else {
    process.stdout.write("\x1b[1;32m✓ All core offload tools verified.\x1b[0m\n\n");
    return true;
  }
}

async function main() {
  const packageDir = path.resolve(__dirname, "..");
  ensureLicenseInstalled(packageDir);

  const rawArgs = process.argv.slice(2);
  if (rawArgs.includes("check") || rawArgs.includes("doctor") || rawArgs.includes("--check")) {
    const ok = checkSystemDependencies(true);
    process.exit(ok ? 0 : 1);
  }

  if (rawArgs.includes("--postinstall")) {
    checkSystemDependencies(false);
    process.stdout.write("InBoost LongRun postinstall: verified configuration and local offload tools.\n");
    process.exit(0);
  }

  if (rawArgs.includes("init")) {
    checkSystemDependencies(false);
    runInit(packageDir);
    process.exit(0);
  }

  let binaryPath = findBinary(packageDir);
  if (!binaryPath) {
    try {
      binaryPath = await downloadBinary(getBinaryName());
    } catch (e) {
      process.stderr.write(`Error downloading binary: ${e.message}\n`);
      process.exit(1);
    }
  }

  const child = spawn(binaryPath, rawArgs, {
    stdio: "inherit",
    env: process.env,
  });

  child.on("close", (code) => {
    process.exit(code ?? 0);
  });

  child.on("error", (err) => {
    process.stderr.write(`Failed to start ${binaryPath}: ${err.message}\n`);
    process.exit(1);
  });
}

main().catch((err) => {
  process.stderr.write(`Error: ${err.message}\n`);
  process.exit(1);
});
