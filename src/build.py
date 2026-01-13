
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

# -----------------------------
# Config (edit as needed)
# -----------------------------
APP_NAME = "EbookImageOptimiser"
ENTRY_POINT = "app.py"   # your PySide6 UI file
ICON_FILE = "app.ico"
VENV_DIR = ".venv"
DIST_DIR = "dist"

# Whether to build one-file exe and windowed (no console)
ONEFILE = True
WINDOWED = True
CLEAN_BUILD = True

# Add data files/folders: list of tuples (src_path, dest_subfolder)
# Example: DATA_SPEC = [("assets", "assets"), ("configs", "configs")]
DATA_SPEC: List[Tuple[str, str]] = []

# If PyInstaller fails to bundle Qt platform plugins, set this True to force-add them.
FORCE_ADD_QT_PLATFORMS = False

# -----------------------------
# Helpers
# -----------------------------


def run(cmd: List[str], env=None, check=True) -> int:
    """Run a command; return exit code; optionally raise if check=True."""
    print(">>", " ".join(cmd))
    proc = subprocess.run(cmd, env=env)
    if check and proc.returncode != 0:
        raise RuntimeError(f"Command failed with code {proc.returncode}: {' '.join(cmd)}")
    return proc.returncode


def is_windows() -> bool:
    return os.name == "nt"


def venv_python(venv_dir: Path) -> Path:
    """Return path to python inside venv."""
    if is_windows():
        return venv_dir / "Scripts" / "python.exe"
    # For completeness; though batch file is Windows-oriented
    return venv_dir / "bin" / "python"


def venv_activate_cmd(venv_dir: Path) -> str:
    """Return activation command for venv (Windows). Not used directly since we call Python by absolute path."""
    if is_windows():
        return str(venv_dir / "Scripts" / "activate")
    return f"source {venv_dir/'bin'/'activate'}"


def ensure_venv(venv_dir: Path, base_python: str = sys.executable) -> None:
    """Create venv if missing."""
    if not venv_dir.exists():
        print(f"[INFO] Creating virtual environment: {venv_dir}")
        run([base_python, "-m", "venv", str(venv_dir)])


def pip_install(py: Path, packages: List[str]) -> None:
    """Install packages using pip within venv."""
    print("[INFO] Upgrading pip…")
    run([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    print(f"[INFO] Installing: {', '.join(packages)}")
    run([str(py), "-m", "pip", "install", "--upgrade"] + packages)


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

    # Data files
    # PyInstaller --add-data syntax on Windows: SRC;DEST
    for src, dest in DATA_SPEC:
        src_path = Path(src)
        if not src_path.exists():
            print(f"[WARN] Data source not found: {src} (skipping)")
            continue
        cmd += ["--add-data", f"{src};{dest}"]

    # Optional: Force add Qt platforms if needed
    if FORCE_ADD_QT_PLATFORMS:
        try:
            site_packages = subprocess.check_output([str(py), "-c",
                                                     "import site, sys; print(site.getsitepackages()[0] if hasattr(site,'getsitepackages') else sys.prefix)"],
                                                    text=True).strip()
            platforms_src = Path(site_packages) / "PySide6" / "plugins" / "platforms"
            if platforms_src.exists():
                cmd += ["--add-data", f"{platforms_src};PySide6/plugins/platforms"]
                print(f"[INFO] Added Qt platforms from: {platforms_src}")
            else:
                print("[WARN] Qt 'platforms' not found to add explicitly.")
        except Exception as e:
            print(f"[WARN] Could not auto-detect site-packages for Qt platforms: {e}")

    return cmd


def build():
    root = Path.cwd()
    entry = root / ENTRY_POINT
    if not entry.exists():
        raise FileNotFoundError(f"Entry point not found: {entry}")

    # Prepare venv
    venv_dir = root / VENV_DIR
    ensure_venv(venv_dir, base_python=sys.executable)
    py = venv_python(venv_dir)

    # Install deps
    pip_install(py, ["PySide6", "Pillow", "PyInstaller", "opencv-python", "numpy"])

    # Run PyInstaller with optimized Qt modules
    cmd = collect_pyinstaller_cmd(py)

    print("[INFO] Running PyInstaller with optimized Qt modules…")
    run(cmd)

    # Report result
    exe_path = Path(DIST_DIR) / f"{APP_NAME}.exe"
    if exe_path.exists():
        print(f"[SUCCESS] Build complete: {exe_path}")
    else:
        print(f"[WARN] Build finished but executable not found at: {exe_path}")
        print("       Check PyInstaller output above; one-folder builds use 'dist/<name>/'.")


def main():
    try:
        build()
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
