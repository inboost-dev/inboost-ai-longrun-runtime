#!/usr/bin/env python3
"""
Automated publisher for InBoost LongRun npm and PyPI packages.
Reads tokens from ~/.env safely without exposing credentials to stdout or transcript.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_NPM_DIR = REPO_ROOT / "dist_npm"
DIST_PYPI_DIR = REPO_ROOT / "dist_pypi"


def load_env() -> dict[str, str]:
    env_vars = {}
    env_path = Path.home() / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars


def publish_npm(npm_token: str):
    print("==================================================")
    print("▶ Publishing 4 npm packages to npmjs.org...")
    print("==================================================")

    version = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))["version"]
    tarballs = [
        DIST_NPM_DIR / f"inboost-pro-inboost-ai-longrun-{version}.tgz",
        DIST_NPM_DIR / f"inboost-pro-inboost-longrun-{version}.tgz",
        DIST_NPM_DIR / f"inboost-ai-longrun-{version}.tgz",
        DIST_NPM_DIR / f"inboost-longrun-{version}.tgz",
    ]

    with tempfile.NamedTemporaryFile("w", delete=False) as tf:
        tf.write(f"//registry.npmjs.org/:_authToken={npm_token}\n")
        userconfig_path = tf.name

    try:
        for t in tarballs:
            if not t.exists():
                print(f"  ✗ Tarball not found: {t.name}")
                continue

            print(f"Publishing {t.name}...")
            cmd = [
                "npm",
                "--userconfig", userconfig_path,
                "publish",
                str(t.resolve()),
                "--access", "public",
            ]
            res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"  ✓ Published {t.name} successfully!")
            else:
                err_clean = "\n".join(
                    line for line in res.stderr.splitlines()
                    if not any(token_part in line for token_part in [npm_token[:8], "authToken"])
                )
                print(f"  ✗ Error publishing {t.name} (exit {res.returncode}):")
                print(f"    {err_clean}")
    finally:
        if os.path.exists(userconfig_path):
            os.remove(userconfig_path)


def publish_pypi(pypi_token: str):
    print("\n==================================================")
    print("▶ Publishing wheels to pypi.org...")
    print("==================================================")

    wheels = list(DIST_PYPI_DIR.glob("*.whl"))
    for w in wheels:
        print(f"Publishing {w.name}...")
        cmd = [
            sys.executable, "-m", "twine", "upload",
            str(w),
            "--username", "__token__",
            "--password", pypi_token,
            "--skip-existing",
        ]
        res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  ✓ Published {w.name} successfully!")
        else:
            err_clean = "\n".join(
                line for line in (res.stdout + "\n" + res.stderr).splitlines()
                if not any(token_part in line for token_part in [pypi_token[:8], "__token__"])
            )
            print(f"  ✗ Error publishing {w.name} (exit {res.returncode}):")
            print(f"    {err_clean}")


def main():
    env = load_env()
    npm_token = env.get("NPM_TOKEN")
    pypi_token = env.get("PYPI_API_TOKEN")

    if not npm_token:
        print("Error: NPM_TOKEN not found in ~/.env")
    else:
        publish_npm(npm_token)

    if not pypi_token:
        print("Error: PYPI_API_TOKEN not found in ~/.env")
    else:
        publish_pypi(pypi_token)


if __name__ == "__main__":
    main()
