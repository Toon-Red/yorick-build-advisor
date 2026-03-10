"""FastAPI server for LoL Build Advisor v2.

Port 5001 — no LLM for build generation, only optional summarize endpoint.
"""

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

from config import API_PORT, API_HOST

# Enable LCU debug logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logging.getLogger("lcu").setLevel(logging.DEBUG)

# Shard icon lookup (Community Dragon assets)
_CDRAGON_SHARDS = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perk-images/statmods"
SHARD_INFO = {
    5008: {"name": "Adaptive Force", "icon": f"{_CDRAGON_SHARDS}/statmodsadaptiveforceicon.png"},
    5005: {"name": "Attack Speed", "icon": f"{_CDRAGON_SHARDS}/statmodsattackspeedicon.png"},
    5007: {"name": "Ability Haste", "icon": f"{_CDRAGON_SHARDS}/statmodscdrscalingicon.png"},
    5010: {"name": "Move Speed", "icon": f"{_CDRAGON_SHARDS}/statmodsmovementspeedicon.png"},
    5002: {"name": "Armor", "icon": f"{_CDRAGON_SHARDS}/statmodsarmoricon.png"},
    5003: {"name": "Magic Resist", "icon": f"{_CDRAGON_SHARDS}/statmodsmagicresicon.png"},
    5001: {"name": "Health (flat)", "icon": f"{_CDRAGON_SHARDS}/statmodshealthplusicon.png"},
    5011: {"name": "Health (scaling)", "icon": f"{_CDRAGON_SHARDS}/statmodshealthscalingicon.png"},
    5013: {"name": "Tenacity/Slow Resist", "icon": f"{_CDRAGON_SHARDS}/statmodstenacityicon.png"},
}
from engine import recommend_builds, recommend_builds_multi, build_option_to_dict
from scrapers.ddragon import DataDragon
from data.matchup_table import get_all_matchup_enemies, get_matchup, MATCHUP_TABLE
from data.user_config import (
    load_user_config, save_user_config, delete_user_config,
    get_merged_buckets, get_merged_matchups, get_merged_rune_pages,
    get_merged_item_builds, get_merged_rune_build_compat,
    matchup_to_dict, rune_page_to_dict, item_build_to_dict,
)
from data.matchup_table import MatchupInfo
from data.rune_pages import RunePageTemplate
from data.item_builds import ItemBuildTemplate
from lcu.client import LCUClient
from lcu.auto_detect import poll_champ_select, has_state_changed, ChampSelectSnapshot
from lcu.rune_import import import_rune_page
from lcu.item_import import import_item_set
from lcu.spell_import import import_summoner_spells, parse_spell_pair

# Global state
ddragon = DataDragon()
lcu_client = LCUClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Loading Data Dragon...")
    ddragon.load()
    print(f"Data Dragon loaded: {ddragon.summary()}")
    yield
    # Shutdown
    await lcu_client.disconnect()


app = FastAPI(title="LoL Build Advisor v2", lifespan=lifespan)


# --- Request/Response Models ---

class BuildQueryRequest(BaseModel):
    champion: str = "Yorick"
    enemy: str
    team: list[str] | None = None


class RuneImportRequest(BaseModel):
    name: str
    primary_style_id: int
    sub_style_id: int
    selected_perk_ids: list[int]


class ItemImportRequest(BaseModel):
    champion: str
    starter: list[int]
    core: list[int]
    boots: int
    situational: list[int]


class SpellImportRequest(BaseModel):
    spells: str  # "Ghost/Ignite", "Exhaust/TP", etc.


class MultiBuildRequest(BaseModel):
    champion: str = "Yorick"
    enemies: list[dict]  # [{"name": str, "weight": float}, ...]


# --- API Endpoints ---

@app.get("/api/health")
async def health():
    from version import __version__, DEV_MODE
    return {"status": "ok", "ddragon_version": ddragon.version,
            "version": __version__, "dev_mode": DEV_MODE}


