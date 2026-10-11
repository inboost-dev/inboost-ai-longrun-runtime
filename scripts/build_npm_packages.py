#!/usr/bin/env python3
"""
Builds all 4 npm release packages into dist_npm/ directory:
1. @inboost-pro/inboost-ai-longrun (Organization primary package)
2. @inboost-pro/inboost-longrun (Organization alias package)
3. inboost-ai-longrun (Root primary package)
4. inboost-longrun (Root alias package)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_NPM_DIR = REPO_ROOT / "dist_npm"
BASE_PKG_JSON = REPO_ROOT / "package.json"

PACKAGES = [
    {
        "name": "@inboost-pro/inboost-ai-longrun",
        "description": "Local context conservation, quota extension, and verification engine for AI coding agents",
        "publish_access": "public",
    },
    {
        "name": "@inboost-pro/inboost-longrun",
        "description": "Local context conservation, quota extension, and verification engine for AI coding agents (alias package)",
        "publish_access": "public",
    },
    {
        "name": "inboost-ai-longrun",
        "description": "Local context conservation, quota extension, and verification engine for AI coding agents",
        "publish_access": "public",
    },
    {
        "name": "inboost-longrun",
        "description": "Local context conservation, quota extension, and verification engine for AI coding agents (alias package)",
        "publish_access": "public",
    },
]


def build_npm_packages() -> list[Path]:
    DIST_NPM_DIR.mkdir(parents=True, exist_ok=True)
    orig_content = BASE_PKG_JSON.read_text(encoding="utf-8")
    base_data = json.loads(orig_content)

    built_tarballs: list[Path] = []
    try:
        for pkg in PACKAGES:
            print(f"Building npm package: {pkg['name']}...")
            pkg_data = dict(base_data)
            pkg_data["name"] = pkg["name"]
            pkg_data["description"] = pkg["description"]
            pkg_data["publishConfig"] = {"access": pkg["publish_access"]}
            pkg_data["bin"] = {
                "inboost-longrun": "./bin/inboost-longrun.js",
                "inboost-ai-longrun": "./bin/inboost-longrun.js",
            }
            pkg_data["author"] = "InBoost Technologies <inbound@inboost.pro>"

            BASE_PKG_JSON.write_text(json.dumps(pkg_data, indent=2) + "\n", encoding="utf-8")

            res = subprocess.run(
                ["npm", "pack", "--pack-destination", str(DIST_NPM_DIR)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            tarball_name = res.stdout.strip().splitlines()[-1]
            tarball_path = DIST_NPM_DIR / tarball_name
            print(f"  ✓ Packed: {tarball_path.name} ({tarball_path.stat().st_size / 1024:.1f} KB)")
            built_tarballs.append(tarball_path)

    finally:
        # Restore default package.json
        base_data["name"] = "@inboost-pro/inboost-longrun"
        base_data["publishConfig"] = {"access": "public"}
        base_data["bin"] = {
            "inboost-longrun": "./bin/inboost-longrun.js",
            "inboost-ai-longrun": "./bin/inboost-longrun.js",
        }
        base_data["author"] = "InBoost Technologies <inbound@inboost.pro>"
        BASE_PKG_JSON.write_text(json.dumps(base_data, indent=2) + "\n", encoding="utf-8")

    print("\nAll npm packages built successfully:")
    for t in built_tarballs:
        print(f"  • {t.name}")
    return built_tarballs


if __name__ == "__main__":
    build_npm_packages()
