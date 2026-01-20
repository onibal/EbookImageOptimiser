
@ECHO OFF

:: Change to the parent directory (project root)
cd /d %~dp0..

:: Run the Python-based builder. It will manage venv, deps, and PyInstaller.
python scripts\build_exe.py
if errorlevel 1 (
    echo [ERROR] Build failed.
	pause
    exit /b 1
)

echo [DONE] Executable should be in the "build_output" folder.
pause
exit /b 0
``
