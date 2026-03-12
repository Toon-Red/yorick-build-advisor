# Yorick Decision Tree — Full Specification

## INPUT
```
enemy: str  (enemy champion name)
```

## OUTPUTS (per build option)
```
1. keystone         — Rune page template name (e.g. "Grasp-1", "Comet")
2. resolve_code     — A, B, or C (which resolve runes to adapt)
3. shards           — (shard1, shard2, shard3) tuple of IDs
4. summoners        — "Ghost/Ignite", "Exhaust/TP", etc.
5. starter          — Starting item recommendation
6. item_build       — Item build template name
7. reasoning        — Matchup advice text
```

---

## DECISION 1: KEYSTONE SELECTION

**Source**: PDF Matchup Sheet (pages 84-91) — DEFINITIVE, listed left-to-right = most viable first.

The PDF explicitly assigns keystones per matchup. This is a LOOKUP, not a decision.

| Enemy | PDF Says | Reasoning |
|-------|----------|-----------|
| Aatrox | Conqueror / Comet | Extended fights, sustain-heavy |
| Akali | Comet / Aery | E max ranged poke, she's mobile |
| Ambessa | Aery / Conqueror | Short trades with Aery poke |
| Anivia | Comet / Aery / Phase Rush | Zone control, need poke/escape |
| Aurelion Sol | Aery / Comet | Poke down, he's immobile |
| Aurora | Comet / Aery | E max Eclipse poke |
| Camille | Comet / Aery, Conqueror | Poke her, or extended trades |
| Cassiopeia | Aery / Conqueror | Close-range DPS, Aery procs often |
| Cho'Gath | Conqueror / Hail of Blades | HP tank, need sustained/burst DPS |
| Darius | Comet / Conqueror | Poke him, MS shard to kite |
| Dr. Mundo | Grasp-1 / Conqueror / Comet | Free lane, any works |
| Fiora | Grasp-1 / Conqueror | Short trades with Grasp, Iceborn |
| Gangplank | Grasp-1 / Conqueror / Comet | Free lane, Sundered Sky rush |
| Garen | Conqueror / Comet | Extended trades or poke |
| Gnar | Comet / Aery / Phase Rush | Ranged, E max Eclipse |
| Gragas | Grasp-2 (Sorcery) | Poke with Scorch, Sundered Sky |
| Gwen | Comet / Aery / Conqueror | Poke outside W zone. Phase Rush viable (video: "managed to survive or beat her many times") |
| Heimerdinger | Comet / Aery | Turrets zone, need poke |
| Illaoi | Conqueror / Comet / Aery | Dodge E, extended fight |
| Irelia | Grasp-1 / Conqueror / HoB | BAN HER. Q one-shots ghouls |
| Jax | Grasp / Comet / Aery | Must Grasp + Iceborn. Comet/Aery for poke lane |
| Jayce | Comet / Grasp-1 / Aery / Conqueror | Sundered Sky rush |
| K'Sante | First Strike / Comet / Conqueror | Gold gen, he's tanky |
| Kayle | Comet / Aery | Abuse early, E max Eclipse |
| Kennen | Comet / Aery | Ranged AP, poke build |
| Kled | Grasp / Comet | Iceborn rush, W dismount |
| Malphite | Grasp / Comet | Push and split, AP tank |
| Mordekaiser | Phase Rush / Conqueror / First Strike | CRITICAL: Phase Rush escapes Rylai's. His R steals Maiden |
| Naafiri | Grasp-2 or 3 / Aery | Dogs die to ghouls, short trades |
| Nasus | Conqueror / Phase Rush | Punish early, Phase Rush kites wither |
| Olaf | Grasp / Conqueror | He runs you down, need Grasp sustain |
| Ornn | First Strike / Comet | Gold gen, tank shred |
| Pantheon | Comet / Conqueror | Poke, he falls off |
| Poppy | Grasp-1 / Conqueror | Her W irrelevant, out-split |
| Quinn | Aery / Comet | Ranged, Bramble+Aery trick |
| Renekton | Grasp-2/3 / Conqueror | Lane bully, need poke Grasp |
| Riven | Grasp-1 or 2 / Comet | Iceborn rush, BonePlating |
| Rumble | Comet / Aery / Conqueror | AP poke, melts ghouls |
| Ryze | Conqueror / Grasp-4 | Chase with Approach Velocity |
| Sejuani | Grasp-1/3 / Conqueror | Tank, push and split |
| Sett | Grasp-1 (BonePlating + Unflinching) | EXTREME, dodge W center |
| Shen | Conqueror / Comet / Aery | Push when he ults away |
| Singed | Grasp-1 / Conqueror | Don't chase, push |
| Sion | Grasp / Conqueror / First Strike | HP tank, Liandry's |
| Smolder | Comet / Aery | Ranged, punish early |
| Swain | Aery / Comet / Conqueror | Dodge E, push hard |
| Sylas | Grasp-2/3 / Conqueror / Comet | Short trades, he steals R |
| Tahm Kench | Conqueror / First Strike | Tank, sustained fight |
| Teemo | Aery / Comet | Bramble+Aery trick, E max |
| Trundle | Conqueror / Phase Rush | His R steals stats, MS shard |
| Tryndamere | Grasp-2/1/3 / Conqueror (Exhaust + MS) | Won't die, Exhaust mandatory |
| Udyr | Conqueror / Grasp-3 | Sustain Grasp, kite |
| Urgot | Conqueror / Comet / Aery | Track passive legs |
| Varus | Comet / Conqueror | Brutal poke, farm under tower |
| Vayne | Comet / Aery | Ranged %HP, Adaptive shard |
| Vladimir | Conqueror / Comet / Aery | Punish early, build MR |
| Volibear | Grasp-2 + SecondWind & Unflinching / Conqueror | EXTREME, early all-ins |
| Warwick | Comet / Conqueror | Sustain-heavy, poke down |
| Wukong | Comet / Grasp-2 | Clone bait, poke |
| Yasuo | Grasp + B (SecondWind) + MS Shard | Iceborn rush, slow field |
| Yone | Conqueror + MS Shard / Comet | Tiamat → Titanic, MS shard |
| Yorick | Conqueror / Grasp-1 | Mirror, whoever lands E |
| Zaahen | Comet / Conqueror + MS | Poke, MS shard |
| Zac | Conqueror / Grasp | Tank, push and split |

