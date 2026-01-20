
@ECHO OFF

REM Desired Python version
SET PYTHON_VERSION=3.11.9

REM Change to the parent directory (project root)
CD /D %~dp0..

REM 1. Install pyenv-win if not installed
WHERE pyenv >NUL 2>&1
IF ERRORLEVEL 1 (
    ECHO Installing pyenv-win...
    powershell -Command "Invoke-WebRequest -UseBasicParsing https://pyenv.run | Invoke-Expression"
)

REM 2. Install and set Python version
pyenv install -s %PYTHON_VERSION%
pyenv local %PYTHON_VERSION%

REM 3. Create virtual environment (overwrite if exists)
python -m venv venv

REM 4. Activate and install dependencies
CALL venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-build.txt

ECHO ✅ Environment ready with Python %PYTHON_V
