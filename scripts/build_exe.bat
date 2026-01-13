
@echo off
setlocal

:: Change to the parent directory (project root)
cd /d %~dp0..

:: Run the Python-based builder. It will manage venv, deps, and PyInstaller.
python src\build.py
if errorlevel 1 (
    echo [ERROR] Build failed.
	pause
    exit /b 1
)

echo [DONE] Executable should be in the "dist" folder.
pause
exit /b 0
``