### Archetype Fallbacks (champion not in table)
| Archetype | Keystones |
|-----------|-----------|
| AD Fighter | Conqueror / Grasp |
| AD/AP Poke | Comet / Grasp |
| Ranged/Battle Mage | Conqueror / Aery / Comet |
| Ranged | Aery / Comet |
| HP Tank | Conqueror / Grasp |
| AP/AD Tank | Grasp / Comet / Conqueror |

---

## DECISION 2: RESOLVE ADAPTATION (A/B/C)

**Source**: PDF pages 59-67, Video 3:37-22:44

### The System
When Resolve is **primary** (Grasp pages): 2 rune slots adapt (Demolish always taken as row 1)
When Resolve is **secondary** (all others): 1 rune slot adapts (Demolish always taken)

### IF tree for Resolve Primary (Grasp-1, Grasp-2, Grasp-3, Grasp-4):
```
IF keystone starts with "Grasp":
    IF enemy has specific override (e.g. Volibear):
        → Use override (Volibear = SecondWind + Unflinching = "B+C")
    ELIF enemy IN RANGED_POKE_CHAMPS:
        → B1: SecondWind + Revitalize
        WHY: "second wind is usually used against ranged or constant poke" (video 6:08)
        WHO: Teemo, Quinn, Vayne, Kennen, Kayle, Smolder, Gnar, Jayce, Gangplank,
             Heimerdinger, Rumble, Malphite, Yone, Yasuo, Fiora, Varus, Akshan,
             Aurora, Aurelion Sol, Cassiopeia, Ryze, Swain
    ELIF enemy IN BURST_CC_CHAMPS:
        → C1: BonePlating + Unflinching
        WHY: "unflinching is usually combined with bone plating... fighting somebody very scary" (video 4:24)
             "broken against burst only champs with low DPS during trades" (PDF p65)
        WHO: Riven, Renekton, Jax, Volibear, Pantheon, Sett, Urgot, Kled, Nocturne, Wukong
    ELSE:
        → A1: BonePlating + Revitalize (DEFAULT)
        WHY: "by default bone plating and revitalize" (video 20:57)
```

