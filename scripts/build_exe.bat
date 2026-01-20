
@ECHO OFF

:: Change to the parent directory (project root)
cd /d %~dp0..
call .venv\Scripts\activate.bat
pyinstaller --clean --noconfirm app.spec
echo [DONE] Executable should be in the "dist" folder.
PAUSE
