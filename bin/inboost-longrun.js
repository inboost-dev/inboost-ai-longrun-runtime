#!/usr/bin/env node

/**
 * InBoost LongRun Evaluation Runtime — Universal Node CLI & npx Wrapper
 * 
 * Supports:
 *   npx inboost-longrun
 *   npx inboost-longrun status
 *   npx inboost-longrun serve
 *   npm install -g inboost-longrun
 */

const { spawn, spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const os = require("os");
const https = require("https");

const VERSION = "0.1.0-eval";
const GITHUB_REPO = "inboost-dev/inboost-ai-longrun-runtime";

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

async function main() {
  const packageDir = path.resolve(__dirname, "..");
  ensureLicenseInstalled(packageDir);

  const rawArgs = process.argv.slice(2);
  if (rawArgs.includes("--postinstall")) {
    process.stdout.write("InBoost LongRun postinstall: verified configuration.\n");
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