### IF tree for Resolve Secondary (Conqueror, Comet, Aery, Phase Rush, etc.):
```
IF keystone does NOT start with "Grasp":
    IF enemy IN RANGED_POKE_CHAMPS:
        → B2: Demolish + SecondWind
        WHY: "second option against range poke, we take second wind" (video 19:48)
    ELIF enemy IN BURST_CHAMPS:
        → C2: Demolish + BonePlating
        WHY: "hard matchups or burst, we take bone plating" (video 19:57)
        WHO: Riven, Renekton, Jax, Kled, Nocturne, Wukong, Ambessa, Sett
    ELSE:
        → A2: Demolish + Revitalize (DEFAULT)
        WHY: "by default, revitalize because it's always good" (video 20:02)
```

### Special Override
```
Volibear: Always SecondWind + Unflinching regardless of keystone type
    WHY: PDF says "Grasp-2 + Second Wind & Unflinching"
         Video: "Volar cuz he stuns you" + "Volibar with his lightning passive"
         He has BOTH poke (passive lightning = SecondWind) AND burst/CC (stun = Unflinching)
```

---

## DECISION 3: SHARD SELECTION

**Source**: PDF pages 63-64, Video 6:20-8:10

### Default: Attack Speed / HP / Tenacity
```
shard1 = ALWAYS Attack Speed
    WHY: "we take attack speed just to help us CS and have built-in AS" (video 8:34)

shard2 = VARIES:
    IF enemy IN MS_SHARD_CHAMPS:
        → Movement Speed
        WHY: "Jax, Trinamer, Yon, Yasuo, Zahan, and Trundle... they all tend to have 350 MS"
             "you can close that gap by giving yourself movement speed shard" (video 6:51)
        WHO: Jax, Tryndamere, Yone, Yasuo, Trundle, Zaahen, Darius
    ELIF enemy IN ADAPTIVE_SHARD_CHAMPS:
        → Adaptive Force
        WHY: "fighting full damage characters that taking HP will just make them deal more damage"
             "like a Vayne or a Gwen, or fighting somebody squishy you can confidently beat" (video 7:37)
        WHO: Vayne, Gwen, Kayle, Nasus
    ELSE:
        → HP (DEFAULT)
        WHY: "our pets scale with HP and our Q also scales with HP" (video 8:43)

shard3 = USUALLY Tenacity
    WHY: "Yorick is already very slow, no dashes and most enemies will have CC" (video 8:46)
    RARE EXCEPTION: Double HP when going Titanic + HP-heavy build (HoB pages have HP/HP)
```

---

## DECISION 4: SUMMONER SPELLS

**Source**: PDF pages 51-58, Video 0:16-3:15

```
IF enemy == "Tryndamere":
    → Exhaust/TP
    WHY: "I only really take exhaust when I'm fighting somebody like Trinameir" (video 2:26)
         PDF: "Anti-Burst (Cuck Tryndamere)" (p55)

ELIF enemy IN {"Riven", "Renekton"}:
    → Exhaust/Ghost
    WHY: "burst matchups. Renekton, Riven and Trinameir" (video 3:00)
         "into Riven as well. It's very nice" (video 2:42)

ELIF enemy IN {"Yasuo", "Yone", "Jax", "Irelia", "Rengar"}:
    → "Exhaust viable (Ghost/Ignite default)"
    WHY: "into Jax as well, though you don't have to always take it"
         "also very viable into Yon or Yaso type of attack speed based characters" (video 2:44)

ELIF matchup has specific summoner override (e.g. Irelia = Exhaust/TP):
    → Use the override

ELSE:
    → Ghost/Ignite (DEFAULT)
    WHY: "by default is I take ghosts and ignite into almost everybody" (video 2:08)
```

---

## DECISION 5: STARTER ITEMS

**Source**: PDF page 40

