@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo [INFO] Starting Python code quality check...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed
    exit /b 1
)

REM Check virtual environment
if not exist ".venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install dependencies
if exist "requirements.txt" (
    echo [INFO] Installing Python dependencies...
    pip install -r requirements.txt
)

REM Install development tools separately
echo [INFO] Installing development tools...
pip install black isort flake8 mypy bandit pytest

echo [SUCCESS] Dependencies check completed!
echo.

REM Black format check
echo [INFO] Running Black format check...
python -m black --check --diff src/
if errorlevel 1 (
    echo [ERROR] Black format check failed
    set "has_errors=1"
) else (
    echo [SUCCESS] Black format check passed
)
echo.

REM isort import sorting check
echo [INFO] Running isort import sorting check...
python -m isort --check-only --diff src/
if errorlevel 1 (
    echo [ERROR] isort check failed
    set "has_errors=1"
) else (
    echo [SUCCESS] isort check passed
)
echo.

REM Flake8 code style check
echo [INFO] Running Flake8 code style check...
python -m flake8 src/
if errorlevel 1 (
    echo [ERROR] Flake8 check failed
    set "has_errors=1"
) else (
    echo [SUCCESS] Flake8 check passed
)
echo.

REM Output results
if "%has_errors%"=="1" (
    echo [ERROR] Quality check failed! Please fix the above errors.
    exit /b 1
) else (
    echo [SUCCESS] All quality checks passed!
    exit /b 0
)