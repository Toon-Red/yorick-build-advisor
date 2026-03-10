"""Guide profile manager — CRUD for decision tree guides.

Guides are stored as JSON files in data/guides/.
Each guide is a self-contained decision tree + data tables for one champion.
Multiple guides can exist per champion (e.g. different authors).
"""

import json
import os
import uuid
from pathlib import Path
from datetime import datetime, timezone


GUIDES_DIR = Path(__file__).parent / "data" / "guides"
GUIDES_DIR.mkdir(parents=True, exist_ok=True)

# Active guide tracking stored in user_config.json
_CONFIG_PATH = Path(__file__).parent / "data" / "user_config.json"


def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_config(cfg: dict):
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def list_guides() -> list[dict]:
    """List all guides with metadata (no tree data)."""
    guides = []
    for path in sorted(GUIDES_DIR.glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            guides.append({
                "guide_id": data.get("guide_id", path.stem),
                "guide_name": data.get("guide_name", path.stem),
                "champion": data.get("champion", "Unknown"),
                "author": data.get("author", "Unknown"),
                "file": path.name,
                "matchup_count": len(data.get("data", {}).get("matchups", {})),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return guides


def list_guides_for_champion(champion: str) -> list[dict]:
    """List all guides for a specific champion."""
    return [g for g in list_guides() if g["champion"].lower() == champion.lower()]


def load_guide(guide_id: str) -> dict | None:
    """Load a full guide JSON by guide_id."""
    for path in GUIDES_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("guide_id") == guide_id:
                return data
        except (json.JSONDecodeError, OSError):
            continue
    return None


def save_guide(guide: dict) -> str:
    """Save a guide JSON. Returns the guide_id."""
    guide_id = guide.get("guide_id")
    if not guide_id:
        guide_id = f"{guide.get('champion', 'unknown').lower()}-{uuid.uuid4().hex[:8]}"
        guide["guide_id"] = guide_id

    guide["updated_at"] = datetime.now(timezone.utc).isoformat()
    if "created_at" not in guide:
        guide["created_at"] = guide["updated_at"]

    # Try to find existing file with this guide_id and overwrite it
    path = None
    for existing_path in GUIDES_DIR.glob("*.json"):
        try:
            with open(existing_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if existing.get("guide_id") == guide_id:
                path = existing_path
                break
        except (json.JSONDecodeError, OSError):
            continue

    # Fallback: create new file named by guide_id
    if path is None:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in guide_id)
        path = GUIDES_DIR / f"{safe_name}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(guide, f, indent=2)

    return guide_id


def delete_guide(guide_id: str) -> bool:
    """Delete a guide by guide_id. Returns True if found and deleted."""
    for path in GUIDES_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("guide_id") == guide_id:
                path.unlink()
                # Remove from active if it was active
                cfg = _load_config()
                active = cfg.get("active_guides", {})
                for champ, gid in list(active.items()):
                    if gid == guide_id:
                        del active[champ]
                if active != cfg.get("active_guides", {}):
                    cfg["active_guides"] = active
                    _save_config(cfg)
                return True
        except (json.JSONDecodeError, OSError):
            continue
    return False


def get_active_guide_id(champion: str) -> str | None:
    """Get the active guide_id for a champion."""
    cfg = _load_config()
    return cfg.get("active_guides", {}).get(champion)


def set_active_guide(champion: str, guide_id: str):
    """Set the active guide for a champion."""
    cfg = _load_config()
    if "active_guides" not in cfg:
        cfg["active_guides"] = {}
    cfg["active_guides"][champion] = guide_id
    _save_config(cfg)


def get_active_guide(champion: str) -> dict | None:
    """Load the active guide for a champion. Falls back to first available."""
    guide_id = get_active_guide_id(champion)
    if guide_id:
        guide = load_guide(guide_id)
        if guide:
            return guide

    # Fallback: first guide for this champion
    guides = list_guides_for_champion(champion)
    if guides:
        return load_guide(guides[0]["guide_id"])

    return None


def import_guide(json_data: dict) -> str:
    """Import a guide from JSON data. Returns guide_id."""
    # Ensure it has required fields
    if "data" not in json_data or "root" not in json_data:
        raise ValueError("Invalid guide format: missing 'data' or 'root'")

    # Generate new guide_id if importing a duplicate
    existing = load_guide(json_data.get("guide_id", ""))
    if existing:
        json_data["guide_id"] = f"{json_data.get('guide_id', 'imported')}-{uuid.uuid4().hex[:6]}"

    return save_guide(json_data)


def export_guide(guide_id: str) -> dict | None:
    """Export a guide as JSON (same as load, but semantically for sharing)."""
    return load_guide(guide_id)
