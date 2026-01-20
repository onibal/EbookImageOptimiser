import subprocess
import sys
from pathlib import Path

# Read required Python version from .python-version file
version_file = Path(__file__).parent.parent / ".python-version"
try:
    with open(version_file) as f:
        required_version = tuple(map(int, f.read().strip().split('.')))
except (FileNotFoundError, ValueError) as e:
    sys.exit(f"Error reading .python-version file: {e}")

# Enforce Python version
if sys.version_info[:3] != required_version:
    sys.exit(
        f"This project requires Python {'.'.join(map(str, required_version))}. "
        f"You are using Python {'.'.join(map(str, sys.version_info[:3]))}."
    )

VENV = Path(".venv")


def run(cmd):
    subprocess.check_call(cmd, shell=True)


if not VENV.exists():
    run(f"{sys.executable} -m venv .venv")

pip = VENV / ("Scripts/pip.exe" if sys.platform == "win32" else "bin/pip")

run(f"{pip} install --upgrade pip")
run(f"{pip} install -r requirements.txt")
run(" ".join([str(pip), "install", "-r", "requirements-build.txt"]))

print("✅ Environment ready")
