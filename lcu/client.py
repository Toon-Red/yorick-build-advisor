"""LCU (League Client Update) API client.

Reads the lockfile for connection info, provides authenticated HTTP client.
Handles reconnection when the client restarts (port/token change).
"""

import base64
import logging
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass
import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import LOCKFILE_PATH

log = logging.getLogger("lcu.client")


@dataclass
class LCUCredentials:
    protocol: str
    host: str
    port: int
    token: str
    pid: int

    @property
    def base_url(self) -> str:
        return f"{self.protocol}://127.0.0.1:{self.port}"

    @property
    def auth_header(self) -> str:
        encoded = base64.b64encode(f"riot:{self.token}".encode()).decode()
        return f"Basic {encoded}"


def _is_process_alive(pid: int) -> bool:
    """Check if a Windows process is alive."""
    if sys.platform != "win32":
        return True  # Can't check on non-Windows
    try:
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    except Exception:
        return True  # Assume alive if we can't check


class LCUClient:
    def __init__(self, lockfile_path: Path = LOCKFILE_PATH):
        self.lockfile_path = lockfile_path
        self._creds: LCUCredentials | None = None
        self._client: httpx.AsyncClient | None = None
        self._lockfile_missing_logged: bool = False

    @property
    def connected(self) -> bool:
        return self._creds is not None and self._client is not None

    def read_lockfile(self) -> LCUCredentials | None:
        """Parse the lockfile. Returns None if client isn't running."""
        try:
            text = self.lockfile_path.read_text().strip()
            parts = text.split(":")
            if len(parts) < 5:
                log.warning("Lockfile has fewer than 5 parts: %s", parts)
                return None
            creds = LCUCredentials(
                protocol=parts[4],
                host="127.0.0.1",
                port=int(parts[2]),
                token=parts[3],
                pid=int(parts[1]),
            )
            log.debug("Lockfile parsed: port=%d pid=%d", creds.port, creds.pid)
            self._lockfile_missing_logged = False  # Reset so we log again if it disappears later
            return creds
        except FileNotFoundError:
            if not self._lockfile_missing_logged:
                log.info("League client not running (no lockfile at %s)", self.lockfile_path)
                self._lockfile_missing_logged = True
            return None
        except (ValueError, IndexError) as e:
            log.warning("Lockfile parse error: %s", e)
            return None

    async def _close_client(self):
        """Safely close existing httpx client."""
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None

    async def connect(self) -> bool:
        """Try to connect to the LCU. Returns True if successful.

        Re-reads lockfile each time to catch port/token changes after
        client restart. Reuses existing connection if creds haven't changed.
        """
        creds = self.read_lockfile()
        if not creds:
            await self._close_client()
            self._creds = None
            return False

        # Check if PID is alive (lockfile can linger after crash)
        if not _is_process_alive(creds.pid):
            log.info("LCU PID %d no longer alive, lockfile stale", creds.pid)
            await self._close_client()
            self._creds = None
            return False

        # Reuse existing connection if creds match
        if (self._client and self._creds
                and self._creds.port == creds.port
                and self._creds.token == creds.token):
            # Quick health check on existing connection
            try:
                resp = await self._client.get("/riotclient/auth-token")
                if resp.status_code in (200, 403, 404):
                    return True  # Connection alive
            except Exception:
                log.debug("Existing connection failed, reconnecting")

        # New connection or reconnect needed
        await self._close_client()
        self._creds = creds
        self._client = httpx.AsyncClient(
            base_url=creds.base_url,
            headers={
                "Authorization": creds.auth_header,
                "Accept": "application/json",
            },
            verify=False,
            timeout=10,
        )

        try:
            resp = await self._client.get("/lol-summoner/v1/current-summoner")
            if resp.status_code == 200:
                log.info("Connected to LCU on port %d", creds.port)
                return True
            log.warning("LCU summoner endpoint returned %d", resp.status_code)
            # Don't tear down — the client may be in a transitional state
            # (loading, in-game). Keep the connection for endpoints that work.
            return True
        except httpx.ConnectError as e:
            log.warning("LCU connection refused on port %d: %s", creds.port, e)
            await self._close_client()
            self._creds = None
            return False
        except Exception as e:
            log.warning("LCU connection failed: %s", e)
            await self._close_client()
            self._creds = None
            return False

    async def disconnect(self):
        await self._close_client()
        self._creds = None

    async def get(self, path: str) -> httpx.Response | None:
        if not self._client:
            return None
        try:
            return await self._client.get(path)
        except Exception as e:
            log.debug("GET %s failed: %s", path, e)
            return None

    async def post(self, path: str, json: dict = None) -> httpx.Response | None:
        if not self._client:
            return None
        try:
            return await self._client.post(path, json=json)
        except Exception as e:
            log.debug("POST %s failed: %s", path, e)
            return None

    async def put(self, path: str, json: dict = None) -> httpx.Response | None:
        if not self._client:
            return None
        try:
            return await self._client.put(path, json=json)
        except Exception as e:
            log.debug("PUT %s failed: %s", path, e)
            return None

    async def patch(self, path: str, json: dict = None) -> httpx.Response | None:
        if not self._client:
            return None
        try:
            return await self._client.patch(path, json=json)
        except Exception as e:
            log.debug("PATCH %s failed: %s", path, e)
            return None

    async def delete(self, path: str) -> httpx.Response | None:
        if not self._client:
            return None
        try:
            return await self._client.delete(path)
        except Exception as e:
            log.debug("DELETE %s failed: %s", path, e)
            return None