```
IF enemy IN BAD_AD_MATCHUPS {Riven, Jax, Renekton, Kled, Sett, Tryndamere, Irelia}:
    → Cloth Armor + Refillable
    WHY: "Bad AD Matchup - Armor Cloth & Refillable" (PDF p40)

ELIF enemy IN AP_MELEE_CHAMPS {Gwen, Mordekaiser, Sylas}:
    → Long Sword + Refillable
    WHY: "AP Matchup - Long sword & Refill pot... rush magic mantle next recall" (PDF p40)

ELIF enemy IN AP_POKE_CHAMPS {Teemo, Gragas, Volibear, Rumble, Heimerdinger}:
    → Doran's Shield
    WHY: "AP poke matchup - Doran's Shield & pot into Magic Mantle" (PDF p40)

ELIF enemy IN RANGED_AD_CHAMPS {Vayne, Quinn, Smolder, Kennen, Kayle, Akshan}:
    → Doran's Shield
    WHY: Ranged AD — need sustain, Bramble Vest rush with Aery trick

ELIF enemy IN RANGED_AP_CHAMPS {Aurora, Akali, Cassiopeia, Ryze, Anivia, Swain}:
    → Doran's Shield
    WHY: "E max with Eclipse & Shojin + Comet/Aery for poke"

ELIF enemy IN AD_TANK_AGGRO {Shen, Sion}:
    → Cloth Armor + Refillable
    WHY: "AD Tank with Aggro - Armor Cloth into Black Cleaver" (PDF p40)

ELIF enemy IN AP_TANK_CHAMPS {Malphite, Ornn, Cho'Gath}:
    → Doran's Shield
    WHY: "AP Tank - Doran's Shield into Cull and Black Cleaver" (PDF p40)

ELSE:
    → Doran's Blade + Health Potion (DEFAULT)
    WHY: Standard start for most matchups
```

---

## DECISION 6: ITEM BUILD PATH

**Source**: PDF builds section, Mobafire item pages, matchup-specific builds

```
IF matchup has specific item_category override:
    → Use the mapped build (vs_jax_iceborn → "VS Jax (Iceborn)", etc.)

ELIF enemy IN SHEEN_ICEBORN_CHAMPS {Jax, Fiora, Renekton, Kled, Yasuo, Riven, Irelia}:
    → "Iceborn Cleaver"
    WHY: "Gauntlet into Cleaver, can work into most AD counters like Jax, Ren, Kled" (mobafire)
         Slow field + armor against auto-attack fighters

ELIF enemy IN TIAMAT_TITANIC_CHAMPS {Tryndamere, Trundle, Sett, Yone}:
    → "Titanic Breaker"
    WHY: "Good into Non HP/Tank Killers... champs that need to snowball" (mobafire)
         Need waveclear + HP stacking against stat-check fighters

ELIF enemy IN ECLIPSE_POKE_CHAMPS {Teemo, Aurora, Akali, Kayle, Gnar, Quinn, Akshan}:
    → "Eclipse Poke"
    WHY: "E max into Eclipse & Shojin with Comet or Aery" (mobafire)
         Ranged matchups where you max E and poke

ELIF enemy IN SUNDERED_SKY_CHAMPS {Jayce, Gragas, Gangplank}:
    → "Sundered Sky Rush"
    WHY: "Go Sky first if Hard Matchup" (mobafire)
         Sustain through poke with Sky healing

ELIF enemy IN LIANDRY_SHRED_CHAMPS {Cho'Gath, Dr. Mundo, Sion, Tahm Kench, Ornn, Maokai}:
    → "Liandry Tank Shred"
    WHY: "Beats any Tank... good into Cho'Gath, Tahmkench, Ornn, Mundo, Nasus" (mobafire)
         %HP burn shreds HP stackers

ELSE:
    → "Default BBC" (Shojin → Black Cleaver → Sundered Sky)
    WHY: "Shojin gives pets 12% DMG Amp... Black Cleaver gives Ghouls everything they scale with"
         Default build when no specific counter-build is needed
```

---

## DECISION 7: PRECISION SECONDARY ADAPTATION (Cut Down)

**Source**: PDF page 72, Video 13:08-14:26

```
IF keystone's secondary tree == Precision (only Grasp-1 has this):
    IF enemy IN HP_STACK_TANKS {Sion, Cho'Gath}:
        → Swap Legend Alacrity for Cut Down
        WHY: "into tanks Cut down is very good for shredding tanks with a lot of HP"
             "as long as the enemy is above 50% HP, you will deal bonus damage" (video 13:22)
```

---

## COMPLETE IF-STATEMENT TREE (top-to-bottom execution)

