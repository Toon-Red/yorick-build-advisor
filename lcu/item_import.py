"""Import item sets into the LoL client via LCU API.

Also writes to Config/Champions/<name>/Recommended/ so the set
appears as a Recommended tab in the in-game shop (auto-selected).
"""

import json
import logging
from pathlib import Path

from lcu.client import LCUClient

log = logging.getLogger("lcu.item_import")

_V2_TITLE = "Build Advisor (v2)"
_V2_UID = "v2-build-advisor"
_V2_FILE = "!BuildAdvisor_v2.json"


def _get_lol_path() -> Path:
    """Get LoL install path from config."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import LOL_PATH
    return LOL_PATH


def _write_recommended_file(champion: str, champ_id: int, blocks: list):
    """Write item set to Config/Champions/<name>/Recommended/ for in-game auto-show."""
    try:
        lol_path = _get_lol_path()
        rec_dir = lol_path / "Config" / "Champions" / champion / "Recommended"
        rec_dir.mkdir(parents=True, exist_ok=True)

        # Remove old v2 files (catch both old and new naming)
        for f in rec_dir.glob("V2_*"):
            f.unlink(missing_ok=True)
        for f in rec_dir.glob("!BuildAdvisor*"):
            f.unlink(missing_ok=True)

        # Also remove any RIOT_ItemSet files that are our duplicates
        # (LCU API syncs sets here with sortrank=9999, creating conflicts)
        for f in rec_dir.glob("RIOT_ItemSet_*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("uid") == _V2_UID or data.get("title") in {
                    _V2_TITLE, "Build Advisor", "Build Advisor v2",
                }:
                    f.unlink(missing_ok=True)
                    log.info("Removed duplicate: %s", f.name)
            except Exception:
                pass

        item_set = {
            "associatedChampions": [champ_id] if champ_id else [],
            "associatedMaps": [11, 12],
            "blocks": blocks,
            "map": "any",
            "mode": "any",
            "preferredItemSlots": [],
            "sortrank": 0,
            "startedFrom": "blank",
            "title": _V2_TITLE,
            "type": "custom",
            "uid": _V2_UID,
        }

        out_file = rec_dir / _V2_FILE
        out_file.write_text(json.dumps(item_set, indent=2), encoding="utf-8")
        log.info("Wrote recommended item set to %s", out_file)
    except Exception as e:
        log.warning("Failed to write recommended file: %s", e)


async def import_item_set(
    client: LCUClient,
    champion: str,
    starter: list[int],
    core: list[int],
    boots: int,
    situational: list[int],
    title: str = _V2_TITLE,
) -> dict:
    if not client.connected:
        return {"success": False, "error": "Not connected to client"}

    resp = await client.get("/lol-summoner/v1/current-summoner")
    if not resp or resp.status_code != 200:
        return {"success": False, "error": "Failed to get summoner info"}

    summoner = resp.json()
    summoner_id = summoner.get("summonerId", 0)

    # Look up champion ID from ddragon for associatedChampions
    champ_id = await _get_champion_id(client, champion, summoner_id)

    blocks = []
    if starter:
        blocks.append({
            "type": "Starter",
            "items": [{"id": str(item_id), "count": 1} for item_id in starter],
        })
    if boots:
        blocks.append({
            "type": "Boots",
            "items": [{"id": str(boots), "count": 1}],
        })
    if core:
        blocks.append({
            "type": "Core Build",
            "items": [{"id": str(item_id), "count": 1} for item_id in core],
        })
    if situational:
        blocks.append({
            "type": "Situational",
            "items": [{"id": str(item_id), "count": 1} for item_id in situational],
        })

    # Update LCU API — position [0] in the array = first tab in shop
    sets_resp = await client.get(f"/lol-item-sets/v1/item-sets/{summoner_id}/sets")
    existing_sets = []
    if sets_resp and sets_resp.status_code == 200:
        existing_sets = sets_resp.json().get("itemSets", [])

    # Remove old v2 sets
    _v2_titles = {title, "Build Advisor", "Build Advisor v2", "Build Advisor (v2)"}
    existing_sets = [
        s for s in existing_sets
        if s.get("title") not in _v2_titles and s.get("uid") != _V2_UID
    ]

    new_set = {
        "title": title,
        "type": "custom",
        "map": "any",
        "mode": "any",
        "sortrank": 0,               # Lowest value = first tab
        "startedFrom": "blank",
        "blocks": blocks,
        "associatedChampions": [champ_id] if champ_id else [],
        "associatedMaps": [11, 12],
        "preferredItemSlots": [],
        "uid": _V2_UID,
    }

    # Insert at position 0 — first in array = first tab in game
    existing_sets.insert(0, new_set)

    put_resp = await client.put(
        f"/lol-item-sets/v1/item-sets/{summoner_id}/sets",
        json={"itemSets": existing_sets, "timestamp": 0},
    )

    if not put_resp or put_resp.status_code not in (200, 201):
        err = ""
        if put_resp:
            err = put_resp.text[:200]
        return {"success": False, "error": f"Failed to update item sets: {err}"}

    # Also write to Recommended directory as backup
    import asyncio
    await asyncio.sleep(1)  # Let LCU sync to files first
    _write_recommended_file(champion, champ_id, blocks)

    return {"success": True}


async def _get_champion_id(client: LCUClient, champion_name: str, summoner_id: int = 0) -> int:
    """Get champion numeric ID from name via LCU."""
    try:
        sid = summoner_id if summoner_id > 0 else 0
        resp = await client.get(f"/lol-champions/v1/inventories/{sid}/champions-minimal")
        if resp and resp.status_code == 200:
            for champ in resp.json():
                if champ.get("name", "").lower() == champion_name.lower():
                    return champ.get("id", 0)
        # Fallback: try game data endpoint (doesn't need summoner ID)
        resp2 = await client.get("/lol-game-data/assets/v1/champion-summary.json")
        if resp2 and resp2.status_code == 200:
            for champ in resp2.json():
                if champ.get("name", "").lower() == champion_name.lower():
                    return champ.get("id", 0)
    except Exception:
        pass
    return 0
