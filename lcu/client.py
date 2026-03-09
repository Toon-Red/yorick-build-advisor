"""LCU (League Client Update) API client.

Reads the lockfile for connection info, provides authenticated HTTP client.
"""

import base64
from pathlib import Path
from dataclasses import dataclass
import httpx

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import LOCKFILE_PATH


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


class LCUClient:
    def __init__(self, lockfile_path: Path = LOCKFILE_PATH):
        self.lockfile_path = lockfile_path
        self._creds: LCUCredentials | None = None
        self._client: httpx.AsyncClient | None = None

    @property
    def connected(self) -> bool:
        return self._creds is not None and self._client is not None

    def read_lockfile(self) -> LCUCredentials | None:
        """Parse the lockfile. Returns None if client isn't running."""
        try:
            text = self.lockfile_path.read_text().strip()
            parts = text.split(":")
            if len(parts) < 5:
                return None
            return LCUCredentials(
                protocol=parts[4],
                host="127.0.0.1",
                port=int(parts[2]),
                token=parts[3],
                pid=int(parts[1]),
            )
        except (FileNotFoundError, ValueError, IndexError):
            return None

    async def connect(self) -> bool:
        """Try to connect to the LCU. Returns True if successful."""
        creds = self.read_lockfile()
        if not creds:
            self._creds = None
            self._client = None
            return False

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
            return resp.status_code == 200
        except Exception:
            self._creds = None
            self._client = None
            return False

    async def disconnect(self):
        if self._client:
            await self._client.aclose()
        self._creds = None
        self._client = None

    async def get(self, path: str) -> httpx.Response | None:
        if not self._client:
            return None
        try:
            return await self._client.get(path)
        except Exception:
            return None

    async def post(self, path: str, json: dict = None) -> httpx.Response | None:
        if not self._client:
            return None
        try:
            return await self._client.post(path, json=json)
        except Exception:
            return None

    async def put(self, path: str, json: dict = None) -> httpx.Response | None:
        if not self._client:
            return None
        try:
            return await self._client.put(path, json=json)
        except Exception:
            return None

    async def patch(self, path: str, json: dict = None) -> httpx.Response | None:
        if not self._client:
            return None
        try:
            return await self._client.patch(path, json=json)
        except Exception:
            return None

    async def delete(self, path: str) -> httpx.Response | None:
        if not self._client:
            return None
        try:
            return await self._client.delete(path)
        except Exception:
            return None
