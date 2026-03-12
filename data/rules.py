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
    LEGEND_ALACRITY, CUT_DOWN,
)

# ============================================================================
# Champion category sets (from video notes + guide)
# ============================================================================

RANGED_POKE_CHAMPS = {
    "Teemo", "Quinn", "Vayne", "Kennen", "Kayle", "Smolder", "Gnar",
    "Jayce", "Gangplank", "Heimerdinger", "Rumble",
    "Malphite", "Yone", "Yasuo", "Fiora", "Varus", "Akshan", "Aurora",
    "Aurelion Sol", "Cassiopeia", "Ryze", "Swain",
    "Volibear",  # Lightning passive = poke, needs SecondWind for non-Grasp too (PDF p66)
}

BURST_CC_CHAMPS = {
    "Riven", "Renekton", "Jax", "Volibear", "Pantheon", "Sett",
    "Urgot", "Kled", "Nocturne", "Wukong", "Akali",
}

BURST_CHAMPS = {
    "Riven", "Renekton", "Jax", "Kled", "Nocturne", "Wukong",
    "Ambessa", "Sett", "Akali",
}

MS_SHARD_CHAMPS = {
    "Jax", "Tryndamere", "Yone", "Yasuo", "Trundle",
    "Zaahen", "Darius",
}

ADAPTIVE_SHARD_CHAMPS = {
    "Vayne", "Gwen", "Kayle", "Nasus",
}

EXHAUST_PRIMARY = {"Tryndamere"}
EXHAUST_WITH_GHOST = {"Riven", "Renekton"}
EXHAUST_SECONDARY = {"Yasuo", "Yone", "Jax", "Irelia", "Rengar", "Akali"}

BAD_AD_MATCHUPS = {
    "Riven", "Jax", "Renekton", "Kled", "Sett", "Tryndamere", "Irelia",
}

AP_MELEE_CHAMPS = {"Gwen", "Mordekaiser", "Sylas", "Akali", "Kayle"}

AP_POKE_CHAMPS = {"Teemo", "Gragas", "Volibear", "Rumble", "Heimerdinger"}

RANGED_AD_CHAMPS = {"Vayne", "Quinn", "Smolder", "Kennen", "Kayle", "Akshan"}

RANGED_AP_CHAMPS = {"Aurora", "Akali", "Cassiopeia", "Ryze", "Anivia", "Swain"}

AD_TANK_AGGRO = {"Shen", "Sion"}

AP_TANK_CHAMPS = {"Malphite", "Ornn", "Cho'Gath"}

# Item path categories
SHEEN_ICEBORN_CHAMPS = {"Jax", "Fiora", "Renekton", "Kled", "Yasuo", "Riven", "Irelia"}
TIAMAT_TITANIC_CHAMPS = {"Tryndamere", "Trundle", "Sett", "Yone"}
ECLIPSE_POKE_CHAMPS = {"Teemo", "Aurora", "Quinn", "Akshan"}
SUNDERED_SKY_CHAMPS = {"Jayce", "Gragas", "Gangplank"}
LIANDRY_SHRED_CHAMPS = {"Cho'Gath", "Dr. Mundo", "Sion", "Tahm Kench", "Ornn", "Maokai"}
HP_STACK_TANKS = {"Sion", "Cho'Gath"}


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

RESOLVE_OVERRIDE_CHAMPS = {
    "Volibear": {"row2": SECOND_WIND, "row3": UNFLINCHING, "code": "B+C"},
}


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
        # Matchup-specific overrides (e.g. Volibear = Second Wind + Unflinching)
        if enemy in RESOLVE_OVERRIDE_CHAMPS:
            return dict(RESOLVE_OVERRIDE_CHAMPS[enemy])

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
    elif enemy in buckets["EXHAUST_WITH_GHOST"]:
        return "Exhaust/Ghost"
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

