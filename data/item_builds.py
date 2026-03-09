"""Item build templates from the Kampsycho guide (Mobafire + docx).

Each template stores full numeric item IDs from Data Dragon 16.4.1.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ItemBuildTemplate:
    name: str
    starter: tuple[int, ...]      # Starting items
    boots: tuple[int, ...]        # Boot options (first is default)
    core: tuple[int, ...]         # Core build path (ordered)
    situational: tuple[int, ...]  # Situational options
    description: str = ""


# --- Item ID Constants ---
# Starters
DORANS_BLADE = 1055
DORANS_SHIELD = 1054
CORRUPTING_POTION = 2033
DARK_SEAL = 1082
LONG_SWORD = 1036
HEALTH_POTION = 2003
REFILLABLE_POTION = 2031

# Boots
PLATED_STEELCAPS = 3047
MERCURY_TREADS = 3111
IONIAN_BOOTS = 3158
BOOTS_OF_SWIFTNESS = 3009

# Core items
SPEAR_OF_SHOJIN = 3161
BLACK_CLEAVER = 3071
SUNDERED_SKY = 6610
HULLBREAKER = 3181
STERAKS_GAGE = 3053
ICEBORN_GAUNTLET = 6662
SPIRIT_VISAGE = 3065
TITANIC_HYDRA = 3748
HOLLOW_RADIANCE = 6664
JAKSHO = 6665
UNENDING_DESPAIR = 2502
TRINITY_FORCE = 3078
DEAD_MANS_PLATE = 3742
FORCE_OF_NATURE = 4401
EXPERIMENTAL_HEXPLATE = 3073
BASTIONBREAKER = 2520
OVERLORDS_BLOODMAIL = 2501

# Defensive
WARMOGS_ARMOR = 3083
THORNMAIL = 3075
RANDUINS_OMEN = 3143
FROZEN_HEART = 3110
KAENIC_ROOKERN = 2504
ABYSSAL_MASK = 8020

# Lethality / AD
SERYLDAS_GRUDGE = 6694
DEATHS_DANCE = 6333
MAW_OF_MALMORTIUS = 3156
GUARDIAN_ANGEL = 3026
EDGE_OF_NIGHT = 3814
YOUMUUS_GHOSTBLADE = 3142
PROFANE_HYDRA = 6698

# Guide-specific items
PROTOPLASM_HARNESS = 2525
ARMORED_ADVANCE = 3174
ECLIPSE = 6692
LIANDRYS_TORMENT = 6653
TIAMAT = 3077
BLADE_OF_THE_RUINED_KING = 3153
SERPENTS_FANG = 226695
CHEMPUNK_CHAINSWORD = 226609
RIFTMAKER = 224633
MALIGNANCE = 223118
ENDLESS_HUNGER = 222517

# Matchup-specific components
CLOTH_ARMOR = 1029
EXECUTIONERS_CALLING = 3123
BRAMBLE_VEST = 3076

# --- 16 Item Build Templates ---

ITEM_BUILDS: dict[str, ItemBuildTemplate] = {
    # 1. Default BBC (Bread and Butter Cleaver)
    "Default BBC": ItemBuildTemplate(
        name="Default BBC",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS, IONIAN_BOOTS),
        core=(SPEAR_OF_SHOJIN, BLACK_CLEAVER, SUNDERED_SKY),
        situational=(HULLBREAKER, STERAKS_GAGE, DEATHS_DANCE, SPIRIT_VISAGE),
        description="Shojin gives pets 12% DMG Amp, Only missing 8% from Yorick's old E that gave 20% and Black Cleaver gives Ghouls everything they scale with (HP, AD, MS) and Shred, While Hull & Bastion Breaker help you Splitpush and abuse Turret plates [mobafire L449]",
    ),

    # 2. Iceborn Cleaver
    "Iceborn Cleaver": ItemBuildTemplate(
        name="Iceborn Cleaver",
        starter=(DORANS_SHIELD, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(ICEBORN_GAUNTLET, BLACK_CLEAVER, SUNDERED_SKY),
        situational=(SPEAR_OF_SHOJIN, SPIRIT_VISAGE, STERAKS_GAGE, FROZEN_HEART),
        description="Default Tank Build, Gauntlet into Cleaver or Gauntlet into Sky, Can work into most AD counters like Jax, Ren, Kled [mobafire L464]",
    ),

    # 3. Titanic Breaker
    "Titanic Breaker": ItemBuildTemplate(
        name="Titanic Breaker",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(TITANIC_HYDRA, HULLBREAKER, OVERLORDS_BLOODMAIL),
        situational=(STERAKS_GAGE, SPEAR_OF_SHOJIN, BLACK_CLEAVER, SUNDERED_SKY),
        description="Titanic Breaker & Blood Gage — Good into Non HP/Tank Killers like Riven, Renekton, Kled, Champs that need to snowball, Sky 5th or Shojin, Sky for Sustain, Shojin for DMG [mobafire L455-456]",
    ),

    # 4. Shojin Hull
    "Shojin Hull": ItemBuildTemplate(
        name="Shojin Hull",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, BOOTS_OF_SWIFTNESS),
        core=(SPEAR_OF_SHOJIN, BLACK_CLEAVER, HULLBREAKER, BASTIONBREAKER),
        situational=(EDGE_OF_NIGHT, YOUMUUS_GHOSTBLADE, STERAKS_GAGE, SUNDERED_SKY),
        description="Full Splitpush with Lethality items to boost Bastion Breaker, Choose between Shojin or Cleaver for Scaling DMG Item [mobafire L473-474]",
    ),

    # 5. Iceborn Dragon (Tank)
    "Iceborn Dragon": ItemBuildTemplate(
        name="Iceborn Dragon",
        starter=(DORANS_SHIELD, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(ICEBORN_GAUNTLET, SPEAR_OF_SHOJIN, SPIRIT_VISAGE, JAKSHO),
        situational=(PROTOPLASM_HARNESS, UNENDING_DESPAIR),
        description="Tankier Variation of Iceborn Cleaver [mobafire L458-459]",
    ),

    # 6. Speed Rick
    "Speed Rick": ItemBuildTemplate(
        name="Speed Rick",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(BOOTS_OF_SWIFTNESS, PLATED_STEELCAPS),
        core=(TRINITY_FORCE, BLACK_CLEAVER, DEAD_MANS_PLATE),
        situational=(FORCE_OF_NATURE, SUNDERED_SKY, HULLBREAKER),
        description="vs Ranged Team Comps or against Quinn, Gnar, Ryze, Cassio, etc. Choose Triforce or Tiamat into Sundered Sky first, only Buy Hull into Roaming ones like Quinn or if you can Split for free [mobafire L485-486]",
    ),

    # 7. Conqueror Bruiser
    "Conqueror Bruiser": ItemBuildTemplate(
        name="Conqueror Bruiser",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(SPEAR_OF_SHOJIN, BLACK_CLEAVER, STERAKS_GAGE),
        situational=(SUNDERED_SKY, DEATHS_DANCE, SPIRIT_VISAGE, HULLBREAKER),
        description="Sustained fight build — pairs with Conqueror for extended trades vs bruisers",
    ),

    # 8. Anti-Tank
    "Anti-Tank": ItemBuildTemplate(
        name="Anti-Tank",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, IONIAN_BOOTS),
        core=(SPEAR_OF_SHOJIN, BLACK_CLEAVER, SERYLDAS_GRUDGE),
        situational=(SUNDERED_SKY, STERAKS_GAGE, HULLBREAKER),
        description="Max armor shred vs tanks — Cleaver + Serylda's for armor pen stacking",
    ),

    # 9. Anti-AP
    "Anti-AP": ItemBuildTemplate(
        name="Anti-AP",
        starter=(DORANS_SHIELD, HEALTH_POTION),
        boots=(MERCURY_TREADS,),
        core=(SPEAR_OF_SHOJIN, SPIRIT_VISAGE, KAENIC_ROOKERN),
        situational=(BLACK_CLEAVER, MAW_OF_MALMORTIUS, FORCE_OF_NATURE, STERAKS_GAGE),
        description="MR stacking vs AP-heavy lanes — Spirit Visage + Kaenic Rookern",
    ),

    # 10. Hexplate Engage
    "Hexplate Engage": ItemBuildTemplate(
        name="Hexplate Engage",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(BOOTS_OF_SWIFTNESS, PLATED_STEELCAPS),
        core=(EXPERIMENTAL_HEXPLATE, BLACK_CLEAVER, SUNDERED_SKY),
        situational=(SPEAR_OF_SHOJIN, STERAKS_GAGE, DEAD_MANS_PLATE),
        description="Engage build — Hexplate ult for gap closing + teamfight presence",
    ),

    # 11. Lethal Splitpush (from mobafire L461)
    "Lethal Splitpush": ItemBuildTemplate(
        name="Lethal Splitpush",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(TITANIC_HYDRA, HULLBREAKER, BASTIONBREAKER),
        situational=(SERPENTS_FANG, CHEMPUNK_CHAINSWORD, BLACK_CLEAVER),
        description="Lethality Build for Splitpushing vs Heal & Shield abusers like Riven, Ambessa [mobafire L461]",
    ),

    # 12. Bloodmail Bruiser
    "Bloodmail Bruiser": ItemBuildTemplate(
        name="Bloodmail Bruiser",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(SPEAR_OF_SHOJIN, BLACK_CLEAVER, OVERLORDS_BLOODMAIL),
        situational=(SUNDERED_SKY, STERAKS_GAGE, SPIRIT_VISAGE),
        description="Both Items give you free AD up to 150, Sterak Gives 40 to Yorick, Bloodmail gives 30 from stats then another 30-50 from HP to AD conversion. Bloodmail scales off HP and maxes out at 30% HP, Sterak also Procs the shield at 30% [mobafire L505]",
    ),

    # 13. Full Armor
    "Full Armor": ItemBuildTemplate(
        name="Full Armor",
        starter=(DORANS_SHIELD, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, ARMORED_ADVANCE),
        core=(ICEBORN_GAUNTLET, DEATHS_DANCE, THORNMAIL),
        situational=(PROTOPLASM_HARNESS, FROZEN_HEART, RANDUINS_OMEN),
        description="VS Full AD Team — auto attackers get Thornmail, crits get Omen, high AS melee get Frozen Heart, DD into Sterak if needed [mobafire L531-532]",
    ),

    # 14. Full MR
    "Full MR": ItemBuildTemplate(
        name="Full MR",
        starter=(DORANS_SHIELD, HEALTH_POTION),
        boots=(MERCURY_TREADS,),
        core=(KAENIC_ROOKERN, SPIRIT_VISAGE, FORCE_OF_NATURE),
        situational=(STERAKS_GAGE, JAKSHO, MAW_OF_MALMORTIUS),
        description="VS Full AP or Heavy Magic DMG — vs AP Burst like LB/Zoe/Annie go Rookern + Sterak, against APs that slowly kill go FoN into Jak'Sho or Rookern [mobafire L528-529]",
    ),

    # 15. Guardian Angel Build
    "GA Revive": ItemBuildTemplate(
        name="GA Revive",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(SPEAR_OF_SHOJIN, BLACK_CLEAVER, GUARDIAN_ANGEL),
        situational=(SUNDERED_SKY, STERAKS_GAGE, DEATHS_DANCE),
        description="Last Item Always when LATE GAME (Ghouls stay Alive as you revive). Replace with Sterak's later if you have gold, Sell Hullbreaker if game may end if you lose fight [mobafire L491]",
    ),

    # 16. Unending Despair Tank
    "Unending Despair": ItemBuildTemplate(
        name="Unending Despair",
        starter=(DORANS_SHIELD, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(ICEBORN_GAUNTLET, UNENDING_DESPAIR, SPIRIT_VISAGE),
        situational=(JAKSHO, WARMOGS_ARMOR, BLACK_CLEAVER, THORNMAIL),
        description="Drain tank — Unending Despair aura + Spirit Visage amplified healing",
    ),

    # 17. Eclipse Poke (E max build from guide)
    "Eclipse Poke": ItemBuildTemplate(
        name="Eclipse Poke",
        starter=(LONG_SWORD, REFILLABLE_POTION),
        boots=(IONIAN_BOOTS, BOOTS_OF_SWIFTNESS),
        core=(ECLIPSE, SPEAR_OF_SHOJIN, BLACK_CLEAVER),
        situational=(SUNDERED_SKY, HULLBREAKER, SERYLDAS_GRUDGE, STERAKS_GAGE),
        description="E max into Eclipse & Shojin with Comet or Aery Rune. Works into range top: Teemo, Aurora, Akali, Kayle, Gnar, Quinn, etc. [mobafire L1647]",
    ),

    # 18. Sundered Sky Rush (vs poke/ranged)
    "Sundered Sky Rush": ItemBuildTemplate(
        name="Sundered Sky Rush",
        starter=(DORANS_SHIELD, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(SUNDERED_SKY, SPEAR_OF_SHOJIN, SPIRIT_VISAGE),
        situational=(DEATHS_DANCE, ENDLESS_HUNGER, ECLIPSE, STERAKS_GAGE),
        description="Sky Dragon's Sustain — Fighter Tank Build for aggressive Yorick Mains. Go Sky first if Hard Matchup, Shojin First otherwise [mobafire L467-468]",
    ),

    # 19. Liandry Tank Shred (vs HP tanks)
    "Liandry Tank Shred": ItemBuildTemplate(
        name="Liandry Tank Shred",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, IONIAN_BOOTS),
        core=(BLACK_CLEAVER, LIANDRYS_TORMENT, SPEAR_OF_SHOJIN),
        situational=(ECLIPSE, ABYSSAL_MASK, UNENDING_DESPAIR),
        description="Hybrid Monk — Beats any Tank, if Ahead BC into Eclipse, if they rush HP or you're behind BC into Liandry instead, good into Cho'Gath, Tahmkench, Ornn, Mundo, Nasus. Can solo kill Darius, Illaoi, Ornn when Maiden is released [mobafire L482-483]",
    ),

    # 20. Bonk Shovel — Classic Yorick (from mobafire L476)
    "Bonk Shovel": ItemBuildTemplate(
        name="Bonk Shovel",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(TRINITY_FORCE, SUNDERED_SKY, DEAD_MANS_PLATE),
        situational=(HULLBREAKER, SERYLDAS_GRUDGE, SPEAR_OF_SHOJIN),
        description="Old Classic Build, Best Splitpush Build VS Towers and most ranged champs. Sky + Deadmans beats Ranged champs, Really good in low elo, good into most fighters top like Yone or Yasuo [mobafire L476]",
    ),

    # 21. Voidborn Dragon — AP DPS Amp (from mobafire L479)
    "Voidborn Dragon": ItemBuildTemplate(
        name="Voidborn Dragon",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(SPEAR_OF_SHOJIN, RIFTMAKER, OVERLORDS_BLOODMAIL),
        situational=(STERAKS_GAGE, SPIRIT_VISAGE, UNENDING_DESPAIR),
        description="AP DMG AMP version of Double Pen Build, AP Fighter Tank. Shred Tanks and Amplify your DMG by 26%, Heal for 10% Omnivamp and Increase E's %HP DMG per 100 AP, While Riftmaker Converts your HP Into AP [mobafire L479]",
    ),

    # 22. Hullbreakin' Dat Ashe (from mobafire L470)
    "Hullbreakin Dat Ashe": ItemBuildTemplate(
        name="Hullbreakin Dat Ashe",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, BOOTS_OF_SWIFTNESS),
        core=(TRINITY_FORCE, HULLBREAKER, DEAD_MANS_PLATE),
        situational=(SPEAR_OF_SHOJIN, TITANIC_HYDRA, HOLLOW_RADIANCE),
        description="Choose Between Triforce or Shojin. Splitpush-focused with movespeed and waveclear [mobafire L470]",
    ),

    # 23. Maiden Push Build (from mobafire L488)
    "Maiden Push": ItemBuildTemplate(
        name="Maiden Push",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(BLACK_CLEAVER, LIANDRYS_TORMENT, MALIGNANCE),
        situational=(SPEAR_OF_SHOJIN, HOLLOW_RADIANCE, DEAD_MANS_PLATE),
        description="Not a Full build, just items that work when releasing Maiden or Ghouls in sidelane. Maiden & Ghouls can proc Eclipse & Liandry to lower enemies HP, while Malignance lowers Maiden Cooldown and deals DMG [mobafire L488]",
    ),

    # ========== Matchup-Specific Build Templates ==========

    # 24. VS Jax (Iceborn) — Grasp path [mobafire L537-538]
    "VS Jax (Iceborn)": ItemBuildTemplate(
        name="VS Jax (Iceborn)",
        starter=(CLOTH_ARMOR, REFILLABLE_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(ICEBORN_GAUNTLET, BLACK_CLEAVER, SPIRIT_VISAGE),
        situational=(SPEAR_OF_SHOJIN, ABYSSAL_MASK, SUNDERED_SKY),
        description="VS Jax Grasp path — Sheen rush into Iceborn for slow field + armor. "
                    "BC or Shojin 2nd for shred/DMG, Spirit Visage 3rd for sustain + MR vs his hybrid damage. "
                    "W him when he Counter Strikes to trap him until it expires [mobafire L537-538].",
    ),

    # 25. VS Jax (Shojin) — Conqueror/Comet path [mobafire L540-541]
    "VS Jax (Shojin)": ItemBuildTemplate(
        name="VS Jax (Shojin)",
        starter=(CLOTH_ARMOR, REFILLABLE_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(SPEAR_OF_SHOJIN, ICEBORN_GAUNTLET, BLACK_CLEAVER, ABYSSAL_MASK),
        situational=(SPIRIT_VISAGE, SUNDERED_SKY),
        description="VS Jax Shojin-first path — rush Shojin for 12% pet DMG amp then Iceborn second. "
                    "Works with Conqueror or Comet for poke-heavy lane. Abyssal Mask handles his hybrid damage. "
                    "Poke with E+ghouls, W his Counter Strike [mobafire L540-541].",
    ),

    # 26. VS Morde — BC + FoN + Shojin + DMP [mobafire L543-544]
    "VS Morde": ItemBuildTemplate(
        name="VS Morde",
        starter=(LONG_SWORD, REFILLABLE_POTION),
        boots=(MERCURY_TREADS, BOOTS_OF_SWIFTNESS),
        core=(BLACK_CLEAVER, FORCE_OF_NATURE, SPEAR_OF_SHOJIN, DEAD_MANS_PLATE),
        situational=(SERPENTS_FANG, SPIRIT_VISAGE),
        description="VS Mordekaiser — BC first for armor shred, FoN for magic damage reduction + MS, "
                    "Shojin for pet DMG amp, DMP for movespeed. Serpent's Fang situational to break his passive shield. "
                    "Null-Magic Mantle early for MR. Don't have Maiden out when he Rs you [mobafire L543-544].",
    ),

    # 27. VS Trundle — BC + Titanic + Hull [mobafire L546-547]
    "VS Trundle": ItemBuildTemplate(
        name="VS Trundle",
        starter=(CLOTH_ARMOR, REFILLABLE_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(BLACK_CLEAVER, TITANIC_HYDRA, HULLBREAKER),
        situational=(EXECUTIONERS_CALLING, BLADE_OF_THE_RUINED_KING, SPEAR_OF_SHOJIN, DEAD_MANS_PLATE),
        description="VS Trundle — Tiamat rush into BC for shred, Titanic for waveclear, Hull for splitpush. "
                    "Buy Executioner's Calling if he finishes Ravenous Hydra (anti-heal his lifesteal). "
                    "BOTRK good 4th+ item for his high HP. His R steals your stats — don't ult first [mobafire L546-547].",
    ),

    # 28. VS Trynd (Conqueror) — BC + Titanic + Randuin's [mobafire L549-550]
    "VS Trynd (Conqueror)": ItemBuildTemplate(
        name="VS Trynd (Conqueror)",
        starter=(CLOTH_ARMOR, REFILLABLE_POTION),
        boots=(PLATED_STEELCAPS,),
        core=(BLACK_CLEAVER, TITANIC_HYDRA, RANDUINS_OMEN),
        situational=(DEAD_MANS_PLATE, EXECUTIONERS_CALLING, SPEAR_OF_SHOJIN, HULLBREAKER, CHEMPUNK_CHAINSWORD),
        description="VS Tryndamere Conqueror path — BC + Titanic for sustained DPS, Randuin's to reduce his crits. "
                    "Executioner's early if he heals too much. Exhaust is mandatory — save it for his R. "
                    "W him when he spins in, disengage when he ults [mobafire L549-550].",
    ),

    # 29. VS Irelia — Trinity + Titanic + Frozen Heart [mobafire L552-553]
    "VS Irelia": ItemBuildTemplate(
        name="VS Irelia",
        starter=(CLOTH_ARMOR, REFILLABLE_POTION),
        boots=(PLATED_STEELCAPS,),
        core=(TRINITY_FORCE, TITANIC_HYDRA, FROZEN_HEART),
        situational=(BLADE_OF_THE_RUINED_KING, EXECUTIONERS_CALLING, BRAMBLE_VEST, SUNDERED_SKY),
        description="VS Irelia — Trinity for Sheen proc + dueling, Titanic for waveclear, "
                    "Frozen Heart to cripple her AS-reliant kit (Q resets need attack speed). "
                    "Buy Bramble Vest or Executioner's early to cut her Q healing. "
                    "BOTRK good additional item for stat value. Her Q one-shots ghouls — W to cancel Q chain [mobafire L552-553].",
    ),

    # 30. VS Trynd (Iceborn Old) — Iceborn + BC + DMP [mobafire L555-556]
    "VS Trynd (Iceborn Old)": ItemBuildTemplate(
        name="VS Trynd (Iceborn Old)",
        starter=(CLOTH_ARMOR, REFILLABLE_POTION),
        boots=(PLATED_STEELCAPS,),
        core=(ICEBORN_GAUNTLET, BLACK_CLEAVER, DEAD_MANS_PLATE),
        situational=(EXECUTIONERS_CALLING, SPEAR_OF_SHOJIN, HULLBREAKER),
        description="VS Tryndamere Iceborn tank path — Iceborn slow field kites him, BC shreds armor, "
                    "DMP for movespeed to escape his R duration. Old reliable tank path. "
                    "Buy Executioner's if needed for his Q heal [mobafire L555-556].",
    ),

    # 31. VS Ranged Top — Shojin + BC + Sky + Hull [mobafire L534-535]
    "VS Ranged Top": ItemBuildTemplate(
        name="VS Ranged Top",
        starter=(DORANS_SHIELD, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS, BOOTS_OF_SWIFTNESS),
        core=(SPEAR_OF_SHOJIN, BLACK_CLEAVER, SUNDERED_SKY, HULLBREAKER),
        situational=(BRAMBLE_VEST, DEAD_MANS_PLATE, FORCE_OF_NATURE),
        description="VS Ranged Top (Teemo, Vayne, Kennen, etc.) — Doran's Shield start for sustain. "
                    "Shojin for pet DMG amp, BC for shred, Sky for sustain on catches, Hull for split pressure. "
                    "Aery + Bramble Vest: their autos trigger Bramble which triggers Aery for free poke. Max E [mobafire L534-535].",
    ),

    # 32. Default Titanic Path — BC + Titanic + Hull
    "Default Titanic Path": ItemBuildTemplate(
        name="Default Titanic Path",
        starter=(DORANS_BLADE, HEALTH_POTION),
        boots=(PLATED_STEELCAPS, MERCURY_TREADS),
        core=(BLACK_CLEAVER, TITANIC_HYDRA, HULLBREAKER),
        situational=(BASTIONBREAKER, HOLLOW_RADIANCE, DEAD_MANS_PLATE, SPEAR_OF_SHOJIN),
        description="Default Titanic Path — BC for shred, Titanic for waveclear + HP scaling, Hull for splitpush. "
                    "Good all-around path when you want waveclear + splitting power. "
                    "Works with Conqueror for sustained trades.",
    ),
}


def get_item_build(name: str) -> ItemBuildTemplate | None:
    """Look up an item build template by name (case-insensitive)."""
    for key, build in ITEM_BUILDS.items():
        if key.lower() == name.lower():
            return build
    return None


def all_item_build_names() -> list[str]:
    """Return all item build template names."""
    return list(ITEM_BUILDS.keys())
