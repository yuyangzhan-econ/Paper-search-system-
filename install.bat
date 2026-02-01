@echo off
cd /d "%~dp0"
setlocal EnableDelayedExpansion

title Paper Search System - Installer

echo.
echo ===============================================================
echo           Paper Search System - Installation Wizard
echo ===============================================================
echo.

:: Check Python installation
echo [1/4] Checking Python installation...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please download Python from: https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During installation, check "Add Python to PATH"
    echo.
    goto :end
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo       Found Python %PYTHON_VERSION%
echo.

:: Create virtual environment
echo [2/4] Creating virtual environment...
echo.

if exist "venv" (
    echo       Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        goto :end
    )
    echo       Virtual environment created successfully.
)
echo.

:: Activate virtual environment and install dependencies
echo [3/4] Installing dependencies (this may take a few minutes)...
echo.

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    goto :end
)

:: Upgrade pip first
echo       Upgrading pip...
python -m pip install --upgrade pip --quiet

:: Install dependencies
echo       Installing packages from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies!
    echo.
    echo Try running manually: pip install -r requirements.txt
    goto :end
)

echo.
echo       Dependencies installed successfully.
echo.

:: Create desktop shortcut (optional, may fail)
echo [4/4] Creating desktop shortcut...
echo.

if exist "create_shortcut.py" (
    python create_shortcut.py
    if errorlevel 1 (
        echo       Note: Desktop shortcut creation failed, but installation is complete.
    )
) else (
    echo       Shortcut script not found, skipping...
)

echo.
echo ===============================================================
echo                    Installation Complete!
echo ===============================================================
echo.
echo How to run:
echo.
echo   [Browser Mode]
echo     1. Double-click start.bat
echo     2. Open http://localhost:5000 in browser
echo.
echo   [Window Mode]
echo     Double-click PaperSearch.bat
echo.
echo ===============================================================
echo.

:end
echo.
echo Press any key to exit...
pause >nul
