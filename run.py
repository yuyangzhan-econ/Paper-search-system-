#!/usr/bin/env python3
"""
Paper Search System - Launcher Script
Run this script to start the application.
"""

import sys
import os
import subprocess


def check_dependencies():
    """Check if all required packages are installed."""
    required = ['flask', 'flask_cors', 'pypdf', 'pypinyin', 'jieba', 'requests', 'bs4']
    missing = []

    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    return missing


def install_dependencies():
    """Install missing dependencies."""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])


def main():
    # Check for missing dependencies
    missing = check_dependencies()

    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        response = input("Do you want to install them now? (y/n): ")
        if response.lower() == 'y':
            install_dependencies()
        else:
            print("Please install dependencies manually: pip install -r requirements.txt")
            sys.exit(1)

    # Import and run the app
    from app import app

    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                  Paper Search System                       ║
    ║                     论文检索系统                            ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  打开浏览器访问: http://localhost:5000                      ║
    ║  Open browser:   http://localhost:5000                     ║
    ║                                                            ║
    ║  按 Ctrl+C 退出 / Press Ctrl+C to quit                     ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()