def item_path(enemy: str, category_override: str | None = None, keystone: str = "") -> str:
    """Return the recommended item build template name.

    Returns a key that maps to ITEM_BUILDS in item_builds.py.
    Keystone-dependent routing: certain matchups have different item paths
    depending on whether the keystone is Grasp (tank/sustain) vs non-Grasp (poke/DPS).

    Sources:
      - Jax: Grasp → Iceborn [mobafire L537-538], non-Grasp → Shojin [mobafire L540-541]
      - Tryndamere: Grasp → Iceborn Old [mobafire L555-556], non-Grasp → Conqueror [mobafire L549-550]
      - Ranged AD + Aery → VS Ranged Top (Bramble trick) [mobafire L534-535]
    """
    cat = category_override or "default"
    is_grasp = keystone.startswith("Grasp")

    # --- Keystone-dependent matchup-specific routes ---
    # Jax: Grasp → Iceborn (slow field + armor), non-Grasp → Shojin (poke + pet DMG amp)
    if cat in ("vs_jax_iceborn", "vs_jax_shojin"):
        return "VS Jax (Iceborn)" if is_grasp else "VS Jax (Shojin)"

    # Tryndamere: Grasp → Iceborn Old (tank kite), non-Grasp → Conqueror (sustained DPS)
    if cat in ("vs_trynd_conq", "vs_trynd_iceborn"):
        return "VS Trynd (Iceborn Old)" if is_grasp else "VS Trynd (Conqueror)"

    # Ranged AD + Aery → VS Ranged Top (Bramble trick) instead of Eclipse Poke
    # Their autos trigger Bramble which triggers Aery for free poke [mobafire L534-535]
    if cat == "eclipse_poke" and keystone == "Aery":
        buckets = get_buckets()
        if enemy in buckets.get("RANGED_AD_CHAMPS", RANGED_AD_CHAMPS):
            return "VS Ranged Top"

    # Category overrides from matchup table (non-keystone-dependent)
    CATEGORY_MAP = {
        "iceborn_cleaver": "Iceborn Cleaver",
        "titanic_breaker": "Titanic Breaker",
        "eclipse_poke": "Eclipse Poke",
        "sundered_sky": "Sundered Sky Rush",
        "liandry_shred": "Liandry Tank Shred",
        "vs_morde": "VS Morde",
        "vs_trundle": "VS Trundle",
        "vs_irelia": "VS Irelia",
        "vs_ranged": "VS Ranged Top",
        "default_titanic": "Default Titanic Path",
        "anti_ap": "Anti-AP",
    }
    if cat in CATEGORY_MAP:
        return CATEGORY_MAP[cat]

    # Champion-specific fallbacks (bucket-based)
    buckets = get_buckets()

    # Ranged AD: Aery → VS Ranged Top (Bramble trick), else → Eclipse Poke
    if enemy in buckets["ECLIPSE_POKE_CHAMPS"]:
        if keystone == "Aery" and enemy in buckets.get("RANGED_AD_CHAMPS", RANGED_AD_CHAMPS):
            return "VS Ranged Top"
        return "Eclipse Poke"

    if enemy in buckets["SHEEN_ICEBORN_CHAMPS"]:
        return "Iceborn Cleaver"
    elif enemy in buckets["TIAMAT_TITANIC_CHAMPS"]:
        return "Titanic Breaker"
    elif enemy in buckets["SUNDERED_SKY_CHAMPS"]:
        return "Sundered Sky Rush"
    elif enemy in buckets["LIANDRY_SHRED_CHAMPS"]:
        return "Liandry Tank Shred"

    # Default path
    return "Default BBC"


# ============================================================================
# RULE 6: Rune-to-Build Compatibility
# ============================================================================

# ============================================================================
# RULE 6.5: Precision Secondary Adaptation (Cut Down swap)
# ============================================================================

def precision_secondary_adaptation(perks: list[int], sub_style_id: int, enemy: str) -> list[int]:
    """Swap Legend: Alacrity for Cut Down vs high HP tanks when secondary is Precision.

    Per Kampsycho: "Cutdown swaps out Alacrity vs High HP Tanks like Sion & Cho'Gath"
    Only applies to Grasp pages with Precision secondary (Grasp-1).
    """
    buckets = get_buckets()
    hp_tanks = buckets.get("HP_STACK_TANKS", HP_STACK_TANKS)
    if sub_style_id == 8000 and enemy in hp_tanks:  # Precision secondary
        for i in range(4, 6):  # Secondary rune slots
            if perks[i] == LEGEND_ALACRITY:
                perks[i] = CUT_DOWN
                break
    return perks


# ============================================================================
# RULE 7: Boot Recommendation
# ============================================================================

BOOT_RUSH_CHAMPS = {
    "Darius", "Nasus", "Garen", "Singed", "Udyr",
}

STEELCAPS_CHAMPS = {
    "Jax", "Tryndamere", "Irelia", "Yone", "Yasuo", "Trundle",
    "Riven", "Renekton", "Kled", "Sett", "Nocturne", "Wukong",
    "Fiora", "Warwick",
}

MERCS_CHAMPS = {
    "Mordekaiser", "Teemo", "Rumble", "Heimerdinger", "Volibear",
    "Malphite", "Sylas", "Gwen", "Cho'Gath", "Ornn",
    "Singed", "Cassiopeia", "Akali", "Kayle", "Aurora",
    "Anivia", "Aurelion Sol", "Diana", "Gragas", "Kennen",
    "Swain", "Vladimir",
}

SWIFTNESS_CHAMPS = {
    "Quinn", "Gnar", "Ryze", "Cassiopeia", "Singed",
}


