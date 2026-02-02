"""
Paper Search System - Version Information

To release a new version:
1. Update __version__ below
2. Commit and push to GitHub
3. Create a new release on GitHub with tag "v{version}"
"""

__version__ = "1.0.0"
__author__ = "YuyangZhan-econ"
__github__ = "https://github.com/yuyangzhan-econ/Paper-search-system-"
__release_date__ = "2024"

VERSION_INFO = {
    "version": __version__,
    "author": __author__,
    "github": __github__,
    "release_date": __release_date__,
    "name": "Paper Search System",
    "description": "Local paper management system with fuzzy search"
}


def get_version():
    """Return current version string."""
    return __version__


def get_version_info():
    """Return full version information dict."""
    return VERSION_INFO.copy()


def check_update_available():
    """Check if a newer version is available on GitHub."""
    import urllib.request
    import json

    try:
        repo_path = __github__.split('github.com/')[1].rstrip('/')
        api_url = f"https://api.github.com/repos/{repo_path}/releases/latest"
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Paper-Search'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            latest = data.get('tag_name', '').lstrip('v')
            if latest and latest != __version__:
                return {
                    'available': True,
                    'current': __version__,
                    'latest': latest,
                    'url': data.get('html_url', __github__)
                }
    except Exception:
        pass

    return {'available': False, 'current': __version__}