@app.get("/api/update/check")
async def check_update():
    """Check GitHub for a newer release and staged update status."""
    from updater import (get_latest_release, is_newer, get_current_version,
                         is_update_staged, get_staged_version)
    current = get_current_version()
    result = get_latest_release()
    staged = is_update_staged()
    staged_ver = get_staged_version() if staged else None
    resp = {
        "current_version": current,
        "update_available": False,
        "staged": staged,
        "staged_version": staged_ver,
    }
    if result and is_newer(result["version"], current):
        resp["update_available"] = True
        resp["latest_version"] = result["version"]
        resp["release_name"] = result["name"]
        resp["release_notes"] = result["notes"]
        resp["exe_url"] = result["exe_url"]
    return resp


@app.get("/api/releases")
async def list_releases():
    """Get recent releases with notes for the changelog."""
    from updater import get_all_releases
    return {"releases": get_all_releases(limit=10)}


@app.post("/api/update/download")
async def download_update_endpoint():
    """Start downloading the update exe in the background."""
    from updater import get_latest_release, is_newer, get_current_version, update_manager
    release = get_latest_release()
    if not release or not is_newer(release["version"], get_current_version()):
        return {"ok": False, "error": "No update available"}
    if not release.get("exe_url"):
        return {"ok": False, "error": "No exe asset in release"}
    started = update_manager.start_download(release["exe_url"], release["version"])
    return {"ok": started, "error": "Download already in progress" if not started else None}


@app.get("/api/update/status")
async def update_status():
    """Poll download progress."""
    from updater import update_manager
    return update_manager.get_status()


@app.post("/api/update/apply")
async def apply_update():
    """Apply staged update — spawns batch script and exits."""
    from updater import apply_update_and_restart, is_update_staged
    if not is_update_staged():
        return {"ok": False, "error": "No staged update"}
    apply_update_and_restart()
    return {"ok": True}


@app.get("/api/ddragon/champions")
async def get_champions():
    """Return sorted champion list for dropdown."""
    champs = sorted(ddragon.champions.keys())
    return {"champions": champs, "count": len(champs)}


@app.get("/api/ddragon/version")
async def get_version():
    return {"version": ddragon.version}


@app.get("/api/ddragon/champion-icon/{name}")
async def champion_icon(name: str):
    url = ddragon.champion_portrait_url(name)
    return {"url": url}


@app.get("/api/ddragon/item-icon/{item_id}")
async def item_icon(item_id: int):
    url = ddragon.item_icon_url(item_id)
    name = ddragon.item_name(item_id)
    return {"url": url, "name": name}


@app.get("/api/ddragon/rune-icon/{rune_id}")
async def rune_icon(rune_id: int):
    url = ddragon.rune_icon_url(rune_id)
    name = ddragon.rune_name(rune_id)
    return {"url": url, "name": name}


@app.get("/api/matchups")
async def get_matchups():
    """Return all matchup enemies with difficulties."""
    enemies = get_all_matchup_enemies()
    result = []
    for e in enemies:
        m = get_matchup(e)
        result.append({"enemy": e, "difficulty": m.difficulty})
    return {"matchups": result, "count": len(result)}


def _enrich_options(options):
    """Add Data Dragon names/icons to a list of BuildOption objects."""
    enriched = []
    for opt in options:
        d = build_option_to_dict(opt)
        d["rune_details"] = []
        for perk_id in opt.selected_perk_ids[:6]:
            d["rune_details"].append({
                "id": perk_id,
                "name": ddragon.rune_name(perk_id),
                "icon": ddragon.rune_icon_url(perk_id),
            })
        d["shard_details"] = []
        for perk_id in opt.selected_perk_ids[6:9]:
            d["shard_details"].append({
                "id": perk_id,
                "name": SHARD_INFO.get(perk_id, {}).get("name", str(perk_id)),
                "icon": SHARD_INFO.get(perk_id, {}).get("icon", ""),
            })
        d["item_details"] = {}
        all_item_ids = set(opt.starter + opt.boots + opt.core + opt.situational)
        for iid in all_item_ids:
            d["item_details"][str(iid)] = {
                "id": iid,
                "name": ddragon.item_name(iid),
                "icon": ddragon.item_icon_url(iid),
            }
        d["primary_style_icon"] = ddragon.style_icon_url(opt.primary_style_id)
        d["sub_style_icon"] = ddragon.style_icon_url(opt.sub_style_id)
        enriched.append(d)
    return enriched


