@echo off
cd /d "%~dp0"

title Paper Search System

echo.
echo ===============================================================
echo                    Paper Search System
echo ===============================================================
echo.

:: Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please run install.bat first.
    echo.
    pause
    exit /b 1
)

:: Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Check if pywebview is installed
python -c "import webview" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] pywebview is not installed!
    echo.
    echo Installing pywebview...
    pip install pywebview
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install pywebview!
        echo.
        echo Please try manually: pip install pywebview
        echo.
        pause
        exit /b 1
    )
)

echo.
echo Starting Paper Search System...
echo.
echo If no window appears, try running start.bat instead
echo and open http://localhost:5000 in your browser.
echo.

:: Run desktop app with python (not pythonw) to show errors
python desktop_app.py

:: If we get here, the app exited (either normally or with error)
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error!
    echo.
    echo You can try browser mode instead:
    echo   1. Run start.bat
    echo   2. Open http://localhost:5000 in browser
    echo.
)

pause
