"""IF-THEN adaptation rules from Kampsycho video + guide.

Each function implements one decision step in the build pipeline:
  1. resolve_adaptation() — A/B/C resolve rune selection
  2. shard_choice() — MS/AF/HP shard selection
  3. summoner_spells() — Ghost+Ignite / Exhaust / etc.
  4. starter_items() — Starting item recommendation
  5. item_path() — Item build path name
"""

from data.rune_pages import (
    SHARD_AS, SHARD_HP, SHARD_MS, SHARD_AF, SHARD_TENACITY, SHARD_ARMOR,
    SECOND_WIND, BONE_PLATING, REVITALIZE, UNFLINCHING, DEMOLISH,
)

# ============================================================================
# Champion category sets (from video notes + guide)
# ============================================================================

RANGED_POKE_CHAMPS = {
    "Teemo", "Quinn", "Vayne", "Kennen", "Kayle", "Smolder", "Gnar",
    "Jayce", "Gangplank", "Heimerdinger", "Rumble",
    "Malphite", "Yone", "Varus", "Akshan", "Aurora",
    "Aurelion Sol", "Cassiopeia", "Ryze", "Swain",
}

BURST_CC_CHAMPS = {
    "Riven", "Renekton", "Jax", "Volibear", "Pantheon", "Sett",
    "Urgot", "Kled", "Nocturne", "Wukong",
}

BURST_CHAMPS = {
    "Riven", "Renekton", "Jax", "Kled", "Nocturne", "Wukong",
    "Ambessa", "Sett",
}

MS_SHARD_CHAMPS = {
    "Jax", "Tryndamere", "Yone", "Yasuo", "Trundle",
    "Zaahen", "Darius",
}

ADAPTIVE_SHARD_CHAMPS = {
    "Vayne", "Gwen", "Kayle", "Nasus",
}

EXHAUST_PRIMARY = {"Tryndamere", "Riven", "Renekton"}
EXHAUST_SECONDARY = {"Yasuo", "Yone", "Jax", "Irelia", "Rengar"}

BAD_AD_MATCHUPS = {
    "Riven", "Jax", "Renekton", "Kled", "Sett", "Tryndamere", "Irelia",
}

AP_MELEE_CHAMPS = {"Gwen", "Mordekaiser", "Sylas"}

AP_POKE_CHAMPS = {"Teemo", "Gragas", "Volibear", "Rumble", "Heimerdinger"}

RANGED_AD_CHAMPS = {"Vayne", "Quinn", "Smolder", "Kennen", "Kayle", "Akshan"}

RANGED_AP_CHAMPS = {"Aurora", "Akali", "Cassiopeia", "Ryze", "Anivia", "Swain"}

AD_TANK_AGGRO = {"Shen", "Sion"}

AP_TANK_CHAMPS = {"Malphite", "Ornn", "Cho'Gath"}

# Item path categories
SHEEN_ICEBORN_CHAMPS = {"Jax", "Fiora", "Renekton", "Kled", "Yasuo", "Riven", "Irelia"}
TIAMAT_TITANIC_CHAMPS = {"Tryndamere", "Trundle", "Sett", "Yone"}
ECLIPSE_POKE_CHAMPS = {"Teemo", "Aurora", "Akali", "Kayle", "Gnar", "Quinn", "Akshan"}
SUNDERED_SKY_CHAMPS = {"Jayce", "Gragas", "Gangplank"}
LIANDRY_SHRED_CHAMPS = {"Cho'Gath", "Dr. Mundo", "Sion", "Tahm Kench", "Ornn", "Maokai"}


# ============================================================================
# Merged bucket access (Python defaults + JSON overrides)
# ============================================================================

def get_buckets() -> dict[str, set]:
    """Return merged bucket sets from user_config overlay."""
    from data.user_config import get_merged_buckets
    return get_merged_buckets()


# ============================================================================
# RULE 1: Resolve Adaptation (A/B/C system)
# ============================================================================

