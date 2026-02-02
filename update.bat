@echo off
cd /d "%~dp0"

title Paper Search System - Updater

echo.
echo ===============================================================
echo              Paper Search System - Updater
echo ===============================================================
echo.

:: Check if venv exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

:: Run updater
python update.py

pause
