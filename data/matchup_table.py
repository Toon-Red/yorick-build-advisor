"""Matchup table: 71 champion entries from Kampsycho guide + video.

Each entry maps enemy champion → difficulty, recommended keystones, item category,
shard overrides, exhaust viability, and matchup-specific advice.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MatchupInfo:
    difficulty: str                          # Easy, Medium, Advanced, HARD, EXTREME
    keystones: tuple[str, ...]               # Priority-ordered keystone recommendations
    item_category: str = "default"           # Item path category (see rules.py)
    tags: tuple[str, ...] = ()               # Archetype tags for rule lookups
    shard_override: str | None = None        # "MS", "AF", or None (use default)
    exhaust_viable: bool = False             # Whether Exhaust is recommended/viable
    summoner_spells: str = "Ghost/Ignite"    # Default summoner spell recommendation
    special_note: str = ""                   # BAN HER, etc.
    advice: str = ""                         # Short matchup advice


# ============================================================================
# ALL 71 MATCHUP ENTRIES — from Kampsycho docx + Mobafire + video notes
# ============================================================================

MATCHUP_TABLE: dict[str, MatchupInfo] = {
    "Aatrox": MatchupInfo(
        difficulty="HARD",
        keystones=("Conqueror", "Comet"),
        item_category="default",
        tags=("vs_fighter", "vs_sustain"),
        advice="Dodge Q sweetspots. W him when he Qs. Ghouls body-block Q. Post-6 with Maiden you win extended trades if he misses Q.",
    ),
    "Akali": MatchupInfo(
        difficulty="Advanced",
        keystones=("Comet", "Aery"),
        item_category="eclipse_poke",
        tags=("vs_assassin", "vs_ap", "e_max"),
        exhaust_viable=True,
        advice="E max with Eclipse. Rush Null Magic Mantle on first back. W her when she dashes in and shroud is down. Mercs for MR + tenacity. Exhaust her all-in if she snowballs.",
    ),
    "Akshan": MatchupInfo(
        difficulty="Advanced",
        keystones=("Aery", "Comet"),
        item_category="eclipse_poke",
        tags=("vs_ranged", "vs_adc_top", "e_max"),
        advice="Ranged matchup — Second Wind. Let him push, farm under tower. W him to cancel his E swing.",
    ),
    "Ambessa": MatchupInfo(
        difficulty="HARD",
        keystones=("Aery", "Conqueror"),
        item_category="default",
        tags=("vs_fighter", "vs_dash"),
        advice="Multiple dashes but short-range. Poke with E+Aery. Disengage after E+ghouls poke.",
    ),
    "Anivia": MatchupInfo(
        difficulty="Advanced",
        keystones=("Comet", "Aery", "Phase Rush"),
        item_category="default",
        tags=("vs_ap", "vs_zone_control"),
        advice="Her wall blocks ghouls. W her — she's immobile. Kill egg with ghouls. Push hard, she has mana issues early.",
    ),
    "Aurelion Sol": MatchupInfo(
        difficulty="Advanced",
        keystones=("Aery", "Comet"),
        item_category="default",
        tags=("vs_ap", "vs_ranged"),
        advice="He scales hard — punish early. W him when he walks up. He's immobile without flash.",
    ),
    "Aurora": MatchupInfo(
        difficulty="Advanced",
        keystones=("Comet", "Aery"),
        item_category="eclipse_poke",
        tags=("vs_ap", "vs_ranged", "e_max"),
        advice="E max with Eclipse. She's squishy — land E and all-in. W her when she tries to escape with R.",
    ),
    "Briar": MatchupInfo(
        difficulty="Medium",
        keystones=("Grasp-1", "Conqueror"),
        item_category="default",
        tags=("vs_fighter", "vs_sustain", "vs_dash"),
        advice="Wall her during frenzy to trap her with ghouls. Bait W, then commit with E+W after it ends.",
    ),
    "Camille": MatchupInfo(
        difficulty="HARD",
        keystones=("Comet", "Aery", "Conqueror"),
        item_category="default",
        tags=("vs_fighter", "vs_true_damage", "vs_dash"),
        advice="W where she will land from E. Don't fight in her R zone without ghouls. Force extended fights with Maiden.",
    ),
    "Cassiopeia": MatchupInfo(
        difficulty="Medium",
        keystones=("Aery", "Conqueror"),
        item_category="default",
        tags=("vs_ap", "vs_ranged"),
        advice="High DPS but squishy. Don't face her (R stuns). Build MR. Farm safe, outscale in side lane.",
    ),
    "Cho'Gath": MatchupInfo(
        difficulty="Advanced",
        keystones=("Conqueror", "Hail of Blades"),
        item_category="liandry_shred",
        tags=("vs_tank", "anti_hp_stack"),
        advice="HP stacker — Liandry's burn shreds him. Dodge Q, don't stand in W silence. Out-split him hard.",
    ),
    "Darius": MatchupInfo(
        difficulty="Easy",
        keystones=("Comet", "Conqueror"),
        item_category="default",
        tags=("vs_fighter", "poke_lane"),
        shard_override="MS",
        advice="Poke with E+ghouls from range. W him when he uses E pull. Don't let him get 5 stacks.",
    ),
    "Dr. Mundo": MatchupInfo(
        difficulty="Easy",
        keystones=("Grasp-1", "Conqueror", "Comet"),
        item_category="liandry_shred",
        tags=("vs_tank", "free_lane", "anti_hp_stack"),
        advice="He can't kill you. Dodge Q cleavers. Liandry's burn shreds his HP stacking. Split push wins.",
    ),
    "Fiora": MatchupInfo(
        difficulty="HARD",
        keystones=("Grasp-1", "Conqueror"),
        item_category="iceborn_cleaver",
        tags=("vs_fighter", "vs_true_damage"),
        advice="Can't outtrade her easily. Q her every time she goes for a vital, don't go for Graves. Just Q her till she stops, back off when she uses W - if your wall shoves her during parry it stuns you. Grasp + Iceborn.",
    ),
    "Gangplank": MatchupInfo(
        difficulty="Easy",
        keystones=("Grasp-1", "Conqueror", "Comet"),
        item_category="sundered_sky",
        tags=("vs_ranged_poke", "push_lane"),
        advice="Sundered Sky rush. He's squishy — land E and all-in. His W cleanses slow but not W wall.",
    ),
    "Garen": MatchupInfo(
        difficulty="Easy",
        keystones=("Conqueror", "Comet"),
        item_category="default",
        tags=("vs_fighter", "vs_sustain"),
        advice="W him when he runs at you with Q. E+ghouls deny his passive regen. Avoid R execute at low HP.",
    ),
    "Gnar": MatchupInfo(
        difficulty="Advanced",
        keystones=("Comet", "Aery", "Phase Rush"),
        item_category="eclipse_poke",
        tags=("vs_ranged", "e_max"),
        shard_override="MS",
        advice="E max with Eclipse. Back off near Mega form. W him in Mini to force all-in. Phase Rush escapes Mega.",
    ),
    "Gragas": MatchupInfo(
        difficulty="Advanced",
        keystones=("Grasp-2",),
        item_category="sundered_sky",
        tags=("vs_ap", "vs_fighter"),
        advice="Sundered Sky rush + Second Wind. His body slam goes through W. Grasp-2 with Manaflow and Scorch.",
    ),
    "Gwen": MatchupInfo(
        difficulty="HARD",
        keystones=("Comet", "Aery", "Conqueror", "Phase Rush"),
        item_category="default",
        tags=("vs_fighter", "vs_true_damage", "vs_ap"),
        shard_override="AF",
        advice="Her W zone makes ghouls useless inside it. Poke with E from outside W. Phase Rush gives slow resistance vs her ult/Rylai's — 'managed to just survive the matchup or beat her many times'. Conqueror for extended trades if she W's early.",
    ),
    "Heimerdinger": MatchupInfo(
        difficulty="Advanced",
        keystones=("Comet", "Aery"),
        item_category="default",
        tags=("vs_ranged", "vs_ap", "vs_zone_control"),
        advice="Turrets zone you hard. Ghouls die to turrets. Farm safely, build MR. He's immobile — call for ganks.",
    ),
    "Illaoi": MatchupInfo(
        difficulty="Medium",
        keystones=("Conqueror", "Comet", "Aery"),
        item_category="default",
        tags=("vs_fighter",),
        advice="DODGE HER E. If she pulls your spirit, walk away. NEVER fight in her R — walk out and re-engage.",
    ),
    "Irelia": MatchupInfo(
        difficulty="EXTREME",
        keystones=("Grasp-1", "Conqueror", "Hail of Blades"),
        item_category="vs_irelia",
        tags=("vs_fighter", "vs_dash"),
        exhaust_viable=True,
        summoner_spells="Exhaust/TP",
        special_note="BAN HER",
        advice="BAN HER. Irelia's Q counts as auto, one-shots Ghouls, stacks passive -> you auto-lose. If not banned: Exhaust + Grasp, Sheen rush into anti-heal (Bramble/Executioner's early), then Iceborn or Triforce into Titanic + Frozen Heart.",
    ),
    "Jax": MatchupInfo(
        difficulty="EXTREME",
        keystones=("Grasp-1", "Comet", "Aery"),
        item_category="vs_jax_iceborn",
        tags=("vs_fighter",),
        shard_override="MS",
        exhaust_viable=True,
        advice="Dodges all our DMG but E. Dashes over wall, out-duels. ALWAYS Grasp + MS shard + Sheen rush into Iceborn. Bait his jump, W him, trade, back off, repeat till he dies. Aery + Bramble trick viable.",
    ),
    "Jayce": MatchupInfo(
        difficulty="Medium",
        keystones=("Comet", "Grasp-1", "Aery", "Conqueror"),
        item_category="sundered_sky",
        tags=("vs_ranged", "vs_poke"),
        advice="Sundered Sky rush + Second Wind. He falls off hard after 15 mins. W him in melee form.",
    ),
    "K'Sante": MatchupInfo(
        difficulty="HARD",
        keystones=("First Strike", "Comet", "Conqueror"),
        item_category="default",
        tags=("vs_tank", "vs_fighter"),
        advice="First Strike for gold gen. W him when he dashes. His All Out (R) makes him squishy — all-in window.",
    ),
    "Kayle": MatchupInfo(
        difficulty="Easy",
        keystones=("Comet", "Aery"),
        item_category="eclipse_poke",
        tags=("vs_ranged", "e_max"),
        shard_override="AF",
        advice="ABUSE HER EARLY. Melee until 6, weak until 11. E max Eclipse. Zone her off CS. End before 16.",
    ),
    "Kennen": MatchupInfo(
        difficulty="Easy",
        keystones=("Comet", "Aery"),
        item_category="vs_ranged",
        tags=("vs_ranged", "vs_ap"),
        advice="Ranged stun + disengage. E max + Comet/Aery. D. Shield start. Don't stack near ghouls (his ult AoE). W him when he E's in for stun.",
    ),
    "Kled": MatchupInfo(
        difficulty="HARD",
        keystones=("Grasp-1", "Comet"),
        item_category="iceborn_cleaver",
        tags=("vs_fighter", "vs_all_in"),
        advice="Iceborn rush. W him when he dismounts to deny remount. Ghouls body-block his Q.",
    ),
    "Malphite": MatchupInfo(
        difficulty="Medium",
        keystones=("Grasp-1", "Comet"),
        item_category="default",
        tags=("vs_tank", "push_lane"),
        advice="He pokes with Q but runs out of mana. BC shreds his armor. Push and split.",
    ),
    "Maokai": MatchupInfo(
        difficulty="Easy",
        keystones=("Conqueror", "First Strike"),
        item_category="liandry_shred",
        tags=("vs_tank", "push_lane"),
        advice="Tiny threat. He can't match your splitpush at any stage.",
    ),
    "Mordekaiser": MatchupInfo(
        difficulty="HARD",
        keystones=("Phase Rush", "Conqueror", "First Strike"),
        item_category="vs_morde",
        tags=("vs_ap", "vs_fighter"),
        advice="CRITICAL: His R steals Maiden. Phase Rush escapes Rylai's. Ghouls DON'T follow into Death Realm. Maiden DOES.",
    ),
    "Naafiri": MatchupInfo(
        difficulty="Medium",
        keystones=("Grasp-2", "Grasp-3", "Aery"),
        item_category="default",
        tags=("vs_assassin", "vs_ad"),
        advice="Her dogs die to ghouls. W her when she dashes in. Grasp for short trades. Outscale hard.",
    ),
    "Nasus": MatchupInfo(
        difficulty="Easy",
        keystones=("Conqueror", "Phase Rush"),
        item_category="default",
        tags=("vs_tank", "deny_stacks"),
        shard_override="AF",
        advice="Punish early. WARNING: ghouls give him free Q stacks. Freeze when possible. Phase Rush kites his wither.",
    ),
    "Nocturne": MatchupInfo(
        difficulty="HARD",
        keystones=("Grasp-1", "Conqueror", "Hail of Blades"),
        item_category="default",
        tags=("vs_fighter", "vs_dash"),
        advice="Bait his spell shield before E. His R denies vision. Wall him after he dashes in.",
    ),
    "Olaf": MatchupInfo(
        difficulty="HARD",
        keystones=("Grasp-1", "Conqueror"),
        item_category="default",
        tags=("vs_fighter", "vs_lane_bully"),
        advice="He runs you down early. Don't fight 1-5. His R = unstoppable (W doesn't trap). Farm safe, outscale.",
    ),
    "Ornn": MatchupInfo(
        difficulty="HARD",
        keystones=("First Strike", "Comet"),
        item_category="liandry_shred",
        tags=("vs_tank", "vs_cc"),
        advice="First Strike for gold gen. Dodge his E and R. Push and split but respect his CC chain.",
    ),
    "Pantheon": MatchupInfo(
        difficulty="Medium",
        keystones=("Comet", "Conqueror"),
        item_category="default",
        tags=("vs_fighter", "vs_lane_bully"),
        advice="Empowered W stun into Q chunks hard. Bone Plating helps. He falls off after 15 mins. Survive and outscale.",
    ),
    "Poppy": MatchupInfo(
        difficulty="Medium",
        keystones=("Grasp-1", "Conqueror"),
        item_category="default",
        tags=("vs_tank",),
        advice="Her W blocks dashes but you don't dash. Don't fight near walls (E stun). Out-split her.",
    ),
    "Quinn": MatchupInfo(
        difficulty="Medium",
        keystones=("Aery", "Comet"),
        item_category="eclipse_poke",
        tags=("vs_ranged", "vs_adc_top", "e_max"),
        advice="E max with Eclipse. W her when she vaults in. You outscale massively. Bramble+Aery trick.",
    ),
    "Renekton": MatchupInfo(
        difficulty="HARD",
        keystones=("Grasp-2", "Grasp-3", "Conqueror"),
        item_category="iceborn_cleaver",
        tags=("vs_fighter", "vs_lane_bully"),
        exhaust_viable=True,
        advice="Lane Bully, dashes over wall, heals off your pets, double dashes so you can't catch him. You outscale but he snowballs harder. Be careful early, give up CS if needed. Exhaust + Unflinching. Iceborn rush.",
    ),
    "Riven": MatchupInfo(
        difficulty="HARD",
        keystones=("Grasp-1", "Grasp-2", "Comet"),
        item_category="iceborn_cleaver",
        tags=("vs_fighter", "vs_dash", "vs_all_in"),
        exhaust_viable=True,
        advice="Iceborn rush. She dashes through W but armor + slow help. Bone Plating blocks her combo. HoB viable.",
    ),
    "Rumble": MatchupInfo(
        difficulty="Medium",
        keystones=("Comet", "Aery", "Conqueror"),
        item_category="default",
        tags=("vs_ap", "vs_zone_control"),
        advice="His flamespitter melts ghouls. Don't stack ghouls in Q range. MR important. W him — he's immobile.",
    ),
    "Ryze": MatchupInfo(
        difficulty="Advanced",
        keystones=("Conqueror", "Grasp-4"),
        item_category="default",
        tags=("vs_ap", "vs_ranged"),
        advice="He combos hard but is squishy. Land E and all-in. W him — no escape. Grasp-4 Approach Velocity to chase.",
    ),
    "Sejuani": MatchupInfo(
        difficulty="Medium",
        keystones=("Grasp-1", "Grasp-3", "Conqueror"),
        item_category="default",
        tags=("vs_tank", "vs_cc"),
        advice="Good CC but low damage. Push and take plates. Out-split all game. Respect CC chain for ganks.",
    ),
    "Sett": MatchupInfo(
        difficulty="EXTREME",
        keystones=("Grasp-1",),
        item_category="titanic_breaker",
        tags=("vs_fighter",),
        advice="Dodge W true damage center. Bone Plating + Unflinching mandatory. W him during E pull. Tiamat → Titanic.",
    ),
    "Shen": MatchupInfo(
        difficulty="Medium",
        keystones=("Conqueror", "Comet", "Aery"),
        item_category="default",
        tags=("vs_tank", "punish_ult"),
        advice="Push when he ults away — free plates. His W blocks auto attacks including ghouls. Out-split him.",
    ),
    "Singed": MatchupInfo(
        difficulty="Easy",
        keystones=("Grasp-1", "Conqueror"),
        item_category="default",
        tags=("vs_ap",),
        advice="DO NOT CHASE. W him when he runs in to fling. Push and take plates while he proxies.",
    ),
    "Sion": MatchupInfo(
        difficulty="Medium",
        keystones=("Grasp-1", "Conqueror", "First Strike"),
        item_category="liandry_shred",
        tags=("vs_tank", "anti_hp_stack"),
        advice="Dodge Q charge. W him during Q channel to cancel. HP stacker — Liandry's shreds him.",
    ),
    "Skarner": MatchupInfo(
        difficulty="Easy",
        keystones=("Grasp-1", "Conqueror", "Comet"),
        item_category="default",
        tags=("vs_tank", "vs_cc"),
        advice="He's tanky but you outscale. Don't get dragged by R. W him to kite. Free lane.",
    ),
    "Smolder": MatchupInfo(
        difficulty="Advanced",
        keystones=("Comet", "Aery"),
        item_category="vs_ranged",
        tags=("vs_ranged", "vs_scaling"),
        advice="He scales hard - punish early before stacks. E max + Comet/Aery poke. D. Shield start. He's squishy early, all-in with ghouls + Maiden post-6.",
    ),
    "Swain": MatchupInfo(
        difficulty="Easy",
        keystones=("Aery", "Comet", "Conqueror"),
        item_category="default",
        tags=("vs_ap", "vs_ranged"),
        advice="Dodge E root. Build MR. Push hard — poor waveclear early. W him to deny escape.",
    ),
    "Sylas": MatchupInfo(
        difficulty="Medium",
        keystones=("Grasp-2", "Grasp-3", "Conqueror", "Comet"),
        item_category="default",
        tags=("vs_ap", "vs_fighter"),
        advice="He steals R but Maiden isn't scary for him. Grasp for short trades. Push and take plates.",
    ),
    "Tahm Kench": MatchupInfo(
        difficulty="Medium",
        keystones=("Conqueror", "First Strike"),
        item_category="default",
        tags=("vs_tank", "vs_sustain"),
        advice="He's tanky with grey health but can't kill you. Don't get hit by Q tongue 3 times. Push freely.",
    ),
    "Teemo": MatchupInfo(
        difficulty="Medium",
        keystones=("Aery", "Comet"),
        item_category="eclipse_poke",
        tags=("vs_ranged", "vs_ap", "vs_blind", "e_max"),
        advice="E max Eclipse. His blind stops ghoul autos. Tiamat bypasses blind for Aery. Bramble+Aery trick. Buy Sweeper.",
    ),
    "Trundle": MatchupInfo(
        difficulty="EXTREME",
        keystones=("Conqueror", "Phase Rush"),
        item_category="vs_trundle",
        tags=("vs_fighter", "vs_stat_steal"),
        shard_override="MS",
        advice="His R steals your stats. Conqueror + MS shard. Tiamat rush for waveclear, then BC for shred. Buy Executioner's if he finishes Ravenous Hydra. Phase Rush viable if he builds Rylai's.",
    ),
    "Tryndamere": MatchupInfo(
        difficulty="EXTREME",
        keystones=("Grasp-2", "Grasp-1", "Grasp-3", "Conqueror", "Phase Rush"),
        item_category="vs_trynd_conq",
        tags=("vs_fighter", "vs_crit", "vs_split"),
        shard_override="MS",
        exhaust_viable=True,
        summoner_spells="Exhaust/TP",
        advice="Won't die, dashes over wall, out-DPS/outtrades you. Take Conqueror + Exhaust. Rush Tabis + HP item. If losing early finish Titanic first, then BC + armor (Randuin's/DMP). Phase Rush viable to escape his W slow.",
    ),
    "Udyr": MatchupInfo(
        difficulty="Medium",
        keystones=("Conqueror", "Grasp-3"),
        item_category="default",
        tags=("vs_fighter", "vs_sustain"),
        advice="He runs fast with bear stance. W him to kite. Can't match your push. Out-split him.",
    ),
    "Urgot": MatchupInfo(
        difficulty="HARD",
        keystones=("Conqueror", "Comet", "Aery"),
        item_category="default",
        tags=("vs_fighter", "vs_ranged"),
        advice="Don't stand in W range. W him when he E dashes in. Track passive leg cooldowns. Don't get R executed at 25%.",
    ),
    "Varus": MatchupInfo(
        difficulty="EXTREME",
        keystones=("Comet", "Conqueror"),
        item_category="default",
        tags=("vs_ranged", "vs_poke"),
        advice="Brutal poke lane. Second Wind + Doran's Shield. Farm under tower. Call for ganks — no escape.",
    ),
    "Vayne": MatchupInfo(
        difficulty="Advanced",
        keystones=("Comet", "Aery"),
        item_category="vs_ranged",
        tags=("vs_ranged", "vs_adc_top", "vs_true_damage"),
        shard_override="AF",
        advice="Ranged + %HP true damage. Adaptive shard (HP helps her deal MORE damage). D. Shield + Second Wind. Bramble Vest + Aery trick. E max with Comet/Aery. Outscale at 2 items.",
    ),
    "Vladimir": MatchupInfo(
        difficulty="Easy",
        keystones=("Conqueror", "Comet", "Aery"),
        item_category="default",
        tags=("vs_ap", "vs_sustain"),
        advice="His pool dodges everything. Don't waste W when pool is up. Punish early when CDs are long. Build MR.",
    ),
    "Volibear": MatchupInfo(
        difficulty="EXTREME",
        keystones=("Grasp-2", "Conqueror"),
        item_category="default",
        tags=("vs_fighter", "vs_all_in"),
        advice="Wins early all-ins. Don't fight 1-3. His R disables tower. Grasp-2 with Unflinching. Post-6 with Maiden can match.",
    ),
    "Warwick": MatchupInfo(
        difficulty="EXTREME",
        keystones=("Comet", "Conqueror"),
        item_category="default",
        tags=("vs_fighter", "vs_sustain"),
        advice="He heals a lot below 50% — need anti-heal or burst. His R suppresses. W him when he Qs onto you. Comet poke to whittle.",
    ),
    "Wukong": MatchupInfo(
        difficulty="HARD",
        keystones=("Comet", "Grasp-2"),
        item_category="default",
        tags=("vs_fighter", "vs_clone"),
        advice="Clone can bait W. Don't W until you confirm it's real. His R knockup — W to cancel R spin.",
    ),
    "Yasuo": MatchupInfo(
        difficulty="HARD",
        keystones=("Grasp-1",),
        item_category="iceborn_cleaver",
        tags=("vs_fighter", "vs_dash", "vs_windwall"),
        shard_override="MS",
        advice="Iceborn rush — slow field key since he dashes through ghouls. Windwall blocks E. Steelcaps reduce damage a lot.",
    ),
    "Yone": MatchupInfo(
        difficulty="EXTREME",
        keystones=("Conqueror", "Comet"),
        item_category="titanic_breaker",
        tags=("vs_fighter", "vs_dash"),
        shard_override="MS",
        exhaust_viable=True,
        advice="W where he'll snap back from E. Conqueror + MS shard. Tiamat → Titanic. Ghouls body-block his R.",
    ),
    "Yorick": MatchupInfo(
        difficulty="Easy",
        keystones=("Conqueror", "Grasp-1"),
        item_category="default",
        tags=("vs_fighter",),
        advice="Mirror match — whoever lands E with more ghouls wins. W enemy Maiden to deny it.",
    ),
    "Zaahen": MatchupInfo(
        difficulty="Medium",
        keystones=("Comet", "Conqueror"),
        item_category="default",
        tags=("vs_fighter",),
        shard_override="MS",
        advice="Comet poke is strong. MS shard helps with his mobility. Push and split.",
    ),
    "Zac": MatchupInfo(
        difficulty="Medium",
        keystones=("Conqueror", "Grasp-1"),
        item_category="default",
        tags=("vs_tank", "vs_cc"),
        advice="He's tanky with good CC. Stand on blobs to deny healing. Push and split. Respect engage for ganks.",
    ),
}


# ============================================================================
# ARCHETYPE FALLBACKS — for champions not in the table
# ============================================================================

ARCHETYPE_CHAMPIONS: dict[str, list[str]] = {
    "ad_fighter": [
        "Aatrox", "Ambessa", "Camille", "Darius", "Fiora", "Garen", "Illaoi",
        "Irelia", "Jax", "Briar", "Kled", "Nocturne", "Olaf", "Pantheon",
        "Renekton", "Riven", "Sett", "Trundle", "Tryndamere", "Udyr",
        "Warwick", "Wukong", "Yasuo", "Yone", "Yorick", "Zaahen",
    ],
    "ad_ap_poke": ["Gangplank", "Gragas", "Jayce", "Naafiri", "Urgot"],
    "ranged_battle_mage": [
        "Akali", "Anivia", "Aurelion Sol", "Aurora", "Cassiopeia",
        "Heimerdinger", "Rumble", "Ryze", "Singed", "Swain", "Sylas", "Vladimir",
    ],
    "ranged": [
        "Akshan", "Gnar", "Kayle", "Kennen", "Quinn", "Smolder",
        "Teemo", "Vayne", "Varus",
    ],
    "hp_tank": ["Cho'Gath", "Dr. Mundo", "Maokai", "Nasus", "Sion", "Tahm Kench", "Zac"],
    "ap_ad_tank": [
        "Diana", "Gwen", "K'Sante", "Malphite", "Mordekaiser", "Ornn",
        "Poppy", "Sejuani", "Shen", "Skarner", "Volibear",
    ],
}

ARCHETYPE_DEFAULTS: dict[str, MatchupInfo] = {
    "ad_fighter": MatchupInfo(
        difficulty="Medium",
        keystones=("Grasp-1", "Conqueror"),
        item_category="default",
        tags=("vs_fighter",),
        advice="AD fighter — Grasp for short trades, Conqueror for extended. Cloth + Refill start.",
    ),
    "ad_ap_poke": MatchupInfo(
        difficulty="Medium",
        keystones=("Comet", "Grasp-1"),
        item_category="sundered_sky",
        tags=("vs_poke",),
        advice="Poke champion — Sundered Sky rush + Second Wind. Survive lane and outscale.",
    ),
    "ranged_battle_mage": MatchupInfo(
        difficulty="Advanced",
        keystones=("Comet", "Aery", "Conqueror"),
        item_category="default",
        tags=("vs_ap", "vs_ranged"),
        advice="Ranged/battle mage — E max, Eclipse poke build. Build MR. Outscale in split.",
    ),
    "ranged": MatchupInfo(
        difficulty="Advanced",
        keystones=("Aery", "Comet"),
        item_category="eclipse_poke",
        tags=("vs_ranged", "e_max"),
        advice="Ranged top — Aery + Bramble Vest trick. E max, Eclipse build. D Shield start. Outscale.",
    ),
    "hp_tank": MatchupInfo(
        difficulty="Easy",
        keystones=("Conqueror", "First Strike"),
        item_category="liandry_shred",
        tags=("vs_tank",),
        advice="HP tank — Conqueror for stacking, Liandry's for %HP burn. Free lane, push and split.",
    ),
    "ap_ad_tank": MatchupInfo(
        difficulty="Medium",
        keystones=("Grasp-1", "Conqueror", "Comet"),
        item_category="default",
        tags=("vs_tank",),
        advice="AP/AD tank — Grasp or Conqueror. Push and take plates. Out-split them.",
    ),
}


def get_matchup(enemy: str) -> MatchupInfo:
    """Look up matchup info, falling back to archetype if not found."""
    # Exact match
    if enemy in MATCHUP_TABLE:
        return MATCHUP_TABLE[enemy]

    # Case-insensitive match
    enemy_lower = enemy.lower().strip()
    for name, info in MATCHUP_TABLE.items():
        if name.lower() == enemy_lower:
            return info

    # Archetype fallback
    for archetype, champs in ARCHETYPE_CHAMPIONS.items():
        if enemy in champs or enemy_lower in [c.lower() for c in champs]:
            return ARCHETYPE_DEFAULTS[archetype]

    # Ultimate fallback
    return ARCHETYPE_DEFAULTS["ad_fighter"]


def get_all_matchup_enemies() -> list[str]:
    """Return sorted list of all enemies in the matchup table."""
    return sorted(MATCHUP_TABLE.keys())