@app.post("/api/build/query")
async def build_query(req: BuildQueryRequest):
    """Run ALL profiles for this champion and return grouped results."""
    matchup = get_matchup(req.enemy)

    # Find all guides for this champion
    guides = guide_manager.list_guides_for_champion(req.champion)

    profiles = []
    for guide_meta in guides:
        guide = guide_manager.load_guide(guide_meta["guide_id"])
        if not guide:
            continue
        options = recommend_from_guide(guide, req.champion, req.enemy)
        profiles.append({
            "guide_id": guide_meta["guide_id"],
            "guide_name": guide_meta["guide_name"],
            "author": guide_meta["author"],
            "options": _enrich_options(options),
            "count": len(options),
        })

    # Fallback: if no guides exist, use the legacy Python engine
    if not profiles:
        options = recommend_builds(req.champion, req.enemy)
        profiles.append({
            "guide_id": "_legacy",
            "guide_name": "Built-in Engine",
            "author": "System",
            "options": _enrich_options(options),
            "count": len(options),
        })

    return {
        "champion": req.champion,
        "enemy": req.enemy,
        "difficulty": matchup.difficulty,
        "special_note": matchup.special_note,
        "profiles": profiles,
        "profile_count": len(profiles),
    }


# --- Multi-Build Endpoint ---

@app.post("/api/build/query-multi")
async def build_query_multi(req: MultiBuildRequest):
    """Run weighted multi-enemy build and return options."""
    options = recommend_builds_multi(req.champion, req.enemies)
    enriched = _enrich_options(options)

    # Use the highest-weight enemy for difficulty/special_note
    top_enemy = max(req.enemies, key=lambda e: e.get("weight", 0)) if req.enemies else {"name": "Unknown"}
    matchup = get_matchup(top_enemy["name"])

    return {
        "champion": req.champion,
        "enemy": "Multi (" + ", ".join(f"{e['name']} {e['weight']:.0%}" for e in sorted(req.enemies, key=lambda x: -x["weight"])) + ")",
        "difficulty": matchup.difficulty,
        "special_note": matchup.special_note,
        "options": enriched,
        "count": len(enriched),
    }


# --- LCU Endpoints ---

@app.get("/api/lcu/status")
async def lcu_status():
    connected = await lcu_client.connect()
    result = {"connected": connected}
    # Include diagnostic info for debugging
    creds = lcu_client.read_lockfile()
    if creds:
        result["port"] = creds.port
        result["pid"] = creds.pid
    else:
        result["lockfile_exists"] = lcu_client.lockfile_path.exists()
        result["lockfile_path"] = str(lcu_client.lockfile_path)
    return result


@app.get("/api/lcu/champ-select-stream")
async def champ_select_stream(request: Request):
    """SSE endpoint for live champ select detection."""
    async def event_generator():
        prev_snapshot = ChampSelectSnapshot()
        idle_count = 0

        while True:
            if await request.is_disconnected():
                break

            connected = await lcu_client.connect()
            if not connected:
                yield f"data: {json.dumps({'type': 'disconnected'})}\n\n"
                await asyncio.sleep(5)
                idle_count += 1
                if idle_count > 60:  # 5 minutes of no LCU
                    break
                continue

            snapshot = await poll_champ_select(lcu_client, ddragon.champion_by_key)

            if snapshot.active:
                idle_count = 0
                if has_state_changed(prev_snapshot, snapshot):
                    yield f"data: {json.dumps({'type': 'update', **snapshot.to_dict()})}\n\n"
                    prev_snapshot = snapshot
            else:
                if prev_snapshot.active:
                    yield f"data: {json.dumps({'type': 'end'})}\n\n"
                    prev_snapshot = ChampSelectSnapshot()
                idle_count += 1

            await asyncio.sleep(1.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/lcu/import-runes")
async def lcu_import_runes(req: RuneImportRequest):
    connected = await lcu_client.connect()
    if not connected:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "LoL client not running"},
        )
    result = await import_rune_page(
        lcu_client, req.name, req.primary_style_id,
        req.sub_style_id, req.selected_perk_ids,
    )
    return result


