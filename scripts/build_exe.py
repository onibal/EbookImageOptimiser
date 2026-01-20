
# -*- coding: utf-8 -*-
import sys
import subprocess
from pathlib import Path
from typing import List

# -----------------------------
# Config (edit as needed)
# -----------------------------
APP_NAME = "EbookImageOptimiser"
ENTRY_POINT = "app.py"   # your PySide6 UI file
ICON_FILE = "app.ico"
VENV_DIR = ".venv"
FOLDER_OUTPUT = "build_output"

# PyInstaller config
ONEFILE = True
WINDOWED = True
CLEAN_BUILD = True

# -----------------------------
# Helpers
# -----------------------------

def venv_python(venv_dir: Path) -> Path:
    """Return path to python inside venv."""
    return venv_dir / "Scripts" / "python.exe"

def run(cmd: List[str], env=None, check=True) -> int:
    """Run a command; return exit code; optionally raise if check=True."""
    print(">>", " ".join(cmd))
    proc = subprocess.run(cmd, env=env)
    if check and proc.returncode != 0:
        raise RuntimeError(f"Command failed with code {proc.returncode}: {' '.join(cmd)}")
    return proc.returncode

def collect_pyinstaller_cmd(py: Path) -> List[str]:
    """Compose the PyInstaller command with options and data files."""
    cmd = [
        str(py), "-m", "PyInstaller",
        ENTRY_POINT,
        "--name", APP_NAME
    ]
    if ONEFILE:
        cmd.append("--onefile")
    if WINDOWED:
        cmd.append("--windowed")
    if CLEAN_BUILD:
        cmd.append("--clean")
    if ICON_FILE and Path(ICON_FILE).exists():
        cmd += ["--icon", ICON_FILE]
    else:
        print(f"[WARN] Icon file not found or None: {ICON_FILE} (skipping)")

    return cmd


def build():
    root = Path.cwd()
    entry = root / ENTRY_POINT
    if not entry.exists():
        raise FileNotFoundError(f"Entry point not found: {entry}")

    # Prepare venv
    venv_dir = root / VENV_DIR
    py = venv_python(venv_dir)

    # Run PyInstaller with optimized Qt modules
    cmd = collect_pyinstaller_cmd(py)
    
    run(cmd)

    # Report result
    expected_exe_path = Path(FOLDER_OUTPUT) / f"{APP_NAME}.exe"
    if expected_exe_path.exists():
        print(f"[SUCCESS] Build complete: {expected_exe_path}")
    else:
        print(f"[WARN] Build finished but executable not found at: {expected_exe_path}")


def main():
    try:
        build()
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
