#!/usr/bin/env python3
"""
Paper Search System - Desktop Application
Runs as a native desktop window without requiring a browser.
论文检索系统 - 桌面应用程序
"""

import sys
import os
import threading
import time
import socket

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


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
    print("论文检索系统启动中...")

    if not wait_for_server(port):
        print("Error: Server failed to start")
        sys.exit(1)

    # Create native window
    window = webview.create_window(
        title='Paper Search - 论文检索系统',
        url=f'http://127.0.0.1:{port}/',
        width=1400,
        height=900,
        min_size=(1000, 700),
        resizable=True,
        text_select=True,
        confirm_close=False,
    )

    # Start webview (this blocks until window is closed)
    webview.start(
        debug=False,
        http_server=False,
    )


if __name__ == '__main__':
    main()