@app.post("/api/lcu/import-items")
async def lcu_import_items(req: ItemImportRequest):
    connected = await lcu_client.connect()
    if not connected:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "LoL client not running"},
        )
    boots_id = req.boots if req.boots else 0
    result = await import_item_set(
        lcu_client, req.champion, req.starter,
        req.core, boots_id, req.situational,
    )
    return result


@app.post("/api/lcu/import-spells")
async def lcu_import_spells(req: SpellImportRequest):
    connected = await lcu_client.connect()
    if not connected:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "LoL client not running"},
        )
    spell1, spell2 = parse_spell_pair(req.spells)
    result = await import_summoner_spells(lcu_client, spell1, spell2)
    return result


# --- Config CRUD Endpoints ---

@app.get("/api/config")
async def get_full_config():
    """Full merged config (all sections)."""
    buckets = get_merged_buckets()
    matchups = get_merged_matchups()
    rune_pages = get_merged_rune_pages()
    item_builds = get_merged_item_builds()
    rune_build_compat = get_merged_rune_build_compat()

    return {
        "buckets": {name: sorted(champs) for name, champs in buckets.items()},
        "matchups": {enemy: matchup_to_dict(m) for enemy, m in matchups.items()},
        "rune_pages": {name: rune_page_to_dict(p) for name, p in rune_pages.items()},
        "item_builds": {name: item_build_to_dict(b) for name, b in item_builds.items()},
        "rune_build_compat": rune_build_compat,
    }


@app.get("/api/config/buckets")
async def get_config_buckets():
    """All bucket sets as {name: [champions]}."""
    buckets = get_merged_buckets()
    return {name: sorted(champs) for name, champs in buckets.items()}


@app.get("/api/config/matchups")
async def get_config_matchups():
    """All merged matchups as {enemy: {...}}."""
    matchups = get_merged_matchups()
    return {enemy: matchup_to_dict(m) for enemy, m in matchups.items()}


@app.get("/api/config/rune-pages")
async def get_config_rune_pages():
    """All merged rune pages."""
    rune_pages = get_merged_rune_pages()
    return {name: rune_page_to_dict(p) for name, p in rune_pages.items()}


@app.get("/api/config/item-builds")
async def get_config_item_builds():
    """All merged item builds."""
    item_builds = get_merged_item_builds()
    return {name: item_build_to_dict(b) for name, b in item_builds.items()}


@app.put("/api/config/buckets")
async def put_config_buckets(request: Request):
    """Save all bucket assignments (full replace)."""
    body = await request.json()
    cfg = load_user_config()
    cfg["buckets"] = body
    save_user_config(cfg)
    return {"success": True}


@app.put("/api/config/matchups/{enemy}")
async def put_config_matchup(enemy: str, request: Request):
    """Create/update single matchup override."""
    body = await request.json()
    cfg = load_user_config()
    cfg["matchups"][enemy] = body
    save_user_config(cfg)
    return {"success": True, "enemy": enemy}


@app.delete("/api/config/matchups/{enemy}")
async def delete_config_matchup(enemy: str):
    """Remove JSON override for matchup (falls back to Python default)."""
    cfg = load_user_config()
    removed = cfg["matchups"].pop(enemy, None)
    save_user_config(cfg)
    return {"success": True, "removed": removed is not None, "enemy": enemy}


