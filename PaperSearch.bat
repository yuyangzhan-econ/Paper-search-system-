@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Please run install.bat first.
    echo 未找到虚拟环境。请先运行 install.bat 进行安装。
    pause
    exit /b 1
)

:: Activate venv and run
call venv\Scripts\activate.bat
start "" pythonw desktop_app.py
