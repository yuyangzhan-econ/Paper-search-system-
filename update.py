#!/usr/bin/env python3
"""
Paper Search System - Updater
Downloads and installs the latest version while preserving user data.
"""

import os
import sys
import shutil
import tempfile
import zipfile
import json
import urllib.request
import urllib.error
from datetime import datetime

# Configuration
GITHUB_REPO = "yuyangzhan-econ/Paper-search-system-"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_ZIP_URL = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/main.zip"

# Files/folders to preserve during update
PRESERVE_LIST = [
    "data",           # Database folder
    "data/papers.db", # Database file
    "venv",           # Virtual environment
    "icon.ico",       # User's custom icon
]

# Files to never overwrite if they exist
KEEP_IF_EXISTS = [
    "icon.ico",
]

APP_DIR = os.path.dirname(os.path.abspath(__file__))


def get_current_version():
    """Get current installed version."""
    try:
        from version import __version__
        return __version__
    except ImportError:
        return "unknown"


def get_latest_release_info():
    """Get latest release info from GitHub API."""
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={'User-Agent': 'Paper-Search-Updater'}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            return {
                'version': data.get('tag_name', '').lstrip('v'),
                'name': data.get('name', ''),
                'body': data.get('body', ''),
                'download_url': data.get('zipball_url', GITHUB_ZIP_URL),
                'published_at': data.get('published_at', ''),
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # No releases yet, use main branch
            return {
                'version': 'latest',
                'name': 'Latest from main branch',
                'body': '',
                'download_url': GITHUB_ZIP_URL,
                'published_at': '',
            }
        raise
    except Exception as e:
        print(f"Error fetching release info: {e}")
        return None


def download_file(url, dest_path, progress_callback=None):
    """Download a file with progress reporting."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Paper-Search-Updater'})
        with urllib.request.urlopen(req, timeout=120) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            block_size = 8192

            with open(dest_path, 'wb') as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    f.write(buffer)
                    downloaded += len(buffer)
                    if progress_callback and total_size > 0:
                        progress_callback(downloaded, total_size)

        return True
    except Exception as e:
        print(f"Download error: {e}")
        return False


def backup_data():
    """Backup user data before update."""
    backup_dir = os.path.join(APP_DIR, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    try:
        os.makedirs(backup_dir, exist_ok=True)

        for item in PRESERVE_LIST:
            src = os.path.join(APP_DIR, item)
            if os.path.exists(src):
                dst = os.path.join(backup_dir, item)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

        print(f"       Backup created: {backup_dir}")
        return backup_dir
    except Exception as e:
        print(f"       Backup failed: {e}")
        return None


def extract_update(zip_path, target_dir):
    """Extract update ZIP, handling nested directory structure."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # GitHub ZIPs have a root folder like "repo-branch/"
            # We need to extract contents without this root folder
            root_folder = None
            for name in zf.namelist():
                parts = name.split('/')
                if len(parts) > 1 and not root_folder:
                    root_folder = parts[0] + '/'
                    break

            for member in zf.namelist():
                # Skip the root folder
                if root_folder and member.startswith(root_folder):
                    relative_path = member[len(root_folder):]
                else:
                    relative_path = member

                if not relative_path:
                    continue

                # Check if this should be preserved
                should_preserve = False
                for preserve in PRESERVE_LIST:
                    if relative_path == preserve or relative_path.startswith(preserve + '/'):
                        should_preserve = True
                        break

                # Check if should keep existing
                target_path = os.path.join(target_dir, relative_path)
                for keep in KEEP_IF_EXISTS:
                    if relative_path == keep and os.path.exists(target_path):
                        should_preserve = True
                        break

                if should_preserve:
                    continue

                # Extract
                if member.endswith('/'):
                    os.makedirs(target_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zf.open(member) as src, open(target_path, 'wb') as dst:
                        dst.write(src.read())

        return True
    except Exception as e:
        print(f"Extraction error: {e}")
        return False


def update():
    """Main update function."""
    print()
    print("=" * 60)
    print("           Paper Search System - Updater")
    print("=" * 60)
    print()

    # Check current version
    current_version = get_current_version()
    print(f"[1/5] Current version: v{current_version}")
    print()

    # Check for updates
    print("[2/5] Checking for updates...")
    release_info = get_latest_release_info()

    if not release_info:
        print("       Failed to check for updates.")
        print("       Please check your internet connection.")
        return False

    latest_version = release_info['version']
    print(f"       Latest version: v{latest_version}")

    if latest_version != 'latest' and current_version == latest_version:
        print()
        print("       You already have the latest version!")
        return True

    print()
    print(f"       Update available: v{current_version} -> v{latest_version}")
    if release_info.get('name'):
        print(f"       Release: {release_info['name']}")
    print()

    # Confirm update
    response = input("       Do you want to update? (y/n): ").strip().lower()
    if response not in ['y', 'yes']:
        print("       Update cancelled.")
        return False

    print()

    # Backup data
    print("[3/5] Backing up user data...")
    backup_dir = backup_data()
    if not backup_dir:
        print("       Warning: Backup failed, but continuing with update...")
    print()

    # Download update
    print("[4/5] Downloading update...")
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "update.zip")

    def progress(downloaded, total):
        percent = (downloaded / total) * 100
        bar = '=' * int(percent / 2) + '>' + ' ' * (50 - int(percent / 2))
        print(f"\r       [{bar}] {percent:.1f}%", end='', flush=True)

    success = download_file(release_info['download_url'], zip_path, progress)
    print()  # New line after progress bar

    if not success:
        print("       Download failed!")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return False

    print("       Download complete.")
    print()

    # Extract and install
    print("[5/5] Installing update...")
    success = extract_update(zip_path, APP_DIR)

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

    if not success:
        print("       Installation failed!")
        if backup_dir:
            print(f"       Your backup is at: {backup_dir}")
        return False

    print("       Installation complete.")
    print()

    # Update dependencies if needed
    print("       Updating dependencies...")
    requirements_path = os.path.join(APP_DIR, "requirements.txt")
    if os.path.exists(requirements_path):
        venv_pip = os.path.join(APP_DIR, "venv", "Scripts", "pip.exe")
        if os.path.exists(venv_pip):
            os.system(f'"{venv_pip}" install -r "{requirements_path}" --quiet')
        else:
            os.system(f'pip install -r "{requirements_path}" --quiet')
    print()

    print("=" * 60)
    print("                   Update Complete!")
    print("=" * 60)
    print()
    print(f"       Updated from v{current_version} to v{latest_version}")
    print()
    print("       Your data has been preserved:")
    print("       - Database (papers.db)")
    print("       - Settings and configurations")
    print()
    if backup_dir:
        print(f"       Backup location: {backup_dir}")
        print()
    print("       Please restart the application to use the new version.")
    print()

    return True


def main():
    try:
        success = update()
    except KeyboardInterrupt:
        print("\n\nUpdate cancelled by user.")
        success = False
    except Exception as e:
        print(f"\nError during update: {e}")
        import traceback
        traceback.print_exc()
        success = False

    print()
    input("Press Enter to exit...")
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
