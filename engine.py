"""Decision tree engine — assembles full build options from rules + data.

Core function: recommend_builds(champion, enemy) -> list[BuildOption]
Each BuildOption contains full rune page IDs, item IDs, and advice text.
No LLM involved — all logic is hardcoded from Kampsycho guide.
"""

from dataclasses import dataclass, field

from data.rune_pages import RunePageTemplate, SHARD_AS
from data.item_builds import ItemBuildTemplate
from data.matchup_table import get_matchup, MatchupInfo
from data.user_config import get_merged_rune_pages, get_merged_item_builds, get_merged_rune_build_compat
from data.rules import (
    resolve_adaptation,
    shard_choice,
    summoner_spells,
    starter_items,
    item_path,
    precision_secondary_adaptation,
    boot_recommendation,
    first_back_recommendation,
    relevant_combos,
    build_order_note,
    late_game_note,
)
from data.item_builds import ITEM_COMBOS, FIRST_BACK_ITEMS
from data.skill_orders import resolve_skill_order, get_skill_order


@dataclass
class BuildOption:
    keystone: str                           # Rune page name (e.g. "Grasp-1")
    rune_page_name: str                     # Same as keystone for display
    primary_style_id: int                   # 8000-8400
    sub_style_id: int                       # 8000-8400
    selected_perk_ids: list[int]            # 9 rune IDs ready for LCU import
    item_build_name: str                    # Item build template name
    starter: list[int]                      # Starter item IDs
    boots: list[int]                        # Boot options
    core: list[int]                         # Core item IDs
    situational: list[int]                  # Situational item IDs
    difficulty: str                         # Easy/Medium/Advanced/HARD/EXTREME
    summoners: str                          # "Ghost/Ignite", "Exhaust/TP", etc.
    starter_info: dict = field(default_factory=dict)  # {name, note}
    resolve_code: str = ""                  # A/B/C
    shard_info: str = ""                    # "AS/HP/Tenacity", "AS/MS/Tenacity", etc.
    reasoning: str = ""                     # Static advice text from guide
    special_note: str = ""                  # "BAN HER", etc.
    item_build_description: str = ""        # Item build template description
    skill_order_id: str = "standard"        # Skill order template ID
    skill_order_name: str = ""              # Display name
    skill_order_levels: list[str] = field(default_factory=list)  # 18 entries: Q/W/E/R per level
    skill_order_max: list[str] = field(default_factory=list)     # Max priority: ["Q","E","W"]
    skill_order_description: str = ""       # When/why to use this order
    skill_order_condition: str = ""         # Condition text
    # --- Item system v2 fields ---
    boot_rec: dict = field(default_factory=dict)          # {boot, boot_id, rush, note}
    first_back: list[dict] = field(default_factory=list)  # [{gold, items, note}]
    item_combos: list[dict] = field(default_factory=list) # [{name, items, description, tags}]
    build_order: str = ""                                  # Component buy order note
    late_game: str = ""                                    # Late game swap note


def _shard_display(shards: tuple[int, int, int]) -> str:
    """Convert shard IDs to human-readable string."""
    from data.rune_pages import SHARD_AS, SHARD_HP, SHARD_MS, SHARD_AF, SHARD_TENACITY, SHARD_ARMOR, SHARD_MR
    names = {
        SHARD_AS: "AS", SHARD_HP: "HP", SHARD_MS: "MS",
        SHARD_AF: "Adaptive", SHARD_TENACITY: "Tenacity",
        SHARD_ARMOR: "Armor", SHARD_MR: "MR",
    }
    return " / ".join(names.get(s, str(s)) for s in shards)


def _apply_resolve_overrides(
    template: RunePageTemplate,
    resolve: dict,
    shards: tuple[int, int, int],
) -> list[int]:
    """Apply resolve and shard overrides to a rune page template.

    Returns new list of 9 perk IDs.
    """
    perks = list(template.selected_perk_ids)

    is_resolve_primary = template.primary_style_id == 8400  # Resolve

    if is_resolve_primary:
        # Grasp pages: perks[0]=keystone, [1]=Demolish, [2]=row2, [3]=row3, [4]=sec1, [5]=sec2
        if resolve["row2"] is not None:
            perks[2] = resolve["row2"]
        if resolve["row3"] is not None:
            perks[3] = resolve["row3"]
    else:
        # Non-Grasp: resolve is secondary → perks[4]=Demolish, perks[5]=resolve slot
        if resolve["row2"] is not None:
            perks[5] = resolve["row2"]

    # Apply shard overrides (last 3 slots)
    perks[6] = shards[0]
    perks[7] = shards[1]
    perks[8] = shards[2]

    return perks