```python
def build_for_matchup(enemy):
    # ---- STEP 1: LOOKUP matchup data ----
    matchup = MATCHUP_TABLE.get(enemy) or archetype_fallback(enemy)

    # ---- For each keystone in matchup.keystones (priority order): ----
    for keystone in matchup.keystones:
        template = RUNE_PAGES[keystone]

        # ---- STEP 2: RESOLVE ADAPTATION ----
        if keystone.startswith("Grasp"):
            # Primary resolve — 2 slots adapt
            if enemy == "Volibear":
                resolve = (SECOND_WIND, UNFLINCHING)      # B+C hybrid
            elif enemy in RANGED_POKE_CHAMPS:
                resolve = (SECOND_WIND, REVITALIZE)        # B1
            elif enemy in BURST_CC_CHAMPS:
                resolve = (BONE_PLATING, UNFLINCHING)      # C1
            else:
                resolve = (BONE_PLATING, REVITALIZE)       # A1 default
        else:
            # Secondary resolve — 1 slot adapts (other is Demolish)
            if enemy in RANGED_POKE_CHAMPS:
                resolve_slot = SECOND_WIND                  # B2
            elif enemy in BURST_CHAMPS:
                resolve_slot = BONE_PLATING                 # C2
            else:
                resolve_slot = REVITALIZE                   # A2 default

        # ---- STEP 3: SHARD SELECTION ----
        shard1 = ATTACK_SPEED                              # Always
        if matchup.shard_override == "MS" or enemy in MS_SHARD_CHAMPS:
            shard2 = MOVEMENT_SPEED
        elif matchup.shard_override == "AF" or enemy in ADAPTIVE_SHARD_CHAMPS:
            shard2 = ADAPTIVE_FORCE
        else:
            shard2 = HP                                    # Default
        shard3 = TENACITY                                  # Usually (double HP rare)

        # ---- STEP 4: SUMMONER SPELLS ----
        if matchup.summoner_spells != "Ghost/Ignite":
            summs = matchup.summoner_spells                # Matchup override
        elif enemy in EXHAUST_PRIMARY:                     # {Tryndamere}
            summs = "Exhaust/TP"
        elif enemy in EXHAUST_WITH_GHOST:                  # {Riven, Renekton}
            summs = "Exhaust/Ghost"
        elif enemy in EXHAUST_SECONDARY or matchup.exhaust_viable:
            summs = "Exhaust viable (Ghost/Ignite default)"
        else:
            summs = "Ghost/Ignite"                         # Default

        # ---- STEP 5: STARTER ITEMS ----
        if enemy in BAD_AD_MATCHUPS:
            starter = "Cloth Armor + Refillable"
        elif enemy in AP_MELEE_CHAMPS:
            starter = "Long Sword + Refillable"
        elif enemy in AP_POKE_CHAMPS:
            starter = "Doran's Shield"
        elif enemy in RANGED_AD_CHAMPS:
            starter = "Doran's Shield"
        elif enemy in RANGED_AP_CHAMPS:
            starter = "Doran's Shield"
        elif enemy in AD_TANK_AGGRO:
            starter = "Cloth Armor + Refillable"
        elif enemy in AP_TANK_CHAMPS:
            starter = "Doran's Shield"
        else:
            starter = "Doran's Blade + Health Potion"      # Default

        # ---- STEP 6: ITEM BUILD PATH ----
        if matchup.item_category has specific mapping:
            item_build = CATEGORY_MAP[matchup.item_category]
        elif enemy in SHEEN_ICEBORN_CHAMPS:
            item_build = "Iceborn Cleaver"
        elif enemy in TIAMAT_TITANIC_CHAMPS:
            item_build = "Titanic Breaker"
        elif enemy in ECLIPSE_POKE_CHAMPS:
            item_build = "Eclipse Poke"
        elif enemy in SUNDERED_SKY_CHAMPS:
            item_build = "Sundered Sky Rush"
        elif enemy in LIANDRY_SHRED_CHAMPS:
            item_build = "Liandry Tank Shred"
        else:
            item_build = "Default BBC"                     # Default

        # ---- STEP 7: PRECISION SECONDARY CUT DOWN ----
        if template.sub_style_id == PRECISION and enemy in HP_STACK_TANKS:
            swap Legend Alacrity → Cut Down

        # ---- ASSEMBLE & RETURN BUILD OPTION ----
```

---

## CHAMPION BUCKET DEFINITIONS

These sets determine which IF branch a champion falls into across multiple decisions:

