#!/usr/bin/env python3
"""
Paper Search System - Desktop Application
Runs as a native desktop window without requiring a browser.
"""

import sys
import os
import threading
import time
import socket
import platform
import inspect

# Add current directory to path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

# Icon path
ICON_PATH = os.path.join(APP_DIR, "icon.ico")


def find_free_port():
    """Find a free port to use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def run_flask_server(port):
    """Run Flask server in background thread."""
    import logging

    # Suppress Flask logs
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    from app import app
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


def wait_for_server(port, timeout=30):
    """Wait for server to be ready."""
    import urllib.request

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/')
            return True
        except Exception:
            time.sleep(0.1)
    return False


def set_windows_icon(icon_path):
    """Set taskbar icon on Windows using ctypes."""
    if platform.system() != 'Windows':
        return

    try:
        import ctypes
        from ctypes import wintypes

        # Constants
        ICON_SMALL = 0
        ICON_BIG = 1
        WM_SETICON = 0x0080
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x0010
        LR_DEFAULTSIZE = 0x0040

        # Load functions
        user32 = ctypes.windll.user32
        LoadImageW = user32.LoadImageW
        LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
                               ctypes.c_int, ctypes.c_int, wintypes.UINT]
        LoadImageW.restype = wintypes.HANDLE

        # Load icon
        hicon = LoadImageW(None, icon_path, IMAGE_ICON, 0, 0,
                          LR_LOADFROMFILE | LR_DEFAULTSIZE)

        if hicon:
            # Find the window by title using closure
            found_windows = []

            def enum_windows_callback(hwnd, lParam):
                # Use closure to access found_windows list
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd) + 1
                    buf = ctypes.create_unicode_buffer(length)
                    user32.GetWindowTextW(hwnd, buf, length)
                    if 'Paper Search' in buf.value:
                        found_windows.append(hwnd)
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)

            for hwnd in found_windows:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)

    except Exception as e:
        pass  # Silently ignore icon setting errors


def main():
    """Main entry point for desktop application."""
    try:
        import webview
    except ImportError:
        print("="*60)
        print("ERROR: pywebview is not installed!")
        print("Please run: pip install pywebview")
        print("="*60)
        input("Press Enter to exit...")
        sys.exit(1)

    # Find free port
    port = find_free_port()

    # Start Flask server in background thread
    server_thread = threading.Thread(target=run_flask_server, args=(port,), daemon=True)
    server_thread.start()

    # Wait for server to start
    print("Starting Paper Search System...")

    if not wait_for_server(port):
        print("Error: Server failed to start")
        sys.exit(1)

    # Prepare window parameters
    window_params = {
        'title': 'Paper Search',
        'url': f'http://127.0.0.1:{port}/',
        'width': 1400,
        'height': 900,
        'min_size': (1000, 700),
        'resizable': True,
        'text_select': True,
        'confirm_close': False,
    }

    # Check if pywebview supports 'icon' parameter
    if os.path.exists(ICON_PATH):
        try:
            sig = inspect.signature(webview.create_window)
            if 'icon' in sig.parameters:
                window_params['icon'] = ICON_PATH
        except Exception:
            pass

    # Create native window
    window = webview.create_window(**window_params)

    # Set icon after window creation using Windows API (fallback)
    def on_loaded():
        if os.path.exists(ICON_PATH):
            time.sleep(0.8)  # Wait for window to fully load
            set_windows_icon(ICON_PATH)

    if os.path.exists(ICON_PATH):
        threading.Thread(target=on_loaded, daemon=True).start()

    # Start webview (this blocks until window is closed)
    webview.start(
        debug=False,
        http_server=False,
    )


if __name__ == '__main__':
    main()