def recommend_builds(champion: str, enemy: str) -> list[BuildOption]:
    """Run the Kampsycho decision tree for a matchup.

    Returns ranked list of full build options. First option is primary recommendation.
    """
    RUNE_PAGES = get_merged_rune_pages()
    ITEM_BUILDS = get_merged_item_builds()
    RUNE_BUILD_COMPAT = get_merged_rune_build_compat()

    matchup = get_matchup(enemy)
    options = []

    for keystone_name in matchup.keystones:
        rune_template = RUNE_PAGES.get(keystone_name)
        if not rune_template:
            continue

        # Step 1: Resolve adaptation
        resolve = resolve_adaptation(keystone_name, enemy)

        # Step 2: Shard choice
        shards = shard_choice(enemy, matchup.shard_override)

        # Step 3: Summoner spells
        summs = summoner_spells(
            enemy,
            exhaust_viable=matchup.exhaust_viable,
            matchup_spells=matchup.summoner_spells,
        )

        # Step 4: Starter items
        starters = starter_items(enemy)

        # Step 5: Item path (keystone-dependent for Jax, Trynd, ranged AD)
        primary_build_name = item_path(enemy, matchup.item_category, keystone_name)

        # Step 6: Get item template
        item_template = ITEM_BUILDS.get(primary_build_name)
        if not item_template:
            item_template = ITEM_BUILDS["Default BBC"]
            primary_build_name = "Default BBC"

        # Step 7: Apply overrides to rune template
        final_perks = _apply_resolve_overrides(rune_template, resolve, shards)
        final_perks = precision_secondary_adaptation(final_perks, rune_template.sub_style_id, enemy)

        # Step 8: Skill order
        skill_id = resolve_skill_order(enemy, keystone_name, matchup.tags)
        skill = get_skill_order(skill_id)

        # Step 9: Boot recommendation
        boot_rec = boot_recommendation(enemy, keystone_name, primary_build_name)

        # Step 10: First back items
        fb_key = first_back_recommendation(enemy, primary_build_name)
        first_back = FIRST_BACK_ITEMS.get(fb_key, FIRST_BACK_ITEMS["default"])

        # Step 11: Item combos for mix-and-match
        combo_names = relevant_combos(enemy, primary_build_name)
        combos = []
        for cn in combo_names:
            combo = ITEM_COMBOS.get(cn)
            if combo:
                combos.append({
                    "name": combo.name,
                    "items": list(combo.items),
                    "description": combo.description,
                    "tags": list(combo.tags),
                })

        # Step 12: Build order and late game notes
        bo_note = build_order_note(primary_build_name, enemy)
        lg_note = late_game_note(primary_build_name)

        options.append(BuildOption(
            keystone=keystone_name,
            rune_page_name=keystone_name,
            primary_style_id=rune_template.primary_style_id,
            sub_style_id=rune_template.sub_style_id,
            selected_perk_ids=final_perks,
            item_build_name=primary_build_name,
            starter=list(item_template.starter),
            boots=list(item_template.boots),
            core=list(item_template.core),
            situational=list(item_template.situational),
            difficulty=matchup.difficulty,
            summoners=summs,
            starter_info=starters,
            resolve_code=resolve["code"],
            shard_info=_shard_display(shards),
            reasoning=matchup.advice,
            special_note=matchup.special_note,
            item_build_description=item_template.description,
            skill_order_id=skill.id,
            skill_order_name=skill.name,
            skill_order_levels=list(skill.levels),
            skill_order_max=list(skill.max_order),
            skill_order_description=skill.description,
            skill_order_condition=skill.condition,
            boot_rec=boot_rec,
            first_back=first_back,
            item_combos=combos,
            build_order=bo_note,
            late_game=lg_note,
        ))

    # Also add compatible alternative builds for the primary keystone
    if matchup.keystones and len(options) > 0:
        primary_keystone = matchup.keystones[0]
        compatible_builds = RUNE_BUILD_COMPAT.get(primary_keystone, [])
        primary_build_name = options[0].item_build_name

        for alt_build_name in compatible_builds:
            if alt_build_name == primary_build_name:
                continue
            if alt_build_name not in ITEM_BUILDS:
                continue
            # Only add first 2 alternatives to avoid clutter
            alt_count = sum(1 for o in options if o.keystone == primary_keystone and o.item_build_name != primary_build_name)
            if alt_count >= 2:
                break

            alt_template = ITEM_BUILDS[alt_build_name]
            rune_template = RUNE_PAGES[primary_keystone]
            resolve = resolve_adaptation(primary_keystone, enemy)
            shards = shard_choice(enemy, matchup.shard_override)

            final_perks = _apply_resolve_overrides(rune_template, resolve, shards)
            final_perks = precision_secondary_adaptation(final_perks, rune_template.sub_style_id, enemy)

            alt_skill_id = resolve_skill_order(enemy, primary_keystone, matchup.tags)
            alt_skill = get_skill_order(alt_skill_id)

            alt_boot_rec = boot_recommendation(enemy, primary_keystone, alt_build_name)
            alt_fb_key = first_back_recommendation(enemy, alt_build_name)
            alt_first_back = FIRST_BACK_ITEMS.get(alt_fb_key, FIRST_BACK_ITEMS["default"])
            alt_combo_names = relevant_combos(enemy, alt_build_name)
            alt_combos = []
            for cn in alt_combo_names:
                combo = ITEM_COMBOS.get(cn)
                if combo:
                    alt_combos.append({
                        "name": combo.name,
                        "items": list(combo.items),
                        "description": combo.description,
                        "tags": list(combo.tags),
                    })

            options.append(BuildOption(
                keystone=primary_keystone,
                rune_page_name=primary_keystone,
                primary_style_id=rune_template.primary_style_id,
                sub_style_id=rune_template.sub_style_id,
                selected_perk_ids=final_perks,
                item_build_name=alt_build_name,
                starter=list(alt_template.starter),
                boots=list(alt_template.boots),
                core=list(alt_template.core),
                situational=list(alt_template.situational),
                difficulty=matchup.difficulty,
                summoners=summoner_spells(enemy, matchup.exhaust_viable, matchup.summoner_spells),
                starter_info=starter_items(enemy),
                resolve_code=resolve["code"],
                shard_info=_shard_display(shards),
                reasoning=f"Alternative build: {alt_template.description[:100]}",
                special_note=matchup.special_note,
                item_build_description=alt_template.description,
                skill_order_id=alt_skill.id,
                skill_order_name=alt_skill.name,
                skill_order_levels=list(alt_skill.levels),
                skill_order_max=list(alt_skill.max_order),
                skill_order_description=alt_skill.description,
                skill_order_condition=alt_skill.condition,
                boot_rec=alt_boot_rec,
                first_back=alt_first_back,
                item_combos=alt_combos,
                build_order=build_order_note(alt_build_name, enemy),
                late_game=late_game_note(alt_build_name),
            ))

    return options