@app.put("/api/config/rune-pages/{name}")
async def put_config_rune_page(name: str, request: Request):
    """Create/update rune page override."""
    body = await request.json()
    cfg = load_user_config()
    cfg["rune_pages"][name] = body
    save_user_config(cfg)
    return {"success": True, "name": name}


@app.delete("/api/config/rune-pages/{name}")
async def delete_config_rune_page(name: str):
    """Remove JSON override for rune page."""
    cfg = load_user_config()
    removed = cfg["rune_pages"].pop(name, None)
    save_user_config(cfg)
    return {"success": True, "removed": removed is not None, "name": name}


@app.put("/api/config/item-builds/{name}")
async def put_config_item_build(name: str, request: Request):
    """Create/update item build override."""
    body = await request.json()
    cfg = load_user_config()
    cfg["item_builds"][name] = body
    save_user_config(cfg)
    return {"success": True, "name": name}


@app.delete("/api/config/item-builds/{name}")
async def delete_config_item_build(name: str):
    """Remove JSON override for item build."""
    cfg = load_user_config()
    removed = cfg["item_builds"].pop(name, None)
    save_user_config(cfg)
    return {"success": True, "removed": removed is not None, "name": name}


@app.get("/api/config/decision-tree/{champion}")
async def get_decision_tree(champion: str):
    """Get decision tree for a champion."""
    cfg = load_user_config()
    trees = cfg.get("decision_trees", {})
    tree = trees.get(champion)
    if tree:
        return tree
    return JSONResponse({"root": None}, status_code=200)


@app.put("/api/config/decision-tree/{champion}")
async def put_decision_tree(champion: str, request: Request):
    """Save decision tree for a champion."""
    body = await request.json()
    cfg = load_user_config()
    if "decision_trees" not in cfg:
        cfg["decision_trees"] = {}
    cfg["decision_trees"][champion] = body
    save_user_config(cfg)
    return {"success": True, "champion": champion}


@app.post("/api/config/reset")
async def reset_config():
    """Delete user_config.json entirely."""
    existed = delete_user_config()
    return {"success": True, "had_config": existed}


# --- DDragon Data for Editors ---

@app.get("/api/ddragon/all-runes")
async def get_all_runes():
    """Full rune tree structure for picker UI."""
    # Build structured rune tree from runesReforged data
    # ddragon.rune_styles has {id, name, icon} but not full slots
    # We need to re-read the cached runesReforged.json for full structure
    from config import DDRAGON_DIR
    version_dir = DDRAGON_DIR / ddragon.version
    runes_file = version_dir / "runesReforged.json"

    if runes_file.exists():
        with open(runes_file, "r", encoding="utf-8") as f:
            rune_trees = json.load(f)
    else:
        rune_trees = []

    # Hardcoded shards (not in runesReforged) — icons from Community Dragon
    shards = [
        {"id": 5008, "name": "Adaptive Force", "short": "AF", "icon": SHARD_INFO[5008]["icon"]},
        {"id": 5005, "name": "Attack Speed", "short": "AS", "icon": SHARD_INFO[5005]["icon"]},
        {"id": 5007, "name": "Ability Haste", "short": "AH", "icon": SHARD_INFO[5007]["icon"]},
        {"id": 5010, "name": "Move Speed", "short": "MS", "icon": SHARD_INFO[5010]["icon"]},
        {"id": 5002, "name": "Armor", "short": "Armor", "icon": SHARD_INFO[5002]["icon"]},
        {"id": 5003, "name": "Magic Resist", "short": "MR", "icon": SHARD_INFO[5003]["icon"]},
        {"id": 5001, "name": "Health (flat)", "short": "HP", "icon": SHARD_INFO[5001]["icon"]},
        {"id": 5011, "name": "Health (scaling)", "short": "HP%", "icon": SHARD_INFO[5011]["icon"]},
        {"id": 5013, "name": "Tenacity/Slow Resist", "short": "Tenacity", "icon": SHARD_INFO[5013]["icon"]},
    ]

    return {"rune_trees": rune_trees, "shards": shards}


