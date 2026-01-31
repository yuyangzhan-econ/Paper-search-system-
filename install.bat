@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

title Paper Search System - Installer / 论文检索系统 - 安装程序

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║          Paper Search System - Installation Wizard            ║
echo ║              论文检索系统 - 安装向导                            ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

:: Check Python installation
echo [1/4] Checking Python installation...
echo       检查 Python 安装...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo         Python 未安装或未添加到环境变量！
    echo.
    echo Please download Python from: https://www.python.org/downloads/
    echo 请从以下地址下载 Python: https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During installation, check "Add Python to PATH"
    echo 重要提示：安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo       Found Python %PYTHON_VERSION%
echo       找到 Python %PYTHON_VERSION%
echo.

:: Create virtual environment
echo [2/4] Creating virtual environment...
echo       创建虚拟环境...
echo.

if exist "venv" (
    echo       Virtual environment already exists, skipping...
    echo       虚拟环境已存在，跳过...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        echo         创建虚拟环境失败！
        pause
        exit /b 1
    )
    echo       Virtual environment created successfully.
    echo       虚拟环境创建成功。
)
echo.

:: Activate virtual environment and install dependencies
echo [3/4] Installing dependencies (this may take a few minutes)...
echo       安装依赖包（可能需要几分钟）...
echo.

call venv\Scripts\activate.bat

:: Upgrade pip first
python -m pip install --upgrade pip --quiet

:: Install dependencies
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    echo         安装依赖包失败！
    echo.
    echo Try running manually: pip install -r requirements.txt
    echo 尝试手动运行: pip install -r requirements.txt
    pause
    exit /b 1
)

echo       Dependencies installed successfully.
echo       依赖包安装成功。
echo.

:: Create desktop shortcut
echo [4/4] Creating desktop shortcut...
echo       创建桌面快捷方式...
echo.

:: Run the shortcut creation script
python create_shortcut.py

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                  Installation Complete!                        ║
echo ║                      安装完成！                                 ║
echo ╠═══════════════════════════════════════════════════════════════╣
echo ║                                                                 ║
echo ║  You can now:                                                   ║
echo ║  您现在可以:                                                     ║
echo ║                                                                 ║
echo ║  1. Double-click the desktop shortcut "Paper Search"           ║
echo ║     双击桌面快捷方式 "Paper Search"                              ║
echo ║                                                                 ║
echo ║  2. Or double-click "PaperSearch.bat" in this folder           ║
echo ║     或双击本文件夹中的 "PaperSearch.bat"                          ║
echo ║                                                                 ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

pause
