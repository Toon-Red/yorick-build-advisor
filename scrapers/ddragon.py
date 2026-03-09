"""Data Dragon CDN loader - champion, item, and rune data from Riot."""

import json
from pathlib import Path
import requests

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DDRAGON_BASE, DDRAGON_VERSIONS_URL, DDRAGON_DIR


class DataDragon:
    def __init__(self):
        self.version = None
        self.champions = {}      # name -> {id, key, name, title, tags}
        self.champion_by_key = {}  # numeric key -> name
        self.items = {}          # id_str -> {name, description, ...}
        self.runes = {}          # id -> {name, icon, ...}
        self.rune_styles = {}    # style_id -> {name, slots, ...}

    def load(self):
        """Load or download all Data Dragon data."""
        self.version = self._get_latest_version()
        version_dir = DDRAGON_DIR / self.version
        version_dir.mkdir(exist_ok=True)

        self._load_champions(version_dir)
        self._load_items(version_dir)
        self._load_runes(version_dir)

    def _get_latest_version(self) -> str:
        cache_file = DDRAGON_DIR / "current_version.txt"
        try:
            resp = requests.get(DDRAGON_VERSIONS_URL, timeout=5)
            resp.raise_for_status()
            version = resp.json()[0]
            cache_file.write_text(version)
            return version
        except Exception:
            if cache_file.exists():
                return cache_file.read_text().strip()
            return "15.4.1"  # fallback

    def _fetch_or_cache(self, url: str, cache_path: Path) -> dict:
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    def _load_champions(self, version_dir: Path):
        url = f"{DDRAGON_BASE}/{self.version}/data/en_US/champion.json"
        data = self._fetch_or_cache(url, version_dir / "champion.json")
        for name, info in data["data"].items():
            self.champions[name] = {
                "id": info["id"],
                "key": int(info["key"]),
                "name": info["name"],
                "title": info["title"],
                "tags": info.get("tags", []),
            }
            self.champion_by_key[int(info["key"])] = info["name"]

    def _load_items(self, version_dir: Path):
        url = f"{DDRAGON_BASE}/{self.version}/data/en_US/item.json"
        data = self._fetch_or_cache(url, version_dir / "item.json")
        for item_id, info in data["data"].items():
            self.items[item_id] = {
                "id": int(item_id),
                "name": info["name"],
                "description": info.get("plaintext", ""),
                "gold": info.get("gold", {}).get("total", 0),
                "tags": info.get("tags", []),
            }

    def _load_runes(self, version_dir: Path):
        url = f"{DDRAGON_BASE}/{self.version}/data/en_US/runesReforged.json"
        data = self._fetch_or_cache(url, version_dir / "runesReforged.json")
        for style in data:
            style_id = style["id"]
            self.rune_styles[style_id] = {
                "id": style_id,
                "name": style["name"],
                "icon": style["icon"],
            }
            for slot in style["slots"]:
                for rune in slot["runes"]:
                    self.runes[rune["id"]] = {
                        "id": rune["id"],
                        "name": rune["name"],
                        "icon": rune["icon"],
                        "style_id": style_id,
                        "style_name": style["name"],
                    }

    # Lookup helpers
    def champion_name(self, key: int) -> str:
        return self.champion_by_key.get(key, f"Unknown({key})")

    def champion_key(self, name: str) -> int | None:
        for cname, info in self.champions.items():
            if cname.lower() == name.lower() or info["name"].lower() == name.lower():
                return info["key"]
        return None

    def item_name(self, item_id: int) -> str:
        return self.items.get(str(item_id), {}).get("name", f"Unknown({item_id})")

    def rune_name(self, rune_id: int) -> str:
        return self.runes.get(rune_id, {}).get("name", f"Unknown({rune_id})")

    def rune_id_by_name(self, name: str) -> int | None:
        name_lower = name.lower().strip()
        for rid, info in self.runes.items():
            if info["name"].lower() == name_lower:
                return rid
        return None

    def item_id_by_name(self, name: str) -> int | None:
        name_lower = name.lower().strip()
        for iid, info in self.items.items():
            if info["name"].lower() == name_lower:
                return int(iid)
        return None

    # URL builders
    def champion_portrait_url(self, name: str) -> str:
        return f"{DDRAGON_BASE}/{self.version}/img/champion/{name}.png"

    def item_icon_url(self, item_id: int) -> str:
        return f"{DDRAGON_BASE}/{self.version}/img/item/{item_id}.png"

    def rune_icon_url(self, rune_id: int) -> str:
        icon = self.runes.get(rune_id, {}).get("icon", "")
        if icon:
            return f"{DDRAGON_BASE}/img/{icon}"
        return ""

    def style_icon_url(self, style_id: int) -> str:
        icon = self.rune_styles.get(style_id, {}).get("icon", "")
        if icon:
            return f"{DDRAGON_BASE}/img/{icon}"
        return ""

    def summary(self) -> dict:
        return {
            "version": self.version,
            "champions": len(self.champions),
            "items": len(self.items),
            "runes": len(self.runes),
            "rune_styles": len(self.rune_styles),
        }