@app.get("/api/ddragon/all-items")
async def get_all_items():
    """All items with id/name/icon/gold for picker UI."""
    items = []
    for item_id_str, info in ddragon.items.items():
        items.append({
            "id": int(item_id_str),
            "name": info["name"],
            "icon": ddragon.item_icon_url(int(item_id_str)),
            "gold": info.get("gold", 0),
            "tags": info.get("tags", []),
        })
    # Sort by name for UI convenience
    items.sort(key=lambda x: x["name"])
    return {"items": items, "count": len(items)}


# --- Guide Endpoints ---

import guide_manager
from tree_executor import recommend_from_guide


@app.get("/api/guides")
async def get_guides(champion: str = None):
    """List all guides, optionally filtered by champion."""
    if champion:
        return {"guides": guide_manager.list_guides_for_champion(champion)}
    return {"guides": guide_manager.list_guides()}


@app.get("/api/guides/{guide_id}")
async def get_guide(guide_id: str):
    """Get full guide JSON (tree + data)."""
    guide = guide_manager.load_guide(guide_id)
    if not guide:
        return JSONResponse({"error": "Guide not found"}, status_code=404)
    return guide


@app.put("/api/guides/{guide_id}")
async def save_guide(guide_id: str, request: Request):
    """Save/update a guide."""
    body = await request.json()
    body["guide_id"] = guide_id
    saved_id = guide_manager.save_guide(body)
    return {"guide_id": saved_id, "ok": True}


@app.delete("/api/guides/{guide_id}")
async def delete_guide(guide_id: str):
    """Delete a guide."""
    if guide_manager.delete_guide(guide_id):
        return {"ok": True}
    return JSONResponse({"error": "Guide not found"}, status_code=404)


@app.post("/api/guides/import")
async def import_guide(request: Request):
    """Import a guide from JSON."""
    body = await request.json()
    try:
        guide_id = guide_manager.import_guide(body)
        return {"guide_id": guide_id, "ok": True}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/api/guides/{guide_id}/export")
async def export_guide(guide_id: str):
    """Export a guide as downloadable JSON."""
    guide = guide_manager.export_guide(guide_id)
    if not guide:
        return JSONResponse({"error": "Guide not found"}, status_code=404)
    return guide


@app.put("/api/guides/{guide_id}/active")
async def set_active_guide(guide_id: str):
    """Set a guide as the active one for its champion."""
    guide = guide_manager.load_guide(guide_id)
    if not guide:
        return JSONResponse({"error": "Guide not found"}, status_code=404)
    guide_manager.set_active_guide(guide["champion"], guide_id)
    return {"ok": True, "champion": guide["champion"], "guide_id": guide_id}


@app.post("/api/guides/{guide_id}/execute")
async def execute_guide(guide_id: str, request: Request):
    """Execute a guide tree for a matchup. Body: {"enemy": "Jax"}"""
    guide = guide_manager.load_guide(guide_id)
    if not guide:
        return JSONResponse({"error": "Guide not found"}, status_code=404)
    body = await request.json()
    enemy = body.get("enemy", "")
    if not enemy:
        return JSONResponse({"error": "Missing 'enemy' field"}, status_code=400)
    from engine import build_option_to_dict
    results = recommend_from_guide(guide, guide["champion"], enemy)
    return {"builds": [build_option_to_dict(r) for r in results]}


# --- Static Files ---

static_dir = Path(__file__).parent / "static"

@app.get("/")
async def index():
    return FileResponse(static_dir / "index.html")


@app.get("/flow")
async def flow():
    return FileResponse(static_dir / "flow.html")


@app.get("/editor")
async def editor():
    return FileResponse(static_dir / "editor.html")


# Mount static files AFTER explicit routes
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


if __name__ == "__main__":
    uvicorn.run("app:app", host=API_HOST, port=API_PORT, reload=True)