def boot_recommendation(enemy: str, keystone: str = "", item_build: str = "") -> dict:
    """Return boot choice, whether to rush, and reasoning.

    Returns dict with:
      - "boot": primary boot name
      - "boot_id": primary boot item ID
      - "rush": bool (buy before first core item)
      - "note": explanation string
    """
    from data.item_builds import (
        PLATED_STEELCAPS, MERCURY_TREADS, BOOTS_OF_SWIFTNESS, IONIAN_BOOTS,
    )
    buckets = get_buckets()

    # Eclipse/Comet poke builds → Ionian for ability haste (but not vs AP threats needing MR)
    if item_build in ("Eclipse Poke",) or keystone in ("Comet", "Aery"):
        if enemy in buckets.get("ECLIPSE_POKE_CHAMPS", ECLIPSE_POKE_CHAMPS) and enemy not in MERCS_CHAMPS:
            return {
                "boot": "Ionian Boots",
                "boot_id": IONIAN_BOOTS,
                "rush": False,
                "note": "Ability haste for poke build (E max + Eclipse)",
            }

    # Swiftness vs ranged kiters
    if enemy in SWIFTNESS_CHAMPS:
        return {
            "boot": "Boots of Swiftness",
            "boot_id": BOOTS_OF_SWIFTNESS,
            "rush": True,
            "note": f"Swiftness to close gap vs {enemy}. Rush boots to avoid being kited.",
        }

    # Mercury's vs AP/CC heavy
    if enemy in MERCS_CHAMPS:
        rush = enemy in BOOT_RUSH_CHAMPS or enemy in buckets.get("AP_POKE_CHAMPS", AP_POKE_CHAMPS)
        return {
            "boot": "Mercury's Treads",
            "boot_id": MERCURY_TREADS,
            "rush": rush,
            "note": f"Merc's for MR + tenacity vs {enemy}." + (" Rush boots." if rush else ""),
        }

    # Steelcaps vs auto-attackers
    if enemy in STEELCAPS_CHAMPS or enemy in buckets.get("BAD_AD_MATCHUPS", BAD_AD_MATCHUPS):
        rush = enemy in BOOT_RUSH_CHAMPS
        return {
            "boot": "Plated Steelcaps",
            "boot_id": PLATED_STEELCAPS,
            "rush": rush,
            "note": f"Steelcaps for auto-attack reduction vs {enemy}." + (" Rush boots." if rush else ""),
        }

    # Default: Steelcaps (most top laners are AD)
    return {
        "boot": "Plated Steelcaps",
        "boot_id": PLATED_STEELCAPS,
        "rush": False,
        "note": "Steelcaps default for most AD top laners.",
    }


# ============================================================================
# RULE 8: First Back Recommendation
# ============================================================================

def first_back_recommendation(enemy: str, item_build: str = "") -> str:
    """Return the first back category key for FIRST_BACK_ITEMS lookup.

    Returns a string key that maps to FIRST_BACK_ITEMS in item_builds.py.
    """
    buckets = get_buckets()

    # Tiamat rush for Titanic paths
    if item_build in ("Titanic Breaker", "VS Trundle", "VS Trynd (Conqueror)",
                       "Default Titanic Path", "Lethal Splitpush"):
        return "tiamat_rush"

    # Sheen rush for Iceborn/Trinity paths
    if item_build in ("Iceborn Cleaver", "VS Jax (Iceborn)", "VS Trynd (Iceborn Old)",
                       "VS Irelia", "Speed Rick", "Bonk Shovel",
                       "Hullbreakin Dat Ashe", "Iceborn Dragon"):
        return "sheen_rush"

    # Hard AD matchups → armor rush
    if enemy in buckets.get("BAD_AD_MATCHUPS", BAD_AD_MATCHUPS):
        return "vs_ad_hard"

    # AP melee → MR components
    if enemy in buckets.get("AP_MELEE_CHAMPS", AP_MELEE_CHAMPS):
        return "vs_ap_melee"

    # AP poke → MR rush
    if enemy in buckets.get("AP_POKE_CHAMPS", AP_POKE_CHAMPS):
        return "vs_ap_poke"

    # Ranged AD → Bramble rush (Aery trick)
    if enemy in buckets.get("RANGED_AD_CHAMPS", RANGED_AD_CHAMPS):
        return "vs_ranged_ad"

    # Safe farm lanes (tanks you outscale)
    if enemy in buckets.get("AP_TANK_CHAMPS", AP_TANK_CHAMPS):
        return "safe_lane"

    return "default"


# ============================================================================
# RULE 9: Relevant Item Combos (mix-and-match for slots 4-6)
# ============================================================================