### RANGED_POKE_CHAMPS (→ resolve B: Second Wind)
```
Teemo, Quinn, Vayne, Kennen, Kayle, Smolder, Gnar, Jayce, Gangplank,
Heimerdinger, Rumble, Malphite, Yone, Yasuo, Fiora, Varus, Akshan,
Aurora, Aurelion Sol, Cassiopeia, Ryze, Swain
```
PDF/Video: "ranged champions or poke champs, even Fiora/Yas/Yone's Q poke"

### BURST_CC_CHAMPS (→ resolve C1: BonePlating + Unflinching, for Grasp only)
```
Riven, Renekton, Jax, Volibear, Pantheon, Sett, Urgot, Kled, Nocturne, Wukong
```
PDF p65: "Jax, Riven, Renekton, Pantheon, Volibear, anything with stun/CC and burst"

### BURST_CHAMPS (→ resolve C2: BonePlating, for non-Grasp)
```
Riven, Renekton, Jax, Kled, Nocturne, Wukong, Ambessa, Sett
```
Similar to above but for when resolve is secondary (only 1 slot)

### MS_SHARD_CHAMPS (→ Movement Speed shard)
```
Jax, Tryndamere, Yone, Yasuo, Trundle, Zaahen, Darius
```
Video 7:02: "Jax, Trinamer, Yon, Yasuo, Zahan, and Trundle... Darius because he just looks to run at you"

### ADAPTIVE_SHARD_CHAMPS (→ Adaptive Force shard)
```
Vayne, Gwen, Kayle, Nasus
```
Video 7:37: "taking HP will just make them deal more damage, like Vayne or Gwen... squishy like Kayle or Nasus"

### EXHAUST_PRIMARY (→ Exhaust/TP)
```
Tryndamere
```

### EXHAUST_WITH_GHOST (→ Exhaust/Ghost)
```
Riven, Renekton
```

### EXHAUST_SECONDARY (→ Exhaust viable)
```
Yasuo, Yone, Jax, Irelia, Rengar
```

### BAD_AD_MATCHUPS (→ Cloth Armor start)
```
Riven, Jax, Renekton, Kled, Sett, Tryndamere, Irelia
```
PDF p40: "Bad AD Matchup - Armor Cloth & Refillable (Riven, Jax)"

### AP_MELEE_CHAMPS (→ Long Sword + Refillable start)
```
Gwen, Mordekaiser, Sylas
```
PDF p40: "AP Matchup - Long sword & Refill (Gwen, Morde)"

### AP_POKE_CHAMPS (→ Doran's Shield start)
```
Teemo, Gragas, Volibear, Rumble, Heimerdinger
```
PDF p40: "AP poke matchup - Doran's Shield (Teemo, Gragas, Volibear's passive)"

### SHEEN_ICEBORN_CHAMPS (→ Iceborn Cleaver build)
```
Jax, Fiora, Renekton, Kled, Yasuo, Riven, Irelia
```
Mobafire: "can work into most AD counters like Jax, Ren, Kled"

### TIAMAT_TITANIC_CHAMPS (→ Titanic Breaker build)
```
Tryndamere, Trundle, Sett, Yone
```
Mobafire: "Good into Non HP/Tank Killers... champs that need to snowball"

### ECLIPSE_POKE_CHAMPS (→ Eclipse Poke build)
```
Teemo, Aurora, Akali, Kayle, Gnar, Quinn, Akshan
```
Mobafire: "E max into Eclipse & Shojin... Works into range top"

### SUNDERED_SKY_CHAMPS (→ Sundered Sky Rush build)
```
Jayce, Gragas, Gangplank
```
Mobafire: "Fighter Tank Build for aggressive Yorick Mains"

### LIANDRY_SHRED_CHAMPS (→ Liandry Tank Shred build)
```
Cho'Gath, Dr. Mundo, Sion, Tahm Kench, Ornn, Maokai
```
Mobafire: "Beats any Tank, good into Cho'Gath, Tahmkench, Ornn, Mundo"

### HP_STACK_TANKS (→ Cut Down swap when Precision secondary)
```
Sion, Cho'Gath
```
Video 13:22: "as long as the enemy is above 50% HP, you will deal bonus damage"

---

## VERIFICATION CASES

