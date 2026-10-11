#!/usr/bin/env python3
"""
CLI launcher for InBoost LongRun Evaluation Runtime.
Resolves platform-native binary, ensures license is placed, and executes the engine.
"""

import os
import platform
import shutil
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path

VERSION = "0.1.0-eval"
GITHUB_REPO = "inboost-dev/inboost-ai-longrun-runtime"


def get_binary_name() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        if machine in ("x86_64", "amd64"):
            return "inboost-longrun-linux-amd64"
        elif machine in ("aarch64", "arm64"):
            return "inboost-longrun-linux-arm64"
    elif system == "darwin":
        if machine in ("arm64", "aarch64"):
            return "inboost-longrun-darwin-arm64"
        elif machine in ("x86_64", "amd64"):
            return "inboost-longrun-darwin-amd64"
    elif system == "windows":
        if machine in ("x86_64", "amd64"):
            return "inboost-longrun-windows-amd64.exe"

    raise RuntimeError(f"Unsupported platform: {system} {machine}")


def ensure_license_installed(package_root: Path) -> None:
    inboost_home = Path.home() / ".inboost"
    inboost_home.mkdir(parents=True, exist_ok=True)
    target_lic = inboost_home / "inboost.lic"

    if not target_lic.exists():
        candidates = [
            package_root / "inboost.lic",
            package_root.parent / "inboost.lic",
            Path(__file__).parent / "inboost.lic",
        ]
        for c in candidates:
            if c.exists():
                try:
                    shutil.copy2(c, target_lic)
                    break
                except Exception:
                    pass


def find_or_download_binary() -> Path:
    bin_name = get_binary_name()
    package_dir = Path(__file__).resolve().parent
    repo_root = package_dir.parent

    # Check candidates
    candidates = [
        package_dir / "bin" / bin_name,
        package_dir / bin_name,
        repo_root / "bin" / bin_name,
        repo_root / "bin" / "inboost-longrun",
        Path.home() / ".local" / "bin" / "inboost-longrun",
        Path("/usr/local/bin/inboost-longrun"),
        Path.home() / ".inboost" / "bin" / bin_name,
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            if os.name != "nt":
                # Ensure executable bit
                try:
                    candidate.chmod(candidate.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                except Exception:
                    pass
            return candidate

    # Check PATH
    which_bin = shutil.which("inboost-longrun")
    if which_bin:
        return Path(which_bin)

    # Download if missing
    inboost_bin_dir = Path.home() / ".inboost" / "bin"
    inboost_bin_dir.mkdir(parents=True, exist_ok=True)
    target_path = inboost_bin_dir / bin_name

    download_url = f"https://github.com/{GITHUB_REPO}/releases/download/v{VERSION}/{bin_name}"
    sys.stderr.write(f"InBoost LongRun binary not found locally. Downloading from {download_url}...\n")

    try:
        urllib.request.urlretrieve(download_url, str(target_path))
        if os.name != "nt":
            target_path.chmod(target_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return target_path
    except Exception as e:
        raise RuntimeError(f"Failed to download InBoost LongRun binary: {e}")


def main() -> None:
    package_root = Path(__file__).resolve().parent.parent
    ensure_license_installed(package_root)

    try:
        binary_path = find_or_download_binary()
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    args = [str(binary_path)] + sys.argv[1:]

    # On POSIX, replace process with execv
    if os.name == "posix":
        try:
            os.execv(str(binary_path), args)
        except OSError as e:
            sys.stderr.write(f"Failed to execute {binary_path}: {e}\n")
            sys.exit(1)
    else:
        # On Windows, run via subprocess
        try:
            res = subprocess.run(args)
            sys.exit(res.returncode)
        except Exception as e:
            sys.stderr.write(f"Execution failed: {e}\n")
            sys.exit(1)


if __name__ == "__main__":
    main()