ANTI_HEAL_CHAMPS = {
    "Dr. Mundo", "Aatrox", "Warwick", "Trundle", "Fiora",
    "Sylas", "Irelia", "Swain", "Illaoi", "Volibear",
}

ANTI_SHIELD_CHAMPS = {
    "Riven", "Sett", "Ambessa", "Mordekaiser",
}


def relevant_combos(enemy: str, item_build_name: str) -> list[str]:
    """Return relevant item combo names for mix-and-match in slots 4-6.

    Always includes at least one push combo. Adds anti-heal/shield when needed.
    Returns combo names that map to ITEM_COMBOS in item_builds.py.
    """
    combos = []

    # Always suggest at least one push option (Maiden & Ghouls push)
    if item_build_name not in ("Maiden Push",):
        combos.append("Maiden Burn")

    # Always suggest Hull Bastion for splitpush potential
    if "Hull" not in item_build_name and "Hullbreakin" not in item_build_name:
        combos.append("Hull Bastion Split")

    # Free AD Tank is universally good 4th-5th
    combos.append("Free AD Tank")

    # Stronk Bonk for sustained fight + catch potential
    if "Bonk" not in item_build_name and "Speed" not in item_build_name:
        combos.append("Stronk Bonk")

    # Sky Dragon Sustain for hard matchups
    if item_build_name not in ("Sundered Sky Rush",):
        combos.append("Sky Dragon Sustain")

    # Anti-heal vs healers
    if enemy in ANTI_HEAL_CHAMPS:
        combos.append("Anti-Heal")

    # Anti-shield vs shield champs
    if enemy in ANTI_SHIELD_CHAMPS:
        combos.append("Anti-Shield")

    # Shojin Amp if not already in core
    if "Shojin" not in item_build_name and "BBC" not in item_build_name:
        combos.append("Shojin Amp")

    return combos


# ============================================================================
# RULE 10: Build Order Note
# ============================================================================

def build_order_note(item_build_name: str, enemy: str) -> str:
    """Return a note about component buy order within the build path."""
    notes = {
        "Default BBC": "Shojin first for 12% pet DMG amp. BC second for shred. Sky 3rd for sustain.",
        "Iceborn Cleaver": "Sheen rush -> Iceborn first for slow field + armor. BC or Sky 2nd.",
        "Titanic Breaker": "Tiamat rush for waveclear -> Titanic -> Hullbreaker for split.",
        "VS Jax (Iceborn)": "Sheen rush -> Iceborn for slow field. W him during Counter Strike.",
        "VS Jax (Shojin)": "Shojin first for 12% pet amp -> Iceborn 2nd for defense.",
        "VS Morde": "BC first for armor shred -> FoN for magic DR + MS. Don't have Maiden when he Rs.",
        "VS Trundle": "Tiamat rush -> BC for shred. Exec early if he finishes Ravenous Hydra.",
        "VS Trynd (Conqueror)": "BC first -> Tiamat -> Titanic. Randuin's to reduce crits.",
        "VS Trynd (Iceborn Old)": "Sheen rush -> Iceborn for slow kite. DMP for MS to escape his R.",
        "VS Irelia": "Trinity for Sheen proc + dueling. Frozen Heart to cripple her AS.",
        "Eclipse Poke": "Eclipse first for burst poke -> Shojin for pet amp. E max.",
        "Sundered Sky Rush": "Sky first if hard matchup, Shojin first if ahead.",
        "Speed Rick": "Triforce or Tiamat->Sky first. Only Hull if they roam or you split free.",
        "Bonk Shovel": "Trinity first for Sheen proc. Sky + DMP beats ranged. Good low elo.",
        "Liandry Tank Shred": "BC first always. Eclipse if ahead, Liandry if behind or they rush HP.",
    }
    return notes.get(item_build_name, "")


# ============================================================================
# RULE 11: Late Game Note
# ============================================================================

def late_game_note(item_build_name: str) -> str:
    """Return a note about late game item swaps."""
    notes = {
        "Default BBC": "GA last item (ghouls stay alive during revive). Replace GA with Sterak's later if you have gold.",
        "Iceborn Cleaver": "Sell Hullbreaker if game may end on next fight. Buy GA or Sterak's.",
        "Titanic Breaker": "Sell Hull if teamfighting. Sterak's + Bloodmail give massive free AD late.",
        "Shojin Hull": "If game goes late, sell Edge of Night for Sterak's or GA.",
        "VS Jax (Iceborn)": "Spirit Visage 3rd for sustain + MR vs his hybrid damage.",
        "VS Trynd (Conqueror)": "Chempunk late if his healing is out of control.",
    }
    return notes.get(item_build_name, "GA as last item - ghouls stay alive during revive. Sell Hullbreaker if needed for teamfight.")


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