### Jax (EXTREME)
- Keystones: Grasp-1, Comet, Aery
- Resolve: C1 (BonePlating + Unflinching) — he's in BURST_CC_CHAMPS
- Shards: AS / MS / Tenacity — MS_SHARD_CHAMPS
- Summoners: Exhaust viable — EXHAUST_SECONDARY
- Starter: Cloth Armor + Refillable — BAD_AD_MATCHUPS
- Items: VS Jax (Iceborn) — item_category="vs_jax_iceborn"

### Tryndamere (EXTREME)
- Keystones: Grasp-2, Grasp-1, Grasp-3, Conqueror, Phase Rush
- Resolve: A1 default (not in poke or burst buckets by default)
- Shards: AS / MS / Tenacity — MS_SHARD_CHAMPS
- Summoners: Exhaust/TP — EXHAUST_PRIMARY
- Starter: Cloth Armor + Refillable — BAD_AD_MATCHUPS
- Items: VS Trynd (Conqueror) — item_category="vs_trynd_conq"

### Teemo (Medium)
- Keystones: Aery, Comet
- Resolve: B2 (Demolish + SecondWind) — RANGED_POKE_CHAMPS
- Shards: AS / HP / Tenacity — default (not in MS or AF set)
- Summoners: Ghost/Ignite — default
- Starter: Doran's Shield — AP_POKE_CHAMPS
- Items: Eclipse Poke — ECLIPSE_POKE_CHAMPS

### Warwick (EXTREME)
- Keystones: Comet, Conqueror
- Resolve: A2 (Demolish + Revitalize) — not in poke or burst buckets
- Shards: AS / HP / Tenacity — default
- Summoners: Ghost/Ignite — default
- Starter: Doran's Blade + HP — default
- Items: Default BBC — default

### Sett (EXTREME)
- Keystones: Grasp-1
- Resolve: C1 (BonePlating + Unflinching) — in BURST_CC_CHAMPS
- Shards: AS / HP / Tenacity — default
- Summoners: Ghost/Ignite — default
- Starter: Cloth Armor + Refillable — BAD_AD_MATCHUPS
- Items: Titanic Breaker — item_category="titanic_breaker"

### Irelia (EXTREME, BAN HER)
- Keystones: Grasp-1, Conqueror, HoB
- Resolve: A1 default (not burst/CC archetype — her threat is sustained Q resets)
- Shards: AS / HP / Tenacity — default
- Summoners: Exhaust/TP — matchup override
- Starter: Cloth Armor + Refillable — BAD_AD_MATCHUPS
- Items: VS Irelia — item_category="vs_irelia"

---

## BUGS FOUND IN CURRENT ENGINE

### BUG 1: Keystone-dependent item paths missing
**Problem**: Jax Comet/Aery gets "VS Jax (Iceborn)" — WRONG. Should get "VS Jax (Shojin)".
**Source**: Mobafire L540-541: "VS Jax Shojin-first path — Works with Conqueror or Comet for poke-heavy lane"
**Root cause**: `matchup.item_category="vs_jax_iceborn"` applies to ALL keystones. Need (enemy, keystone) → item_path.
**Fix needed**: item_path() should take keystone as input. IF keystone is Grasp → Iceborn path, ELSE → Shojin path.

### BUG 2: Volibear non-Grasp resolve is wrong
**Problem**: Volibear Conqueror gets resolve A (Revitalize) — should get B (SecondWind).
**Source**: PDF p66: "Volibear (Passive)" listed under Second Wind champions.
           Video: "Volibar with his lightning passive" for Second Wind.
**Root cause**: Override only applies to Grasp primary. Volibear not in RANGED_POKE_CHAMPS.
**Fix**: Add Volibear to RANGED_POKE_CHAMPS (used only for resolve, not items).

### BUG 3: Starter item text/template mismatch
**Problem**: Yasuo starter_info says "Doran's Blade" but item template (Iceborn Cleaver) has D.Shield IDs.
**Root cause**: starter_items() is enemy-based, item template starters are build-based. No reconciliation.
**Fix**: Either make starter_items() account for the item build path, or use item template starters as source of truth and remove the text that conflicts.

### BUG 4: Missing keystone-item routing for Tryndamere
**Problem**: All Tryndamere keystones get "VS Trynd (Conqueror)" including Grasp pages.
**Source**: Mobafire has VS Trynd (Iceborn Old) as a separate Grasp-compatible tank path.
**Fix**: Grasp keystones → VS Trynd (Iceborn Old), Conqueror → VS Trynd (Conqueror)
