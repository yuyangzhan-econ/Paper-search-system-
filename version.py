"""
Paper Search System - Version Information
"""

__version__ = "1.0.0"
__author__ = "YuyangZhan-econ"
__github__ = "https://github.com/yuyangzhan-econ/Paper-search-system-"

VERSION_INFO = {
    "version": __version__,
    "author": __author__,
    "github": __github__,
    "name": "Paper Search System",
    "description": "Local paper management system with fuzzy search"
}


def get_version():
    """Return current version string."""
    return __version__


def get_version_info():
    """Return full version information dict."""
    return VERSION_INFO.copy()
