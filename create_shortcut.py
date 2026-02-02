#!/usr/bin/env python3
"""
Create desktop shortcut for Paper Search System.
"""

import os
import sys
import platform


def create_windows_shortcut():
    """Create Windows desktop shortcut (.lnk) pointing to PaperSearch.bat."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    bat_path = os.path.join(app_dir, "PaperSearch.bat")

    # Check if PaperSearch.bat exists
    if not os.path.exists(bat_path):
        print(f"       [ERROR] PaperSearch.bat not found!")
        print(f"       Please ensure PaperSearch.bat exists in: {app_dir}")
        return

    # Try to get desktop path
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop):
            # Try alternative paths
            desktop = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
        if not os.path.exists(desktop):
            print(f"       [ERROR] Desktop folder not found!")
            return
    except Exception as e:
        print(f"       [ERROR] Could not find desktop: {e}")
        return

    shortcut_path = os.path.join(desktop, "Paper Search.lnk")

    # Method 1: Try using pywin32
    try:
        from win32com.client import Dispatch
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = bat_path
        shortcut.WorkingDirectory = app_dir
        shortcut.Description = "Paper Search System"
        shortcut.save()
        print(f"       Desktop shortcut created: {shortcut_path}")
        return
    except ImportError:
        pass  # pywin32 not available, try VBS method
    except Exception as e:
        print(f"       Note: pywin32 method failed: {e}")

    # Method 2: Use VBScript to create shortcut
    try:
        vbs_path = os.path.join(app_dir, "temp_shortcut.vbs")

        # Use simple ASCII content to avoid encoding issues
        vbs_content = '''Set oWS = WScript.CreateObject("WScript.Shell")
Set oLink = oWS.CreateShortcut("{shortcut}")
oLink.TargetPath = "{target}"
oLink.WorkingDirectory = "{workdir}"
oLink.Description = "Paper Search System"
oLink.Save
'''.format(
            shortcut=shortcut_path.replace("\\", "\\\\"),
            target=bat_path.replace("\\", "\\\\"),
            workdir=app_dir.replace("\\", "\\\\")
        )

        with open(vbs_path, 'w', encoding='ascii', errors='replace') as f:
            f.write(vbs_content)

        # Run VBS script
        result = os.system(f'cscript //nologo "{vbs_path}"')

        # Clean up
        if os.path.exists(vbs_path):
            os.remove(vbs_path)

        if os.path.exists(shortcut_path):
            print(f"       Desktop shortcut created: {shortcut_path}")
        else:
            print(f"       Note: Shortcut creation may have failed.")
            print(f"       You can manually create a shortcut to: {bat_path}")

    except Exception as e:
        print(f"       Note: Could not create desktop shortcut: {e}")
        print(f"       You can manually create a shortcut to: {bat_path}")


def create_macos_shortcut():
    """Create macOS desktop alias."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    desktop = os.path.expanduser("~/Desktop")

    # Create shell script launcher if it doesn't exist
    launcher_path = os.path.join(app_dir, "PaperSearch.command")
    if not os.path.exists(launcher_path):
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
    except Exception as e:
        print(f"       Launcher created: {launcher_path}")
        print(f"       You can drag it to Desktop or Dock")


def create_linux_shortcut():
    """Create Linux .desktop file."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    desktop = os.path.expanduser("~/Desktop")
    applications = os.path.expanduser("~/.local/share/applications")

    # Create shell script launcher if it doesn't exist
    launcher_path = os.path.join(app_dir, "papersearch.sh")
    if not os.path.exists(launcher_path):
        script_content = f'''#!/bin/bash
cd "{app_dir}"
source venv/bin/activate
python desktop_app.py
'''
        with open(launcher_path, 'w') as f:
            f.write(script_content)
        os.chmod(launcher_path, 0o755)

    # Create .desktop file content
    desktop_entry = f'''[Desktop Entry]
Name=Paper Search
Comment=Paper Search System
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
        create_windows_shortcut()
    elif system == 'Darwin':
        create_macos_shortcut()
    elif system == 'Linux':
        create_linux_shortcut()
    else:
        print(f"       Unsupported platform: {system}")


if __name__ == '__main__':
    main()
