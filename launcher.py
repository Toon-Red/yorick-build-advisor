"""Standalone launcher for Yorick Build Advisor.

Starts the API server, then opens Edge in app mode (no address bar, looks native).
Pinnable to taskbar like Porofessor.
"""
import sys
import os

# Redirect stderr/stdout to log file for windowed exe debugging
if getattr(sys, 'frozen', False) and not sys.stderr:
    _log_dir = os.path.join(os.environ.get('LOCALAPPDATA', '.'), 'YorickBuildAdvisor')
    os.makedirs(_log_dir, exist_ok=True)
    _log = open(os.path.join(_log_dir, 'crash.log'), 'w')
    sys.stdout = _log
    sys.stderr = _log

import ctypes
import socket
import subprocess
import threading
import time
import shutil

# Hide subprocess console windows on Windows
_SUBPROCESS_FLAGS = 0
if sys.platform == 'win32':
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW

# App identity for Windows taskbar pinning
APP_ID = u'Yorick.BuildAdvisor.1.0'
if sys.platform == 'win32':
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)

# When running as PyInstaller bundle, set the working directory
if getattr(sys, '_MEIPASS', None):
    os.chdir(sys._MEIPASS)

import uvicorn
from config import API_HOST, API_PORT


def get_install_dir():
    """Permanent install location for the exe."""
    return os.path.join(os.environ.get('LOCALAPPDATA', ''), 'YorickBuildAdvisor')


def ensure_installed():
    """Copy exe to permanent location if not already in a proper install dir."""
    if not getattr(sys, 'frozen', False):
        return  # Dev mode, skip
    current_dir = os.path.normcase(os.path.dirname(sys.executable))
    if 'program files' in current_dir or os.path.normcase(get_install_dir()) == current_dir:
        return

    install_dir = get_install_dir()
    os.makedirs(install_dir, exist_ok=True)
    try:
        shutil.copy2(sys.executable, os.path.join(install_dir, 'YorickBuildAdvisor.exe'))
    except Exception:
        pass


def ensure_shortcut():
    """Create a Start Menu shortcut with AppUserModelID for taskbar pinning."""
    if not getattr(sys, 'frozen', False):
        return  # Dev mode, skip

    import pythoncom
    from win32com.shell import shell, shellcon
    from win32com.propsys import propsys, pscon

    start_menu = os.path.join(
        os.environ.get('APPDATA', ''),
        'Microsoft', 'Windows', 'Start Menu', 'Programs'
    )
    shortcut_path = os.path.join(start_menu, 'Yorick Build Advisor.lnk')

    install_dir = get_install_dir()
    exe_path = os.path.join(install_dir, 'YorickBuildAdvisor.exe')
    if not os.path.exists(exe_path):
        exe_path = sys.executable

    icon_path = exe_path

    sl = pythoncom.CoCreateInstance(
        shell.CLSID_ShellLink, None,
        pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
    )
    sl.SetPath(exe_path)
    sl.SetWorkingDirectory(os.path.dirname(exe_path))
    sl.SetIconLocation(icon_path, 0)
    sl.SetDescription("Yorick Build Advisor")

    pf = sl.QueryInterface(pythoncom.IID_IPersistFile)
    pf.Save(shortcut_path, 0)

    store = propsys.SHGetPropertyStoreFromParsingName(
        shortcut_path, None,
        shellcon.GPS_READWRITE, propsys.IID_IPropertyStore
    )
    store.SetValue(
        pscon.PKEY_AppUserModel_ID,
        propsys.PROPVARIANTType(APP_ID, pythoncom.VT_LPWSTR)
    )
    store.Commit()


def is_port_listening(port):
    """Check if something is actively LISTENING on the port (not just TIME_WAIT)."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"(Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue "
             f"| Where-Object {{ $_.State -eq 'Listen' }}).Count"],
            capture_output=True, text=True, timeout=5,
            creationflags=_SUBPROCESS_FLAGS
        )
        return int(result.stdout.strip() or '0') > 0
    except Exception:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex((API_HOST, port)) == 0


def kill_existing_server():
    try:
        subprocess.run(
            ["powershell", "-Command",
             "Get-Process -Name YorickBuildAdvisor -ErrorAction SilentlyContinue "
             "| Where-Object { $_.Id -ne $PID } "
             "| Stop-Process -Force -ErrorAction SilentlyContinue"],
            capture_output=True, timeout=5,
            creationflags=_SUBPROCESS_FLAGS
        )
    except Exception:
        pass
    try:
        subprocess.run(
            ["powershell", "-Command",
             f"Get-NetTCPConnection -LocalPort {API_PORT} -ErrorAction SilentlyContinue "
             f"| Where-Object {{ $_.State -eq 'Listen' }} "
             f"| ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}"],
            capture_output=True, timeout=5,
            creationflags=_SUBPROCESS_FLAGS
        )
    except Exception:
        pass
    for _ in range(20):
        if not is_port_listening(API_PORT):
            return True
        time.sleep(0.5)
    return False


def start_server():
    """Start uvicorn with retry logic for TIME_WAIT ports."""
    from app import app as fastapi_app

    import uvicorn.config
    import uvicorn.server

    _orig_bind = socket.socket.bind

    def _reuse_bind(self, address):
        try:
            self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception:
            pass
        return _orig_bind(self, address)

    socket.socket.bind = _reuse_bind

    try:
        for attempt in range(30):
            try:
                config = uvicorn.config.Config(
                    fastapi_app, host=API_HOST, port=API_PORT,
                    reload=False, log_level="warning"
                )
                server = uvicorn.server.Server(config)
                server.run()
                break
            except SystemExit:
                time.sleep(1)
            except Exception:
                time.sleep(1)
    finally:
        socket.socket.bind = _orig_bind


def wait_for_server(timeout=30):
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"http://{API_HOST}:{API_PORT}/api/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def find_edge():
    """Find Microsoft Edge executable."""
    candidates = [
        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def open_app_window(url):
    """Open the app in Edge --app mode (no address bar, looks native)."""
    edge = find_edge()
    if edge:
        # Separate user data dir so it doesn't conflict with normal Edge
        app_data = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'YorickBuildAdvisor', 'edge-data')
        subprocess.Popen([
            edge,
            f"--app={url}",
            f"--user-data-dir={app_data}",
            "--new-window",
            f"--window-size=1050,800",
        ], creationflags=_SUBPROCESS_FLAGS)
        return True

    # Fallback: open in default browser
    import webbrowser
    webbrowser.open(url)
    return True


if __name__ == "__main__":
    # Install exe to permanent location + create Start Menu shortcut for taskbar pinning
    try:
        ensure_installed()
        ensure_shortcut()
    except Exception:
        pass  # Non-fatal, app still works

    if is_port_listening(API_PORT):
        kill_existing_server()

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    if not wait_for_server():
        print("Failed to start server", file=sys.stderr)
        sys.exit(1)

    url = f"http://{API_HOST}:{API_PORT}/"
    open_app_window(url)

    # Keep the process alive while the server runs
    # (server thread is daemon, so it'll exit when main exits)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
