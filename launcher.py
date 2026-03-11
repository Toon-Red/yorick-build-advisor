"""Desktop launcher for Yorick Build Advisor.

Uses pywebview (WebView2) for a native window — not a browser.
Installs to %LOCALAPPDATA%, creates Start Menu shortcut with AppUserModelID,
so Windows treats it as a real app you can pin to the taskbar.
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

from config import API_HOST, API_PORT

# Explicit imports so PyInstaller traces the full dependency chain.
# These are used dynamically in start_server() but PyInstaller can't see that.
import app  # noqa: F401
import uvicorn  # noqa: F401


def get_install_dir():
    """Permanent install location for the exe."""
    return os.path.join(os.environ.get('LOCALAPPDATA', ''), 'YorickBuildAdvisor')


def ensure_installed():
    """Copy exe to permanent location and relaunch from there.

    Returns True if we need to relaunch (caller should exit).
    Returns False if already in the right place or dev mode.
    """
    if not getattr(sys, 'frozen', False):
        return False  # Dev mode, skip

    install_dir = get_install_dir()
    installed_exe = os.path.join(install_dir, 'YorickBuildAdvisor.exe')
    current = os.path.normcase(os.path.abspath(sys.executable))
    target = os.path.normcase(os.path.abspath(installed_exe))

    if current == target:
        return False  # Already running from install dir

    os.makedirs(install_dir, exist_ok=True)
    try:
        shutil.copy2(sys.executable, installed_exe)
    except Exception:
        return False  # Copy failed, just run from current location

    # Relaunch from installed location so Windows associates
    # the taskbar icon with the permanent path
    try:
        subprocess.Popen([installed_exe] + sys.argv[1:])
        return True  # Caller should sys.exit(0)
    except Exception:
        return False


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


if __name__ == "__main__":
    server_only = '--server-only' in sys.argv

    # Apply staged update before anything else (may exit + relaunch)
    try:
        from updater import check_and_apply_staged
        check_and_apply_staged()
    except Exception:
        pass

    # Install exe to permanent location + create Start Menu shortcut for taskbar pinning
    try:
        if ensure_installed():
            sys.exit(0)  # Relaunched from install dir, exit this copy
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

    if server_only:
        # CI smoke test mode: keep server alive without GUI
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        import webview

        url = f"http://{API_HOST}:{API_PORT}/"
        window = webview.create_window(
            'Yorick Build Advisor',
            url,
            width=1050,
            height=800,
            min_size=(800, 500),
        )

        # webview.start() blocks until the window is closed, then the process exits
        webview.start()
