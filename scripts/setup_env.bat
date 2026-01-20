
@ECHO OFF

REM Change to the parent directory (project root)
CD /D %~dp0..

python -m venv .venv
call .\.venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
echo [DONE] Virtual Environment has been created (/.env/)
PAUSE
