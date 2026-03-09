"""Auto-updater that checks GitHub releases and downloads new versions."""
import os
import sys
import json
import subprocess
import tempfile
import threading
import urllib.request

APP_VERSION = "1.0.0"
GITHUB_REPO = "Toon-Red/yorick-build-advisor"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# Hide subprocess windows
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0


def get_latest_release():
    """Check GitHub for the latest release. Returns (version, installer_url) or None."""
    try:
        req = urllib.request.Request(RELEASES_URL, headers={"User-Agent": "YorickBuildAdvisor"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        tag = data.get("tag_name", "").lstrip("v")
        if not tag:
            return None
        # Find the installer asset
        for asset in data.get("assets", []):
            if asset["name"].endswith("_Setup.exe"):
                return (tag, asset["browser_download_url"])
        return None
    except Exception:
        return None


def is_newer(latest, current):
    """Compare version strings like '1.2.3'."""
    try:
        latest_parts = [int(x) for x in latest.split(".")]
        current_parts = [int(x) for x in current.split(".")]
        return latest_parts > current_parts
    except Exception:
        return False


def download_and_run_installer(url):
    """Download installer to temp and run it."""
    try:
        tmp = os.path.join(tempfile.gettempdir(), "YorickBuildAdvisor_Setup.exe")
        urllib.request.urlretrieve(url, tmp)
        # Launch installer and exit current app
        subprocess.Popen(
            [tmp, "/SILENT", "/NORESTART"],
            creationflags=_NO_WINDOW
        )
        os._exit(0)
    except Exception:
        pass


def check_for_updates_async(callback):
    """Check for updates in background thread. Calls callback(version, url) if update available."""
    def _check():
        result = get_latest_release()
        if result and is_newer(result[0], APP_VERSION):
            callback(result[0], result[1])
    threading.Thread(target=_check, daemon=True).start()
