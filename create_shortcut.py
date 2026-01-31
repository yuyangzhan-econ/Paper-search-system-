#!/usr/bin/env python3
"""
Create desktop shortcut for Paper Search System.
为论文检索系统创建桌面快捷方式。
"""

import os
import sys
import platform


def create_windows_shortcut():
    """Create Windows desktop shortcut (.lnk)."""
    try:
        import winshell
        from win32com.client import Dispatch
    except ImportError:
        # If pywin32 is not available, create a batch file shortcut
        create_windows_batch_shortcut()
        return

    # Get paths
    app_dir = os.path.dirname(os.path.abspath(__file__))
    desktop = winshell.desktop()
    shortcut_path = os.path.join(desktop, "Paper Search.lnk")

    # Python executable in venv
    python_exe = os.path.join(app_dir, "venv", "Scripts", "pythonw.exe")
    if not os.path.exists(python_exe):
        python_exe = os.path.join(app_dir, "venv", "Scripts", "python.exe")

    # Create shortcut
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = python_exe
    shortcut.Arguments = f'"{os.path.join(app_dir, "desktop_app.py")}"'
    shortcut.WorkingDirectory = app_dir
    shortcut.Description = "Paper Search System - 论文检索系统"
    shortcut.save()

    print(f"       Desktop shortcut created: {shortcut_path}")
    print(f"       桌面快捷方式已创建: {shortcut_path}")


def create_windows_batch_shortcut():
    """Create a batch file for launching the app."""
    app_dir = os.path.dirname(os.path.abspath(__file__))

    # Create launcher batch file
    launcher_path = os.path.join(app_dir, "PaperSearch.bat")
    batch_content = f'''@echo off
cd /d "{app_dir}"
call venv\\Scripts\\activate.bat
start "" pythonw desktop_app.py
'''

    with open(launcher_path, 'w', encoding='utf-8') as f:
        f.write(batch_content)

    print(f"       Launcher created: {launcher_path}")
    print(f"       启动器已创建: {launcher_path}")

    # Try to create desktop shortcut to the batch file
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.exists(desktop):
            # Create a simple VBS script to create shortcut
            vbs_path = os.path.join(app_dir, "temp_shortcut.vbs")
            shortcut_path = os.path.join(desktop, "Paper Search.lnk")

            vbs_content = f'''Set oWS = WScript.CreateObject("WScript.Shell")
Set oLink = oWS.CreateShortcut("{shortcut_path}")
oLink.TargetPath = "{launcher_path}"
oLink.WorkingDirectory = "{app_dir}"
oLink.Description = "Paper Search System"
oLink.Save
'''
            with open(vbs_path, 'w', encoding='utf-8') as f:
                f.write(vbs_content)

            # Run VBS script
            os.system(f'cscript //nologo "{vbs_path}"')

            # Clean up
            if os.path.exists(vbs_path):
                os.remove(vbs_path)

            if os.path.exists(shortcut_path):
                print(f"       Desktop shortcut created: {shortcut_path}")
                print(f"       桌面快捷方式已创建: {shortcut_path}")

    except Exception as e:
        print(f"       Note: Could not create desktop shortcut automatically.")
        print(f"       You can create a shortcut to PaperSearch.bat manually.")
        print(f"       注意：无法自动创建桌面快捷方式。")
        print(f"       您可以手动创建 PaperSearch.bat 的快捷方式。")


def create_macos_app():
    """Create macOS application shortcut."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    desktop = os.path.expanduser("~/Desktop")

    # Create shell script launcher
    launcher_path = os.path.join(app_dir, "PaperSearch.command")
    script_content = f'''#!/bin/bash
cd "{app_dir}"
source venv/bin/activate
python desktop_app.py
'''
    with open(launcher_path, 'w') as f:
        f.write(script_content)
    os.chmod(launcher_path, 0o755)

    # Create symbolic link on desktop
    link_path = os.path.join(desktop, "Paper Search.command")
    if os.path.exists(link_path):
        os.remove(link_path)

    try:
        os.symlink(launcher_path, link_path)
        print(f"       Desktop shortcut created: {link_path}")
    except Exception:
        print(f"       Launcher created: {launcher_path}")
        print(f"       You can drag it to Desktop or Dock")


def create_linux_desktop_entry():
    """Create Linux .desktop file."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    desktop = os.path.expanduser("~/Desktop")
    applications = os.path.expanduser("~/.local/share/applications")

    # Create shell script launcher
    launcher_path = os.path.join(app_dir, "papersearch.sh")
    script_content = f'''#!/bin/bash
cd "{app_dir}"
source venv/bin/activate
python desktop_app.py
'''
    with open(launcher_path, 'w') as f:
        f.write(script_content)
    os.chmod(launcher_path, 0o755)

    # Create .desktop file
    desktop_entry = f'''[Desktop Entry]
Name=Paper Search
Comment=Paper Search System - 论文检索系统
Exec="{launcher_path}"
Terminal=false
Type=Application
Categories=Office;Science;
'''

    # Save to applications folder
    os.makedirs(applications, exist_ok=True)
    desktop_file = os.path.join(applications, "papersearch.desktop")
    with open(desktop_file, 'w') as f:
        f.write(desktop_entry)
    os.chmod(desktop_file, 0o755)

    # Copy to desktop
    if os.path.exists(desktop):
        desktop_link = os.path.join(desktop, "Paper Search.desktop")
        with open(desktop_link, 'w') as f:
            f.write(desktop_entry)
        os.chmod(desktop_link, 0o755)
        print(f"       Desktop shortcut created: {desktop_link}")

    print(f"       Application entry created: {desktop_file}")


def main():
    system = platform.system()

    if system == 'Windows':
        create_windows_batch_shortcut()
    elif system == 'Darwin':
        create_macos_app()
    elif system == 'Linux':
        create_linux_desktop_entry()
    else:
        print(f"       Unsupported platform: {system}")
        print(f"       不支持的系统: {system}")


if __name__ == '__main__':
    main()
