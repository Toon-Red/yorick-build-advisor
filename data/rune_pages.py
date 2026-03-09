"""Rune page templates from the Kampsycho guide (Mobafire + docx).

Each template stores full numeric IDs from Data Dragon 16.4.1.
Shard IDs: 5008=AF, 5005=AS, 5007=AH, 5010=MS, 5002=Armor, 5003=MR, 5001=HP, 5011=HP%, 5013=Tenacity

Rune tree IDs:
  8000=Precision, 8100=Domination, 8200=Sorcery, 8300=Inspiration, 8400=Resolve
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RunePageTemplate:
    name: str
    primary_style_id: int
    sub_style_id: int
    selected_perk_ids: tuple[int, ...]  # 9 ints: keystone, row1, row2, row3, sec1, sec2, shard1, shard2, shard3
    description: str = ""


# --- Rune ID Constants ---
# Resolve (8400)
GRASP = 8437
DEMOLISH = 8446
FONT_OF_LIFE = 8463
SHIELD_BASH = 8401
CONDITIONING = 8429
SECOND_WIND = 8444
BONE_PLATING = 8473
OVERGROWTH = 8451
REVITALIZE = 8453
UNFLINCHING = 8242

# Precision (8000)
CONQUEROR = 8010
PRESENCE_OF_MIND = 8009
LEGEND_ALACRITY = 9104
LEGEND_HASTE = 9105
LEGEND_BLOODLINE = 9103
CUT_DOWN = 8017
LAST_STAND = 8299
COUP_DE_GRACE = 8014
TRIUMPH = 9111
ABSORB_LIFE = 9101

# Sorcery (8200)
ARCANE_COMET = 8229
SUMMON_AERY = 8214
PHASE_RUSH = 8230
MANAFLOW_BAND = 8226
NIMBUS_CLOAK = 8275
TRANSCENDENCE = 8210
CELERITY = 8234
ABSOLUTE_FOCUS = 8233
SCORCH = 8237
WATERWALKING = 8232
GATHERING_STORM = 8236

# Domination (8100)
HAIL_OF_BLADES = 9923
ELECTROCUTE = 8112
DARK_HARVEST = 8128
TASTE_OF_BLOOD = 8139
CHEAP_SHOT = 8126
SUDDEN_IMPACT = 8143
SIXTH_SENSE = 8137
GRISLY_MEMENTOS = 8140
DEEP_WARD = 8141
TREASURE_HUNTER = 8135
RELENTLESS_HUNTER = 8105
ULTIMATE_HUNTER = 8106

# Inspiration (8300)
FIRST_STRIKE = 8369
GLACIAL_AUGMENT = 8351
UNSEALED_SPELLBOOK = 8360
HEXTECH_FLASHTRAPTION = 8306
MAGICAL_FOOTWEAR = 8304
CASH_BACK = 8321
TRIPLE_TONIC = 8313
BISCUIT_DELIVERY = 8345
TIME_WARP_TONIC = 8352
COSMIC_INSIGHT = 8347
APPROACH_VELOCITY = 8410
JACK_OF_ALL_TRADES = 8316

# Shards
SHARD_AF = 5008   # Adaptive Force
SHARD_AS = 5005   # Attack Speed
SHARD_AH = 5007   # Ability Haste
SHARD_MS = 5010   # Move Speed
SHARD_ARMOR = 5002
SHARD_MR = 5003
SHARD_HP = 5001
SHARD_HP_PCT = 5011
SHARD_TENACITY = 5013  # +15% Tenacity/Slow Resist


# --- 10 Rune Page Templates ---
# Mapped from Kampsycho docx shorthand to Mobafire page numbers

RUNE_PAGES: dict[str, RunePageTemplate] = {
    # Page 1: Phase Rush — Mobility/kiting
    "Phase Rush": RunePageTemplate(
        name="Phase Rush",
        primary_style_id=8200,  # Sorcery
        sub_style_id=8400,      # Resolve
        selected_perk_ids=(
            PHASE_RUSH,       # Keystone
            MANAFLOW_BAND,    # Row 1
            CELERITY,         # Row 2
            SCORCH,           # Row 3
            DEMOLISH,         # Sec 1
            REVITALIZE,       # Sec 2
            SHARD_AS, SHARD_MS, SHARD_TENACITY,  # Shards [mobafire L185-188]
        ),
        description="Mobility/kiting build for matchups where you need to disengage quickly",
    ),

    # Page 2: Grasp-1 (Default Grasp) — Resolve/Precision
    "Grasp-1": RunePageTemplate(
        name="Grasp-1",
        primary_style_id=8400,  # Resolve
        sub_style_id=8000,      # Precision
        selected_perk_ids=(
            GRASP,            # Keystone
            DEMOLISH,         # Row 1
            BONE_PLATING,     # Row 2
            REVITALIZE,       # Row 3
            LEGEND_ALACRITY,  # Sec 1
            PRESENCE_OF_MIND, # Sec 2
            SHARD_AS, SHARD_HP, SHARD_TENACITY,  # Shards [mobafire L206-209]
        ),
        description="Default Grasp page — good all-around for short trades and tower taking",
    ),

    # Page 3: Comet — Sorcery/Resolve (pet poke)
    "Comet": RunePageTemplate(
        name="Comet",
        primary_style_id=8200,  # Sorcery
        sub_style_id=8400,      # Resolve
        selected_perk_ids=(
            ARCANE_COMET,     # Keystone
            MANAFLOW_BAND,    # Row 1
            TRANSCENDENCE,    # Row 2
            SCORCH,           # Row 3
            DEMOLISH,         # Sec 1
            REVITALIZE,       # Sec 2
            SHARD_AS, SHARD_HP, SHARD_TENACITY,  # Shards [mobafire L227-230]
        ),
        description="Pet poke build — E+ghouls proc Comet for ranged harass",
    ),

    # Page 4: Conqueror — Precision/Resolve (sustained damage)
    "Conqueror": RunePageTemplate(
        name="Conqueror",
        primary_style_id=8000,  # Precision
        sub_style_id=8400,      # Resolve
        selected_perk_ids=(
            CONQUEROR,        # Keystone
            PRESENCE_OF_MIND, # Row 1
            LEGEND_ALACRITY,  # Row 2
            CUT_DOWN,         # Row 3
            DEMOLISH,         # Sec 1
            REVITALIZE,       # Sec 2
            SHARD_AS, SHARD_HP, SHARD_TENACITY,  # Shards [mobafire L248-251]
        ),
        description="Sustained damage for extended fights vs tanks and bruisers",
    ),

    # Page 5: Aery — Sorcery/Resolve (aggressive poke)
    "Aery": RunePageTemplate(
        name="Aery",
        primary_style_id=8200,  # Sorcery
        sub_style_id=8400,      # Resolve
        selected_perk_ids=(
            SUMMON_AERY,      # Keystone
            MANAFLOW_BAND,    # Row 1
            CELERITY,         # Row 2
            SCORCH,           # Row 3
            DEMOLISH,         # Sec 1
            REVITALIZE,       # Sec 2
            SHARD_AS, SHARD_MS, SHARD_TENACITY,  # Shards [mobafire L269-272]
        ),
        description="Aggressive poke — Aery procs more often than Comet for frequent trades",
    ),

    # Page 6: Grasp-4 — Resolve/Inspiration (chase/mobility)
    "Grasp-4": RunePageTemplate(
        name="Grasp-4",
        primary_style_id=8400,  # Resolve
        sub_style_id=8300,      # Inspiration
        selected_perk_ids=(
            GRASP,            # Keystone
            DEMOLISH,         # Row 1
            SECOND_WIND,      # Row 2
            REVITALIZE,       # Row 3
            CASH_BACK,        # Sec 1
            APPROACH_VELOCITY, # Sec 2
            SHARD_AS, SHARD_AF, SHARD_TENACITY,  # Shards [mobafire L290-293]
        ),
        description="Chase/mobility Grasp — Approach Velocity for sticking to targets after W",
    ),

    # Page 7: First Strike — Inspiration/Resolve (economy)
    "First Strike": RunePageTemplate(
        name="First Strike",
        primary_style_id=8300,  # Inspiration
        sub_style_id=8400,      # Resolve
        selected_perk_ids=(
            FIRST_STRIKE,     # Keystone
            CASH_BACK,        # Row 1
            TRIPLE_TONIC,     # Row 2
            APPROACH_VELOCITY, # Row 3
            DEMOLISH,         # Sec 1
            REVITALIZE,       # Sec 2
            SHARD_AS, SHARD_AF, SHARD_HP,  # Shards [mobafire L311-314]
        ),
        description="Economy page — First Strike gold generation for scaling builds",
    ),

    # Page 8: Grasp-2 — Resolve/Sorcery (poke + tenacity)
    "Grasp-2": RunePageTemplate(
        name="Grasp-2",
        primary_style_id=8400,  # Resolve
        sub_style_id=8200,      # Sorcery
        selected_perk_ids=(
            GRASP,            # Keystone
            DEMOLISH,         # Row 1
            BONE_PLATING,     # Row 2
            UNFLINCHING,      # Row 3
            MANAFLOW_BAND,    # Sec 1
            SCORCH,           # Sec 2
            SHARD_AS, SHARD_HP, SHARD_TENACITY,  # Shards [mobafire L332-335]
        ),
        description="Poke + tenacity Grasp — Manaflow for mana, Unflinching for CC-heavy lanes",
    ),

    # Page 9: Hail of Blades — Domination/Resolve (burst AS)
    "Hail of Blades": RunePageTemplate(
        name="Hail of Blades",
        primary_style_id=8100,  # Domination
        sub_style_id=8400,      # Resolve
        selected_perk_ids=(
            HAIL_OF_BLADES,   # Keystone
            TASTE_OF_BLOOD,   # Row 1
            SIXTH_SENSE,      # Row 2
            ULTIMATE_HUNTER,  # Row 3
            DEMOLISH,         # Sec 1
            OVERGROWTH,       # Sec 2
            SHARD_AS, SHARD_HP, SHARD_HP,  # Shards [mobafire L353-356]
        ),
        description="Burst attack speed — fast Q trades and quick grave generation",
    ),

    # Page 10: Grasp-3 — Resolve/Domination (sustain)
    "Grasp-3": RunePageTemplate(
        name="Grasp-3",
        primary_style_id=8400,  # Resolve
        sub_style_id=8100,      # Domination
        selected_perk_ids=(
            GRASP,            # Keystone
            DEMOLISH,         # Row 1
            SECOND_WIND,      # Row 2
            REVITALIZE,       # Row 3
            TASTE_OF_BLOOD,   # Sec 1
            SIXTH_SENSE,      # Sec 2
            SHARD_AS, SHARD_HP, SHARD_TENACITY,  # Shards [mobafire L374-377]
        ),
        description="Sustain Grasp — Second Wind + Taste of Blood for heavy poke lanes",
    ),
}


def get_rune_page(name: str) -> RunePageTemplate | None:
    """Look up a rune page template by name (case-insensitive)."""
    for key, page in RUNE_PAGES.items():
        if key.lower() == name.lower():
            return page
    return None


def all_rune_page_names() -> list[str]:
    """Return all rune page template names."""
    return list(RUNE_PAGES.keys())
