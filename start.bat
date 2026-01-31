@echo off
chcp 65001 >nul
title Paper Search System - 论文检索系统

echo ╔═══════════════════════════════════════════════════════════╗
echo ║                  Paper Search System                       ║
echo ║                     论文检索系统                            ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

:: Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found, using system Python
)

:: Install dependencies if needed
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting server...
echo Open browser: http://localhost:5000
echo Press Ctrl+C to quit
echo.

python app.py

pause
