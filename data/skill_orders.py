"""Skill order templates from Kampsycho Mobafire guide.

Three named skill orders, each defining the exact ability to level at levels 1-18.
Matchups link to these by ID. The engine picks the right one based on matchup tags
and keystone selection.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SkillOrderTemplate:
    id: str
    name: str
    description: str
    levels: tuple[str, ...]  # 18 entries: ability at each level (Q/W/E/R)
    max_order: tuple[str, ...]  # Which ability maxed first, second, third (e.g. ("Q","E","W"))
    condition: str  # When to use this skill order


# Level-by-level skill orders extracted from Mobafire screenshots
# Levels:  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18

SKILL_ORDERS: dict[str, SkillOrderTemplate] = {
    "w_stack": SkillOrderTemplate(
        id="w_stack",
        name="W-Stack vs Immobile",
        description="Put 3 points into W by Lvl 7, then max Q, then E, W last. Into immobile champs or one-dash champs.",
        levels=("Q", "E", "W", "Q", "W", "R", "W", "Q", "Q", "Q", "R", "E", "E", "E", "E", "R", "W", "W"),
        max_order=("Q", "E", "W"),
        condition="vs immobile / one-dash champs",
    ),
    "standard": SkillOrderTemplate(
        id="standard",
        name="Standard Q-Max",
        description="Start Q, 2 points into E, then Q max. Put 3 points into W after Q is maxed, then max E and W last.",
        levels=("Q", "E", "W", "E", "Q", "R", "Q", "Q", "Q", "E", "R", "W", "E", "W", "E", "R", "W", "W"),
        max_order=("Q", "E", "W"),
        condition="default / standard matchups",
    ),
    "e_max": SkillOrderTemplate(
        id="e_max",
        name="E-Max vs Ranged",
        description="E max order vs ranged when using Comet or Aery.",
        levels=("E", "Q", "W", "E", "Q", "R", "E", "E", "E", "Q", "R", "Q", "Q", "W", "W", "R", "W", "W"),
        max_order=("E", "Q", "W"),
        condition="vs ranged + Comet/Aery keystone",
    ),
}


# --- Matchup → Skill Order Resolution ---

# Champions where W-stack (3 points by lvl 7) is recommended.
# Immobile or single-dash champs where the wall trap is high value.
W_STACK_CHAMPS = {
    "Mordekaiser", "Dr. Mundo", "Nasus", "Illaoi", "Darius", "Garen",
    "Singed", "Sion", "Maokai", "Cho'Gath", "Malphite", "Ornn",
    "Sett", "Volibear", "Olaf", "Udyr", "Warwick", "Trundle",
    "Tahm Kench", "Skarner", "Zac", "Sejuani", "Poppy",
    "Jax", "Kled", "Yorick", "Briar",
    "Swain", "Vladimir", "Rumble", "Heimerdinger", "Anivia",
    "Sylas", "Cassiopeia", "Ryze",
}

# Champions where E-max is recommended (ranged matchups with Comet/Aery).
E_MAX_CHAMPS = {
    "Akali", "Akshan", "Aurora", "Gnar", "Kayle", "Quinn", "Teemo",
    "Smolder", "Vayne", "Varus", "Kennen",
}

# Keystones that pair with E-max
E_MAX_KEYSTONES = {"Comet", "Aery"}


def resolve_skill_order(enemy: str, keystone: str, tags: tuple[str, ...] = ()) -> str:
    """Determine which skill order to use for a matchup.

    Returns skill order ID: "w_stack", "standard", or "e_max".
    """
    # E-max tag in matchup data takes priority
    if "e_max" in tags and keystone in E_MAX_KEYSTONES:
        return "e_max"

    # Explicit E-max champs with appropriate keystone
    if enemy in E_MAX_CHAMPS and keystone in E_MAX_KEYSTONES:
        return "e_max"

    # W-stack for immobile/single-dash
    if enemy in W_STACK_CHAMPS:
        return "w_stack"

    # Default: standard Q-max
    return "standard"


def get_skill_order(skill_order_id: str) -> SkillOrderTemplate:
    """Get a skill order template by ID."""
    return SKILL_ORDERS.get(skill_order_id, SKILL_ORDERS["standard"])
