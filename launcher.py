"""Standalone launcher for Yorick Build Advisor.

Opens a native WebView2 window with the app — pinnable to taskbar like Porofessor.
Window controls (min/max/close) go through HTTP endpoints on the local server.
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
import asyncio
import socket
import subprocess
import threading
import time
import queue
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
    # Skip if already in Program Files or LocalAppData install location
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

    # Get the installed exe path (permanent location)
    install_dir = get_install_dir()
    exe_path = os.path.join(install_dir, 'YorickBuildAdvisor.exe')
    if not os.path.exists(exe_path):
        exe_path = sys.executable  # Fallback to current

    icon_path = exe_path  # Use the exe's embedded icon

    # Create the .lnk
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

    # Stamp AppUserModelID on the shortcut
    store = propsys.SHGetPropertyStoreFromParsingName(
        shortcut_path, None,
        shellcon.GPS_READWRITE, propsys.IID_IPropertyStore
    )
    store.SetValue(
        pscon.PKEY_AppUserModel_ID,
        propsys.PROPVARIANTType(APP_ID, pythoncom.VT_LPWSTR)
    )
    store.Commit()

# Shared queue for window commands (thread-safe)
window_commands = queue.Queue()


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
        # Fallback to connect check
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
    # Inject window control endpoints into the FastAPI app before starting
    from app import app as fastapi_app
    from fastapi.responses import JSONResponse

    @fastapi_app.post("/api/window/{action}")
    async def window_control(action: str, body: dict = None):
        """Handle window control commands from the UI."""
        if action in ("minimize", "maximize", "close"):
            window_commands.put(action)
            return JSONResponse({"ok": True})
        elif action == "start_drag" and body:
            window_commands.put(("start_drag", body.get("x", 0), body.get("y", 0)))
            return JSONResponse({"ok": True})
        elif action == "do_drag" and body:
            window_commands.put(("do_drag", body.get("x", 0), body.get("y", 0)))
            return JSONResponse({"ok": True})
        return JSONResponse({"ok": False}, status_code=400)

    import uvicorn.config
    import uvicorn.server

    # Monkey-patch socket to always set SO_REUSEADDR (handles TIME_WAIT from previous instance)
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
        sys.exit(1)

    import win32gui
    import win32con
    import win32api
    from webview2 import Window
    from webview2.base import dll

    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "icon.ico")
    if getattr(sys, '_MEIPASS', None):
        icon_path = os.path.join(sys._MEIPASS, "static", "icon.ico")

    w = Window(
        title="Yorick Build Advisor",
        url=f"http://{API_HOST}:{API_PORT}/",
        size="1050x800",
        icon=icon_path if os.path.exists(icon_path) else None,
    )

    # Remove native title bar after window builds
    def remove_native_frame():
        time.sleep(0.8)
        try:
            hwnd = dll.get_window()
            if hwnd:
                style = win32api.GetWindowLong(hwnd, win32con.GWL_STYLE)
                style = style & ~win32con.WS_CAPTION
                style = style | win32con.WS_THICKFRAME
                win32api.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
                win32gui.SetWindowPos(
                    hwnd, None, 0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                    win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
                )
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        except Exception:
            pass

    threading.Thread(target=remove_native_frame, daemon=True).start()

    # Process window commands from the queue during the event loop
    drag_state = [0, 0]  # [start_x, start_y]

    async def run_with_commands():
        import pythoncom
        pythoncom.OleInitialize()
        import webview2 as _wv2mod
        _wv2_dir = os.path.dirname(_wv2mod.__file__)
        if getattr(sys, '_MEIPASS', None):
            _wv2_dir = os.path.join(sys._MEIPASS, "webview2")
        dll.preload(w._build_context(os.path.join(
            _wv2_dir, "webview2.js"
        )).encode(encoding='utf-8'))
        dll.build()

        while True:
            r = win32gui.PeekMessage(None, 0, 0, win32con.PM_REMOVE)
            code, msg = r
            if code == 0:
                # Process any pending window commands
                try:
                    while True:
                        cmd = window_commands.get_nowait()
                        hwnd = dll.get_window()
                        if cmd == "close":
                            win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                        elif cmd == "minimize":
                            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                        elif cmd == "maximize":
                            placement = win32gui.GetWindowPlacement(hwnd)
                            if placement[1] == win32con.SW_SHOWMAXIMIZED:
                                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            else:
                                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                        elif isinstance(cmd, tuple) and cmd[0] == "start_drag":
                            rect = win32gui.GetWindowRect(hwnd)
                            drag_state[0] = cmd[1] - rect[0]
                            drag_state[1] = cmd[2] - rect[1]
                        elif isinstance(cmd, tuple) and cmd[0] == "do_drag":
                            new_x = int(cmd[1] - drag_state[0])
                            new_y = int(cmd[2] - drag_state[1])
                            rect = win32gui.GetWindowRect(hwnd)
                            w2 = rect[2] - rect[0]
                            h2 = rect[3] - rect[1]
                            win32gui.MoveWindow(hwnd, new_x, new_y, w2, h2, True)
                except queue.Empty:
                    pass
                except Exception:
                    pass

                await asyncio.sleep(0.005)
                continue
            if msg[1] == win32con.WM_QUIT:
                break
            win32gui.TranslateMessage(msg)
            win32gui.DispatchMessage(msg)

        w.close()
        pythoncom.CoUninitialize()

    asyncio.run(run_with_commands())
    os._exit(0)
