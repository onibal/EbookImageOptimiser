# EbookImageOptimiser



# Setup virtual environment

1) In project folder: Shift + Right‑click → “Open Command Prompt here” in Explorer.
2) python -m venv .venv
3) .venv\Scripts\activate
	Note: You should now see: (.venv) P:\PythonProjects\EbookImageOptimiser>
4) Upgrade pip (recommended): python -m pip install --upgrade pip
5) installer required package: pip install PySide6 Pillow PyInstaller opencv-python numpy
6) Verify installation: pip list
	You should see:
		PyInstaller
		PySide6
		Pillow
		...

# Setup git
	
.venv/
venv/
__pycache__/
*.pyc