def build_option_to_dict(option: BuildOption) -> dict:
    """Convert BuildOption to JSON-serializable dict."""
    return {
        "keystone": option.keystone,
        "rune_page_name": option.rune_page_name,
        "primary_style_id": option.primary_style_id,
        "sub_style_id": option.sub_style_id,
        "selected_perk_ids": option.selected_perk_ids,
        "item_build_name": option.item_build_name,
        "starter": option.starter,
        "boots": option.boots,
        "core": option.core,
        "situational": option.situational,
        "difficulty": option.difficulty,
        "summoners": option.summoners,
        "starter_info": option.starter_info,
        "resolve_code": option.resolve_code,
        "shard_info": option.shard_info,
        "reasoning": option.reasoning,
        "special_note": option.special_note,
        "item_build_description": option.item_build_description,
        "skill_order": {
            "id": option.skill_order_id,
            "name": option.skill_order_name,
            "levels": option.skill_order_levels,
            "max_order": option.skill_order_max,
            "description": option.skill_order_description,
            "condition": option.skill_order_condition,
        },
        "boot_rec": option.boot_rec,
        "first_back": option.first_back,
        "item_combos": option.item_combos,
        "build_order": option.build_order,
        "late_game": option.late_game,
    }


def recommend_builds_multi(champion: str, enemies: list[dict]) -> list[BuildOption]:
    """Averaged build recommendation across multiple potential enemies.

    Each enemy dict: {"name": str, "weight": float} where weight is top-lane
    probability (0.0-1.0).

    Scores keystones and item builds by how often they appear as the PRIMARY
    (first) recommendation, weighted by enemy probability. Returns merged
    BuildOption list with the top combo as primary plus 1-2 alternatives.
    """
    ITEM_BUILDS = get_merged_item_builds()

    if not enemies:
        return []

    # Sort enemies by weight descending for later use
    enemies_sorted = sorted(enemies, key=lambda e: e["weight"], reverse=True)
    highest_weight_enemy = enemies_sorted[0]

    # Check low-confidence edge case
    low_confidence = all(e["weight"] < 0.10 for e in enemies)

    # Collect per-enemy build results and score keystones/item builds
    keystone_scores: dict[str, float] = {}
    item_build_scores: dict[str, float] = {}
    # Cache full build lists per enemy for later retrieval
    enemy_builds: dict[str, list[BuildOption]] = {}

    for enemy in enemies:
        name = enemy["name"]
        weight = enemy["weight"]
        builds = recommend_builds(champion, name)
        enemy_builds[name] = builds

        if not builds:
            continue

        # Primary recommendation is builds[0]
        primary = builds[0]
        keystone_scores[primary.keystone] = keystone_scores.get(primary.keystone, 0.0) + weight
        item_build_scores[primary.item_build_name] = item_build_scores.get(primary.item_build_name, 0.0) + weight

    if not keystone_scores:
        return []

    # Find top keystone and top item build
    best_keystone = max(keystone_scores, key=keystone_scores.get)
    best_item_build = max(item_build_scores, key=item_build_scores.get)

    # Build the reasoning string: "Averaged: Jax (70%), Gnar (25%), Irelia (5%)"
    parts = [f"{e['name']} ({e['weight']:.0%})" for e in enemies_sorted]
    reasoning = "Averaged: " + ", ".join(parts)
    if low_confidence:
        reasoning += " [LOW CONFIDENCE — all enemies <10% probability]"

    # Use the highest-weight enemy's build data for resolve, shards, summoners, starter
    ref_builds = enemy_builds.get(highest_weight_enemy["name"], [])

    # Find reference build option matching best_keystone from highest-weight enemy,
    # falling back to their primary build
    ref_option = None
    if ref_builds:
        for b in ref_builds:
            if b.keystone == best_keystone:
                ref_option = b
                break
        if ref_option is None:
            ref_option = ref_builds[0]

    if ref_option is None:
        return []

    # Find the item template for the best item build
    best_item_template = ITEM_BUILDS.get(best_item_build)
    if not best_item_template:
        best_item_template = ITEM_BUILDS.get("Default BBC")
        best_item_build = "Default BBC"

    # Build primary recommendation: best keystone + best item, with ref_option's
    # rune perks / resolve / shards / summoners / starter
    primary_option = BuildOption(
        keystone=best_keystone,
        rune_page_name=best_keystone,
        primary_style_id=ref_option.primary_style_id,
        sub_style_id=ref_option.sub_style_id,
        selected_perk_ids=list(ref_option.selected_perk_ids),
        item_build_name=best_item_build,
        starter=list(best_item_template.starter),
        boots=list(best_item_template.boots),
        core=list(best_item_template.core),
        situational=list(best_item_template.situational),
        difficulty=ref_option.difficulty,
        summoners=ref_option.summoners,
        starter_info=ref_option.starter_info,
        resolve_code=ref_option.resolve_code,
        shard_info=ref_option.shard_info,
        reasoning=reasoning,
        special_note=ref_option.special_note,
        item_build_description=best_item_template.description,
        skill_order_id=ref_option.skill_order_id,
        skill_order_name=ref_option.skill_order_name,
        skill_order_levels=list(ref_option.skill_order_levels),
        skill_order_max=list(ref_option.skill_order_max),
        skill_order_description=ref_option.skill_order_description,
        skill_order_condition=ref_option.skill_order_condition,
    )

    options = [primary_option]

    # Add 1-2 alternatives: next-best keystone or item combos
    # First: same keystone, second-best item build
    alt_items = sorted(item_build_scores, key=item_build_scores.get, reverse=True)
    for alt_item_name in alt_items:
        if alt_item_name == best_item_build:
            continue
        alt_template = ITEM_BUILDS.get(alt_item_name)
        if not alt_template:
            continue
        options.append(BuildOption(
            keystone=best_keystone,
            rune_page_name=best_keystone,
            primary_style_id=ref_option.primary_style_id,
            sub_style_id=ref_option.sub_style_id,
            selected_perk_ids=list(ref_option.selected_perk_ids),
            item_build_name=alt_item_name,
            starter=list(alt_template.starter),
            boots=list(alt_template.boots),
            core=list(alt_template.core),
            situational=list(alt_template.situational),
            difficulty=ref_option.difficulty,
            summoners=ref_option.summoners,
            starter_info=ref_option.starter_info,
            resolve_code=ref_option.resolve_code,
            shard_info=ref_option.shard_info,
            reasoning=f"Alt item build ({alt_item_name}, score {item_build_scores[alt_item_name]:.0%})",
            special_note="",
            item_build_description=alt_template.description,
            skill_order_id=ref_option.skill_order_id,
            skill_order_name=ref_option.skill_order_name,
            skill_order_levels=list(ref_option.skill_order_levels),
            skill_order_max=list(ref_option.skill_order_max),
            skill_order_description=ref_option.skill_order_description,
            skill_order_condition=ref_option.skill_order_condition,
        ))
        break  # Only 1 alt item build

    # Second: second-best keystone with best item build
    alt_keystones = sorted(keystone_scores, key=keystone_scores.get, reverse=True)
    for alt_ks in alt_keystones:
        if alt_ks == best_keystone:
            continue
        if len(options) >= 3:
            break
        # Find a reference build with this keystone from any enemy
        alt_ref = None
        for name, builds in enemy_builds.items():
            for b in builds:
                if b.keystone == alt_ks:
                    alt_ref = b
                    break
            if alt_ref:
                break
        if not alt_ref:
            continue
        options.append(BuildOption(
            keystone=alt_ks,
            rune_page_name=alt_ks,
            primary_style_id=alt_ref.primary_style_id,
            sub_style_id=alt_ref.sub_style_id,
            selected_perk_ids=list(alt_ref.selected_perk_ids),
            item_build_name=best_item_build,
            starter=list(best_item_template.starter),
            boots=list(best_item_template.boots),
            core=list(best_item_template.core),
            situational=list(best_item_template.situational),
            difficulty=alt_ref.difficulty,
            summoners=ref_option.summoners,
            starter_info=ref_option.starter_info,
            resolve_code=ref_option.resolve_code,
            shard_info=ref_option.shard_info,
            reasoning=f"Alt keystone ({alt_ks}, score {keystone_scores[alt_ks]:.0%})",
            special_note="",
            item_build_description=best_item_template.description,
            skill_order_id=ref_option.skill_order_id,
            skill_order_name=ref_option.skill_order_name,
            skill_order_levels=list(ref_option.skill_order_levels),
            skill_order_max=list(ref_option.skill_order_max),
            skill_order_description=ref_option.skill_order_description,
            skill_order_condition=ref_option.skill_order_condition,
        ))
        break  # Only 1 alt keystone

    return options


def build_option_multi_to_dict(options: list[BuildOption], enemies: list[dict]) -> dict:
    """Convert multi-enemy build options to a JSON-serializable dict.

    Includes the enemy probability breakdown alongside the build options.
    """
    return {
        "enemies": [
            {"name": e["name"], "weight": e["weight"]}
            for e in sorted(enemies, key=lambda x: x["weight"], reverse=True)
        ],
        "builds": [build_option_to_dict(o) for o in options],
    }