def resolve_adaptation(keystone: str, enemy: str) -> dict:
    """Determine resolve rune slots based on keystone + enemy.

    Returns dict with keys:
      - "row2": rune ID for resolve row 2
      - "row3": rune ID for resolve row 3
      - "code": "A", "B", or "C"

    When resolve is PRIMARY (Grasp pages): 2 adaptable slots after Demolish
    When resolve is SECONDARY (others): 1 adaptable slot after Demolish
    """
    buckets = get_buckets()
    is_primary = keystone.startswith("Grasp")

    if is_primary:
        # Grasp pages: row2 + row3 adapt (Demolish is row1)
        if enemy in buckets["RANGED_POKE_CHAMPS"]:
            return {"row2": SECOND_WIND, "row3": REVITALIZE, "code": "B"}
        elif enemy in buckets["BURST_CC_CHAMPS"]:
            return {"row2": BONE_PLATING, "row3": UNFLINCHING, "code": "C"}
        else:
            return {"row2": BONE_PLATING, "row3": REVITALIZE, "code": "A"}
    else:
        # Non-Grasp: only 1 resolve slot adapts (other is Demolish)
        if enemy in buckets["RANGED_POKE_CHAMPS"]:
            return {"row2": SECOND_WIND, "row3": None, "code": "B"}
        elif enemy in buckets["BURST_CHAMPS"]:
            return {"row2": BONE_PLATING, "row3": None, "code": "C"}
        else:
            return {"row2": REVITALIZE, "row3": None, "code": "A"}


# ============================================================================
# RULE 2: Shard Choice
# ============================================================================

def shard_choice(enemy: str, override: str | None = None) -> tuple[int, int, int]:
    """Return (shard1, shard2, shard3) based on enemy.

    Shard1 = always Attack Speed
    Shard2 = HP (default), MS (vs auto-walk champs), AF (vs easy/% HP)
    Shard3 = Tenacity (default), HP or Armor situational
    """
    buckets = get_buckets()
    if override == "MS" or enemy in buckets["MS_SHARD_CHAMPS"]:
        return (SHARD_AS, SHARD_MS, SHARD_TENACITY)
    elif override == "AF" or enemy in buckets["ADAPTIVE_SHARD_CHAMPS"]:
        return (SHARD_AS, SHARD_AF, SHARD_TENACITY)
    else:
        return (SHARD_AS, SHARD_HP, SHARD_TENACITY)


# ============================================================================
# RULE 3: Summoner Spells
# ============================================================================

def summoner_spells(enemy: str, exhaust_viable: bool = False,
                    matchup_spells: str | None = None) -> str:
    """Return summoner spell recommendation string."""
    buckets = get_buckets()
    if matchup_spells and matchup_spells != "Ghost/Ignite":
        return matchup_spells

    if enemy in buckets["EXHAUST_PRIMARY"]:
        return "Exhaust/TP"
    elif enemy in buckets["EXHAUST_SECONDARY"] or exhaust_viable:
        return "Exhaust viable (Ghost/Ignite default)"
    else:
        return "Ghost/Ignite"


# ============================================================================
# RULE 4: Starter Items
# ============================================================================

def starter_items(enemy: str) -> dict:
    """Return starter item recommendation.

    Returns dict with "name" and "note" keys.
    """
    buckets = get_buckets()
    if enemy in buckets["BAD_AD_MATCHUPS"]:
        return {
            "name": "Cloth Armor + Refillable",
            "note": "D-Blade into Cloth rush also viable",
        }
    elif enemy in buckets["AP_MELEE_CHAMPS"]:
        return {
            "name": "Long Sword + Refillable",
            "note": "D-Blade into Magic Mantle rush also works",
        }
    elif enemy in buckets["AP_POKE_CHAMPS"]:
        return {
            "name": "Doran's Shield",
            "note": "Into Magic Mantle on first recall. Second Wind mandatory.",
        }
    elif enemy in buckets["RANGED_AD_CHAMPS"]:
        return {
            "name": "Doran's Shield",
            "note": "Bramble Vest rush. Aery + Bramble trick for free poke.",
        }
    elif enemy in buckets["RANGED_AP_CHAMPS"]:
        return {
            "name": "Doran's Shield",
            "note": "E max with Eclipse & Shojin + Comet/Aery for poke.",
        }
    elif enemy in buckets["AD_TANK_AGGRO"]:
        return {
            "name": "Cloth Armor + Refillable",
            "note": "Rush Black Cleaver into Liandry.",
        }
    elif enemy in buckets["AP_TANK_CHAMPS"]:
        return {
            "name": "Doran's Shield",
            "note": "Into Cull + Black Cleaver.",
        }
    else:
        return {
            "name": "Doran's Blade + Health Potion",
            "note": "Standard start for most matchups.",
        }


