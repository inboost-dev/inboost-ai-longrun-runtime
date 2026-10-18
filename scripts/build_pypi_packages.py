#!/usr/bin/env python3
"""
Builds both PyPI wheels into dist_pypi/:
1. inboost-longrun
2. inboost-ai-longrun
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_PYPI_DIR = REPO_ROOT / "dist_pypi"
PYPROJ = REPO_ROOT / "pyproject.toml"


def build_pypi_packages():
    DIST_PYPI_DIR.mkdir(parents=True, exist_ok=True)
    orig_pyproj = PYPROJ.read_text(encoding="utf-8")

    # Clean existing wheels
    for w in DIST_PYPI_DIR.glob("*.whl"):
        w.unlink()

    packages = [
        ("inboost-longrun", "Local context conservation, quota extension, and verification engine for AI coding agents"),
        ("inboost-ai-longrun", "Local context conservation, quota extension, and verification engine for AI coding agents (alias package)"),
    ]

    try:
        for pkg_name, desc in packages:
            print(f"Building PyPI wheel for: {pkg_name}...")
            content = re.sub(r'name\s*=\s*"[^"]+"', f'name = "{pkg_name}"', orig_pyproj, count=1)
            content = re.sub(r'description\s*=\s*"[^"]+"', f'description = "{desc}"', content, count=1)
            PYPROJ.write_text(content, encoding="utf-8")

            # Clean previous build artifacts
            for egg in REPO_ROOT.glob("*.egg-info"):
                shutil.rmtree(egg, ignore_errors=True)
            build_dir = REPO_ROOT / "build"
            if build_dir.exists():
                shutil.rmtree(build_dir, ignore_errors=True)

            cmd = [sys.executable, "-m", "pip", "wheel", "--no-deps", "-w", str(DIST_PYPI_DIR), str(REPO_ROOT)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                print(f"Error building {pkg_name}: {res.stderr}")
                sys.exit(res.returncode)
            print(f"  ✓ Built wheel for {pkg_name}")

    finally:
        PYPROJ.write_text(orig_pyproj, encoding="utf-8")
        for egg in REPO_ROOT.glob("*.egg-info"):
            shutil.rmtree(egg, ignore_errors=True)
        build_dir = REPO_ROOT / "build"
        if build_dir.exists():
            shutil.rmtree(build_dir, ignore_errors=True)

    print("\nVerifying built wheels with twine check:")
    wheels = list(DIST_PYPI_DIR.glob("*.whl"))
    for w in wheels:
        print(f"  • {w.name}")
    subprocess.run([sys.executable, "-m", "twine", "check"] + [str(w) for w in wheels], check=True)


if __name__ == "__main__":
    build_pypi_packages()
