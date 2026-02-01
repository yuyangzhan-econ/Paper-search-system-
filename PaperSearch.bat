@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

title Paper Search - 论文检索系统

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║              Paper Search - 论文检索系统                   ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

:: Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo         未找到虚拟环境！
    echo.
    echo Please run install.bat first.
    echo 请先运行 install.bat 进行安装。
    echo.
    pause
    exit /b 1
)

:: Activate venv
echo Activating virtual environment...
echo 正在激活虚拟环境...
call venv\Scripts\activate.bat

:: Check if pywebview is installed
python -c "import webview" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] pywebview is not installed!
    echo         pywebview 未安装！
    echo.
    echo Installing pywebview...
    echo 正在安装 pywebview...
    pip install pywebview
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install pywebview!
        echo         安装 pywebview 失败！
        echo.
        echo Please try: pip install pywebview
        echo 请尝试手动运行: pip install pywebview
        echo.
        pause
        exit /b 1
    )
)

echo.
echo Starting Paper Search...
echo 正在启动论文检索系统...
echo.
echo (If this window closes and no app appears, try running start.bat instead)
echo (如果本窗口关闭后没有出现应用，请尝试运行 start.bat)
echo.

:: Run desktop app with python (not pythonw) to show errors
python desktop_app.py

:: If we get here, the app exited (either normally or with error)
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error!
    echo         应用程序异常退出！
    echo.
    echo You can try browser mode instead:
    echo 您可以尝试浏览器模式：
    echo   1. Run start.bat
    echo   2. Open http://localhost:5000 in browser
    echo.
)

pause
