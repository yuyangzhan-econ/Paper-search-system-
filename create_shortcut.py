#!/usr/bin/env python3
"""
Create desktop shortcut for Paper Search System.
"""

import os
import sys
import platform
import subprocess


def create_windows_shortcut():
    """Create Windows desktop shortcut (.lnk) pointing to PaperSearch.bat."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    bat_path = os.path.join(app_dir, "PaperSearch.bat")
    icon_path = os.path.join(app_dir, "icon.ico")

    # Check if PaperSearch.bat exists
    if not os.path.exists(bat_path):
        print(f"       [ERROR] PaperSearch.bat not found!")
        print(f"       Please ensure PaperSearch.bat exists in: {app_dir}")
        return False

    # Try to get desktop path
    try:
        # Method 1: Use shell to get desktop path (handles localized names)
        import ctypes.wintypes
        CSIDL_DESKTOP = 0
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, 0, buf)
        desktop = buf.value

        if not desktop or not os.path.exists(desktop):
            # Fallback to common paths
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop):
            desktop = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
        if not os.path.exists(desktop):
            # Try Chinese desktop name
            desktop = os.path.join(os.path.expanduser("~"), "桌面")
        if not os.path.exists(desktop):
            print(f"       [ERROR] Desktop folder not found!")
            return False
    except Exception as e:
        # Fallback
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop):
            print(f"       [ERROR] Could not find desktop: {e}")
            return False

    shortcut_path = os.path.join(desktop, "Paper Search.lnk")

    # Method 1: Try using PowerShell (more reliable for paths with special chars)
    try:
        # PowerShell command to create shortcut
        ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{bat_path}"
$Shortcut.WorkingDirectory = "{app_dir}"
$Shortcut.Description = "Paper Search System"
$Shortcut.WindowStyle = 1
'''
        # Add icon if exists
        if os.path.exists(icon_path):
            ps_script += f'$Shortcut.IconLocation = "{icon_path}"\n'

        ps_script += '$Shortcut.Save()'

        # Run PowerShell
        result = subprocess.run(
            ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=30
        )

        if os.path.exists(shortcut_path):
            print(f"       Desktop shortcut created: Paper Search.lnk")
            if os.path.exists(icon_path):
                print(f"       Icon applied: icon.ico")
            return True
        else:
            raise Exception(f"Shortcut not created. stderr: {result.stderr}")

    except Exception as e:
        print(f"       Note: PowerShell method failed: {e}")

    # Method 2: Try using pywin32
    try:
        from win32com.client import Dispatch
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = bat_path
        shortcut.WorkingDirectory = app_dir
        shortcut.Description = "Paper Search System"
        shortcut.WindowStyle = 1
        if os.path.exists(icon_path):
            shortcut.IconLocation = icon_path
        shortcut.save()
        print(f"       Desktop shortcut created: Paper Search.lnk")
        if os.path.exists(icon_path):
            print(f"       Icon applied: icon.ico")
        return True
    except ImportError:
        pass  # pywin32 not available
    except Exception as e:
        print(f"       Note: pywin32 method failed: {e}")

    # Method 3: Use VBScript with proper escaping
    try:
        vbs_path = os.path.join(app_dir, "temp_shortcut.vbs")

        # Escape paths for VBScript (double quotes inside string)
        def vbs_escape(s):
            return s.replace('"', '""')

        vbs_content = 'Set oWS = WScript.CreateObject("WScript.Shell")\n'
        vbs_content += 'Set oLink = oWS.CreateShortcut("' + vbs_escape(shortcut_path) + '")\n'
        vbs_content += 'oLink.TargetPath = "' + vbs_escape(bat_path) + '"\n'
        vbs_content += 'oLink.WorkingDirectory = "' + vbs_escape(app_dir) + '"\n'
        vbs_content += 'oLink.Description = "Paper Search System"\n'
        vbs_content += 'oLink.WindowStyle = 1\n'
        if os.path.exists(icon_path):
            vbs_content += 'oLink.IconLocation = "' + vbs_escape(icon_path) + '"\n'
        vbs_content += 'oLink.Save\n'

        # Write VBS file with system default encoding
        with open(vbs_path, 'w', encoding='mbcs') as f:
            f.write(vbs_content)

        # Run VBS script
        result = subprocess.run(
            ['cscript', '//nologo', vbs_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Clean up
        if os.path.exists(vbs_path):
            os.remove(vbs_path)

        if os.path.exists(shortcut_path):
            print(f"       Desktop shortcut created: Paper Search.lnk")
            if os.path.exists(icon_path):
                print(f"       Icon applied: icon.ico")
            return True
        else:
            raise Exception(f"VBScript failed. stderr: {result.stderr}")

    except Exception as e:
        print(f"       Note: VBScript method failed: {e}")
        # Clean up VBS file if exists
        vbs_path = os.path.join(app_dir, "temp_shortcut.vbs")
        if os.path.exists(vbs_path):
            try:
                os.remove(vbs_path)
            except:
                pass

    # All methods failed
    print(f"       [WARNING] Could not create desktop shortcut automatically.")
    print(f"")
    print(f"       To create manually:")
    print(f"       1. Right-click on desktop -> New -> Shortcut")
    print(f"       2. Enter path: {bat_path}")
    print(f"       3. Name it: Paper Search")
    if os.path.exists(icon_path):
        print(f"       4. Right-click shortcut -> Properties -> Change Icon -> {icon_path}")
    return False


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
        return True
    except Exception as e:
        print(f"       Launcher created: {launcher_path}")
        print(f"       You can drag it to Desktop or Dock")
        return False


def create_linux_shortcut():
    """Create Linux .desktop file."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    desktop = os.path.expanduser("~/Desktop")
    applications = os.path.expanduser("~/.local/share/applications")
    icon_path = os.path.join(app_dir, "icon.ico")

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
    if os.path.exists(icon_path):
        desktop_entry += f'Icon={icon_path}\n'

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
    return True


def main():
    system = platform.system()

    if system == 'Windows':
        return create_windows_shortcut()
    elif system == 'Darwin':
        return create_macos_shortcut()
    elif system == 'Linux':
        return create_linux_shortcut()
    else:
        print(f"       Unsupported platform: {system}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