# ============================================================================
# RULE 5: Item Path
# ============================================================================

def item_path(enemy: str, category_override: str | None = None) -> str:
    """Return the recommended item build template name.

    Returns a key that maps to ITEM_BUILDS in item_builds.py.
    """
    cat = category_override or "default"

    # Category overrides from matchup table
    if cat == "iceborn_cleaver":
        return "Iceborn Cleaver"
    elif cat == "titanic_breaker":
        return "Titanic Breaker"
    elif cat == "eclipse_poke":
        return "Eclipse Poke"
    elif cat == "sundered_sky":
        return "Sundered Sky Rush"
    elif cat == "liandry_shred":
        return "Liandry Tank Shred"
    elif cat == "vs_morde":
        return "VS Morde"

    # Champion-specific fallbacks
    buckets = get_buckets()
    if enemy in buckets["SHEEN_ICEBORN_CHAMPS"]:
        return "Iceborn Cleaver"
    elif enemy in buckets["TIAMAT_TITANIC_CHAMPS"]:
        return "Titanic Breaker"
    elif enemy in buckets["ECLIPSE_POKE_CHAMPS"]:
        return "Eclipse Poke"
    elif enemy in buckets["SUNDERED_SKY_CHAMPS"]:
        return "Sundered Sky Rush"
    elif enemy in buckets["LIANDRY_SHRED_CHAMPS"]:
        return "Liandry Tank Shred"

    # Default path
    return "Default BBC"


# ============================================================================
# RULE 6: Rune-to-Build Compatibility
# ============================================================================

RUNE_BUILD_COMPAT: dict[str, list[str]] = {
    "Grasp-1": ["Default BBC", "Iceborn Cleaver", "Titanic Breaker", "Conqueror Bruiser",
                 "Sundered Sky Rush", "Anti-Tank", "Shojin Hull", "VS Jax (Iceborn)", "VS Irelia"],
    "Grasp-2": ["Default BBC", "Iceborn Cleaver", "Titanic Breaker", "Sundered Sky Rush", "Anti-AP"],
    "Grasp-3": ["Default BBC", "Iceborn Cleaver", "Anti-AP", "Sundered Sky Rush", "Anti-Tank"],
    "Grasp-4": ["Default BBC", "Speed Rick", "Shojin Hull", "Anti-AP"],
    "Conqueror": ["Default BBC", "Conqueror Bruiser", "Anti-Tank", "Liandry Tank Shred",
                   "Titanic Breaker", "Anti-AP", "Iceborn Cleaver", "VS Trundle",
                   "VS Trynd (Conqueror)", "VS Morde", "Default Titanic Path"],
    "Comet": ["Default BBC", "Shojin Hull", "Eclipse Poke", "Liandry Tank Shred",
              "Anti-AP", "Anti-Tank", "VS Jax (Shojin)"],
    "Aery": ["Default BBC", "Shojin Hull", "Eclipse Poke", "Anti-AP", "VS Ranged Top"],
    "Phase Rush": ["Speed Rick", "Default BBC", "Iceborn Cleaver", "Anti-AP", "VS Morde"],
    "First Strike": ["Default BBC", "Shojin Hull", "Lethal Splitpush", "Anti-Tank"],
    "Hail of Blades": ["Default BBC", "Lethal Splitpush", "Titanic Breaker", "Iceborn Cleaver"],
}
