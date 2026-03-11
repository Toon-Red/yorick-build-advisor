"""User config override layer — JSON file on top of Python defaults.

Manages data/user_config.json for GUI-driven overrides.
When JSON doesn't exist, all getters return Python defaults unchanged.
"""

import json
import os
from pathlib import Path
from dataclasses import asdict

_CONFIG_PATH = Path(__file__).parent / "user_config.json"
_TMP_PATH = Path(__file__).parent / "user_config.json.tmp"


# ============================================================================
# Core I/O
# ============================================================================

def load_user_config() -> dict:
    """Read JSON file, return empty sections if missing or corrupt."""
    if not _CONFIG_PATH.exists():
        return {
            "buckets": {},
            "matchups": {},
            "rune_pages": {},
            "item_builds": {},
            "rune_build_compat": {},
        }
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure all sections exist
        for key in ("buckets", "matchups", "rune_pages", "item_builds", "rune_build_compat"):
            if key not in data:
                data[key] = {}
        return data
    except (json.JSONDecodeError, OSError):
        return {
            "buckets": {},
            "matchups": {},
            "rune_pages": {},
            "item_builds": {},
            "rune_build_compat": {},
        }


def save_user_config(config: dict) -> None:
    """Write JSON atomically (write to .tmp then rename)."""
    with open(_TMP_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    # os.replace is atomic on the same filesystem
    os.replace(str(_TMP_PATH), str(_CONFIG_PATH))


def delete_user_config() -> bool:
    """Delete user_config.json entirely. Returns True if file existed."""
    if _CONFIG_PATH.exists():
        _CONFIG_PATH.unlink()
        return True
    return False


# ============================================================================
# Merge: Buckets
# ============================================================================

# All bucket set names in data.rules
_BUCKET_NAMES = [
    "RANGED_POKE_CHAMPS", "BURST_CC_CHAMPS", "BURST_CHAMPS",
    "MS_SHARD_CHAMPS", "ADAPTIVE_SHARD_CHAMPS",
    "EXHAUST_PRIMARY", "EXHAUST_WITH_GHOST", "EXHAUST_SECONDARY", "BAD_AD_MATCHUPS",
    "AP_MELEE_CHAMPS", "AP_POKE_CHAMPS", "RANGED_AD_CHAMPS",
    "RANGED_AP_CHAMPS", "AD_TANK_AGGRO", "AP_TANK_CHAMPS",
    "SHEEN_ICEBORN_CHAMPS", "TIAMAT_TITANIC_CHAMPS",
    "ECLIPSE_POKE_CHAMPS", "SUNDERED_SKY_CHAMPS", "LIANDRY_SHRED_CHAMPS",
    "HP_STACK_TANKS",
]


def _get_python_buckets() -> dict[str, set]:
    """Import all bucket sets from data.rules (Python defaults)."""
    from data import rules
    result = {}
    for name in _BUCKET_NAMES:
        result[name] = set(getattr(rules, name))
    return result


def get_merged_buckets() -> dict[str, set]:
    """Merge Python bucket sets with JSON overrides.

    JSON buckets section is a full replacement per bucket name:
      {"RANGED_POKE_CHAMPS": ["Teemo", "Quinn", ...]}
    If a bucket name is present in JSON, it fully replaces the Python set.
    """
    py_buckets = _get_python_buckets()
    cfg = load_user_config()
    json_buckets = cfg.get("buckets", {})

    for name, champ_list in json_buckets.items():
        if name in py_buckets:
            py_buckets[name] = set(champ_list)

    return py_buckets


# ============================================================================
# Merge: Matchups
# ============================================================================

def get_merged_matchups() -> dict:
    """Merge Python MATCHUP_TABLE with JSON overrides.

    JSON matchups are keyed by enemy name. Each value is a dict matching
    MatchupInfo fields. JSON entries override Python entries; new JSON
    entries are added.

    Returns dict[str, MatchupInfo].
    """
    from data.matchup_table import MATCHUP_TABLE, MatchupInfo

    # Start with a copy of Python defaults
    merged = dict(MATCHUP_TABLE)

    cfg = load_user_config()
    json_matchups = cfg.get("matchups", {})

    for enemy, data in json_matchups.items():
        # Convert JSON dict to MatchupInfo
        merged[enemy] = MatchupInfo(
            difficulty=data.get("difficulty", "Medium"),
            keystones=tuple(data.get("keystones", ("Grasp-1",))),
            item_category=data.get("item_category", "default"),
            tags=tuple(data.get("tags", ())),
            shard_override=data.get("shard_override"),
            exhaust_viable=data.get("exhaust_viable", False),
            summoner_spells=data.get("summoner_spells", "Ghost/Ignite"),
            special_note=data.get("special_note", ""),
            advice=data.get("advice", ""),
        )

    return merged


# ============================================================================
# Merge: Rune Pages
# ============================================================================

def get_merged_rune_pages() -> dict:
    """Merge Python RUNE_PAGES with JSON overrides.

    Returns dict[str, RunePageTemplate].
    """
    from data.rune_pages import RUNE_PAGES, RunePageTemplate

    merged = dict(RUNE_PAGES)

    cfg = load_user_config()
    json_pages = cfg.get("rune_pages", {})

    for name, data in json_pages.items():
        merged[name] = RunePageTemplate(
            name=data.get("name", name),
            primary_style_id=data["primary_style_id"],
            sub_style_id=data["sub_style_id"],
            selected_perk_ids=tuple(data["selected_perk_ids"]),
            description=data.get("description", ""),
        )

    return merged


# ============================================================================
# Merge: Item Builds
# ============================================================================

def get_merged_item_builds() -> dict:
    """Merge Python ITEM_BUILDS with JSON overrides.

    Returns dict[str, ItemBuildTemplate].
    """
    from data.item_builds import ITEM_BUILDS, ItemBuildTemplate

    merged = dict(ITEM_BUILDS)

    cfg = load_user_config()
    json_builds = cfg.get("item_builds", {})

    for name, data in json_builds.items():
        merged[name] = ItemBuildTemplate(
            name=data.get("name", name),
            starter=tuple(data["starter"]),
            boots=tuple(data["boots"]),
            core=tuple(data["core"]),
            situational=tuple(data["situational"]),
            description=data.get("description", ""),
        )

    return merged


# ============================================================================
# Merge: Rune-Build Compatibility
# ============================================================================

def get_merged_rune_build_compat() -> dict[str, list[str]]:
    """Merge Python RUNE_BUILD_COMPAT with JSON overrides.

    JSON entries fully replace Python entries per rune page name.
    """
    from data.rules import RUNE_BUILD_COMPAT

    merged = dict(RUNE_BUILD_COMPAT)

    cfg = load_user_config()
    json_compat = cfg.get("rune_build_compat", {})

    for rune_name, build_list in json_compat.items():
        merged[rune_name] = list(build_list)

    return merged


# ============================================================================
# Serialization helpers (for API responses)
# ============================================================================

def matchup_to_dict(matchup) -> dict:
    """Convert MatchupInfo to JSON-serializable dict."""
    return {
        "difficulty": matchup.difficulty,
        "keystones": list(matchup.keystones),
        "item_category": matchup.item_category,
        "tags": list(matchup.tags),
        "shard_override": matchup.shard_override,
        "exhaust_viable": matchup.exhaust_viable,
        "summoner_spells": matchup.summoner_spells,
        "special_note": matchup.special_note,
        "advice": matchup.advice,
    }


def rune_page_to_dict(page) -> dict:
    """Convert RunePageTemplate to JSON-serializable dict."""
    return {
        "name": page.name,
        "primary_style_id": page.primary_style_id,
        "sub_style_id": page.sub_style_id,
        "selected_perk_ids": list(page.selected_perk_ids),
        "description": page.description,
    }


def item_build_to_dict(build) -> dict:
    """Convert ItemBuildTemplate to JSON-serializable dict."""
    return {
        "name": build.name,
        "starter": list(build.starter),
        "boots": list(build.boots),
        "core": list(build.core),
        "situational": list(build.situational),
        "description": build.description,
    }
