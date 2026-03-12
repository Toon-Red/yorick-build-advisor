"""Tree-based decision engine — walks a JSON decision tree to produce BuildOption objects.

Replaces engine.py as the build recommendation engine for guide-driven builds.
Given a guide JSON (with matchups, rune_pages, item_builds, buckets, resolve_mappings,
resolve_overrides, rune_build_compat, and a decision tree root), this module walks the
tree depth-first and assembles identical BuildOption objects to what engine.py produces.

Core functions:
  recommend_from_guide(guide_json, champion, enemy) -> list[BuildOption]
  recommend_from_guide_multi(guide_json, champion, enemies) -> list[BuildOption]
"""

from __future__ import annotations

from engine import BuildOption, _shard_display, build_option_to_dict
from data.skill_orders import resolve_skill_order, get_skill_order
from data.rules import (
    precision_secondary_adaptation,
    boot_recommendation,
    first_back_recommendation,
    relevant_combos,
    build_order_note,
    late_game_note,
)
from data.item_builds import ITEM_COMBOS, FIRST_BACK_ITEMS

# Shard name-to-ID mapping (mirrors data/rune_pages.py constants)
_SHARD_IDS = {
    "AS": 5005,
    "HP": 5001,
    "MS": 5010,
    "AF": 5008,      # Adaptive Force
    "Adaptive": 5008,
    "Tenacity": 5013,
    "Armor": 5002,
    "MR": 5003,
    "AH": 5007,
    "HP%": 5011,
}


# ---------------------------------------------------------------------------
# Context — mutable bag of values populated during tree walk
# ---------------------------------------------------------------------------

class _Context:
    """Execution context for a single tree walk."""

    __slots__ = (
        "champion", "enemy", "matchup", "guide",
        # Values set by SET nodes
        "keystones", "resolve_code", "shards", "summoners",
        "starter_info", "item_build", "difficulty", "advice",
        "special_note", "tags", "shard_override", "exhaust_viable",
        "item_category",
        # Per-keystone resolve re-walk
        "current_keystone",
    )

    def __init__(self, champion: str, enemy: str, matchup: dict, guide: dict):
        self.champion = champion
        self.enemy = enemy
        self.matchup = matchup
        self.guide = guide

        # Defaults — tree SET nodes overwrite these
        self.keystones: list[str] = []
        self.resolve_code: str = "A"
        self.shards: str = "AS / HP / Tenacity"
        self.summoners: str = "Ghost/Ignite"
        self.starter_info: dict = {"name": "Doran's Blade + Health Potion", "note": "Standard start for most matchups."}
        self.item_build: str = "Default BBC"
        self.difficulty: str = "Medium"
        self.advice: str = ""
        self.special_note: str = ""
        self.tags: list[str] = []
        self.shard_override: str | None = None
        self.exhaust_viable: bool = False
        self.item_category: str = "default"
        self.current_keystone: str = ""

    def get(self, dotted_path: str):
        """Resolve a dotted path like 'matchup.keystones' or 'difficulty'."""
        parts = dotted_path.split(".", 1)
        root = parts[0]

        if root == "matchup" and len(parts) == 2:
            key = parts[1]
            return self.matchup.get(key)
        elif root == "enemy":
            return self.enemy
        elif root == "champion":
            return self.champion

        # Direct context attribute
        return getattr(self, dotted_path, None)

    def set(self, key: str, value):
        """Set a context attribute. Maps tree-friendly names to Context slots."""
        # Map tree SET keys to Context attribute names
        if key == "starter_items":
            # Tree sets a simple string; wrap into starter_info dict
            self.starter_info = {"name": value, "note": ""}
            return
        setattr(self, key, value)


# ---------------------------------------------------------------------------
# Matchup lookup (case-insensitive with archetype fallback)
# ---------------------------------------------------------------------------

def _lookup_matchup(guide: dict, enemy: str) -> dict:
    """Find matchup entry by enemy name (case-insensitive), with fallback."""
    matchups = guide.get("data", {}).get("matchups", {})

    # Exact match
    if enemy in matchups:
        return matchups[enemy]

    # Case-insensitive
    enemy_lower = enemy.lower().strip()
    for name, info in matchups.items():
        if name.lower() == enemy_lower:
            return info

    # Archetype fallback — check if guide has archetypes
    archetypes = guide.get("data", {}).get("archetypes", {})
    for archetype_name, arch_data in archetypes.items():
        champ_list = arch_data.get("champions", [])
        if enemy in champ_list or enemy_lower in [c.lower() for c in champ_list]:
            return arch_data.get("default_matchup", {})

    # Ultimate fallback: generic medium matchup
    return {
        "difficulty": "Medium",
        "keystones": ["Grasp-1", "Conqueror"],
        "item_category": "default",
        "tags": [],
        "shard_override": None,
        "exhaust_viable": False,
        "summoner_spells": "Ghost/Ignite",
        "special_note": "",
        "advice": "No specific matchup data. Play standard.",
    }


# ---------------------------------------------------------------------------
# Condition evaluation
# ---------------------------------------------------------------------------

def _eval_condition(condition: dict, ctx: _Context) -> bool:
    """Evaluate an IF node condition against the context."""
    field = condition["field"]
    op = condition["op"]
    value = condition["value"]

    # Special: enemy_bucket check — "is enemy in one of these bucket sets?"
    if field == "enemy_bucket":
        buckets = ctx.guide.get("data", {}).get("buckets", {})
        if op == "in":
            # value is a list of bucket names; check if enemy is in ANY of them
            bucket_names = value if isinstance(value, list) else [value]
            for bucket_name in bucket_names:
                members = buckets.get(bucket_name, [])
                if ctx.enemy in members:
                    return True
            return False
        elif op == "not_in":
            bucket_names = value if isinstance(value, list) else [value]
            for bucket_name in bucket_names:
                members = buckets.get(bucket_name, [])
                if ctx.enemy in members:
                    return False
            return True

    # Special: current_keystone checks the keystone being iterated
    if field == "current_keystone":
        actual = ctx.current_keystone
        if op == "starts_with":
            return actual.startswith(value) if isinstance(value, str) else any(actual.startswith(v) for v in value)
        elif op == "eq":
            return actual == value
        elif op == "neq":
            return actual != value
        elif op == "in":
            vals = value if isinstance(value, list) else [value]
            return actual in vals
        elif op == "not_in":
            vals = value if isinstance(value, list) else [value]
            return actual not in vals

    # General field lookup from context
    actual = ctx.get(field)

    if op == "eq":
        return actual == value
    elif op == "neq":
        return actual != value
    elif op == "in":
        if isinstance(value, list):
            return actual in value
        return actual == value
    elif op == "not_in":
        if isinstance(value, list):
            return actual not in value
        return actual != value
    elif op == "starts_with":
        if isinstance(actual, str):
            if isinstance(value, list):
                return any(actual.startswith(v) for v in value)
            return actual.startswith(value)
        return False
    elif op == "contains":
        if isinstance(actual, (list, tuple, set)):
            return value in actual
        if isinstance(actual, str):
            return value in actual
        return False
    elif op == "is_null":
        return actual is None
    elif op == "is_not_null":
        return actual is not None

    return False


# ---------------------------------------------------------------------------
# SWITCH field evaluation
# ---------------------------------------------------------------------------

def _eval_switch_field(field: str, ctx: _Context) -> str | None:
    """Evaluate the SWITCH field and return which case should match.

    For enemy_bucket SWITCH, we return the bucket name that the enemy belongs to.
    For regular fields, we return the field value as a string.
    """
    if field == "enemy_bucket":
        # For SWITCH on enemy_bucket, the case 'match' is a bucket name.
        # We don't return a single value here; matching is done per-case.
        return "__bucket_switch__"

    val = ctx.get(field)
    return str(val) if val is not None else None


# ---------------------------------------------------------------------------
# Tree walker
# ---------------------------------------------------------------------------

def _walk_node(node: dict, ctx: _Context) -> None:
    """Recursively execute a single tree node."""
    node_type = node.get("type", "")

    if node_type == "ROOT":
        for child in node.get("children", []):
            _walk_node(child, ctx)

    elif node_type == "GROUP":
        for child in node.get("children", []):
            _walk_node(child, ctx)

    elif node_type == "SET":
        _exec_set(node, ctx)
        for child in node.get("children", []):
            _walk_node(child, ctx)

    elif node_type == "IF":
        cond = node.get("condition", {})
        if _eval_condition(cond, ctx):
            for child in node.get("children_true", []):
                _walk_node(child, ctx)
        else:
            for child in node.get("children_false", []):
                _walk_node(child, ctx)

    elif node_type == "SWITCH":
        _exec_switch(node, ctx)

    # Unknown node types are silently skipped


def _exec_set(node: dict, ctx: _Context) -> None:
    """Execute SET node assignments."""
    for assignment in node.get("assignments", []):
        key = assignment["key"]
        raw_value = assignment["value"]
        ref_type = assignment.get("ref_type", "literal")

        if ref_type == "lookup":
            # Dotted path into context
            resolved = ctx.get(raw_value)
            ctx.set(key, resolved)
        elif ref_type == "literal":
            ctx.set(key, raw_value)
        elif ref_type == "bucket":
            # Store bucket name for later use (value is a bucket name string)
            ctx.set(key, raw_value)
        elif ref_type == "item_category":
            # Map item category string to actual build name
            resolved = ctx.get(raw_value) if "." in raw_value else raw_value
            build_name = _item_category_to_build_name(resolved or "default")
            ctx.set(key, build_name)
        elif ref_type == "item_build":
            # Item build reference — store the name string
            ctx.set(key, raw_value)
        elif ref_type == "rune_page":
            # Rune page reference — store the name string
            ctx.set(key, raw_value)
        else:
            # Default: treat as literal
            ctx.set(key, raw_value)


def _exec_switch(node: dict, ctx: _Context) -> None:
    """Execute SWITCH node — find matching case and walk its children."""
    field = node.get("field", "")
    cases = node.get("cases", [])

    if field == "enemy_bucket":
        # Special bucket switch: each case.match is a bucket name.
        # Check if enemy is in that bucket.
        buckets = ctx.guide.get("data", {}).get("buckets", {})
        default_case = None
        matched = False

        for case in cases:
            match_val = case.get("match", "")
            if match_val == "*":
                default_case = case
                continue
            members = buckets.get(match_val, [])
            if ctx.enemy in members:
                for child in case.get("children", []):
                    _walk_node(child, ctx)
                matched = True
                break

        if not matched and default_case is not None:
            for child in default_case.get("children", []):
                _walk_node(child, ctx)
        return

    # Regular field switch
    actual = ctx.get(field)
    actual_str = str(actual) if actual is not None else ""
    default_case = None
    matched = False

    for case in cases:
        match_val = case.get("match", "")
        if match_val == "*":
            default_case = case
            continue
        if actual_str == match_val:
            for child in case.get("children", []):
                _walk_node(child, ctx)
            matched = True
            break

    if not matched and default_case is not None:
        for child in default_case.get("children", []):
            _walk_node(child, ctx)


# ---------------------------------------------------------------------------
# Resolve override application (mirrors engine.py _apply_resolve_overrides)
# ---------------------------------------------------------------------------

def _parse_shards(shard_str: str) -> tuple[int, int, int]:
    """Parse a shard display string like 'AS / HP / Tenacity' into (id, id, id)."""
    parts = [p.strip() for p in shard_str.split("/")]
    ids = []
    for part in parts:
        sid = _SHARD_IDS.get(part)
        if sid is None:
            # Try as integer
            try:
                sid = int(part)
            except (ValueError, TypeError):
                sid = 5001  # Fallback to HP
        ids.append(sid)

    # Ensure exactly 3
    while len(ids) < 3:
        ids.append(5001)

    return (ids[0], ids[1], ids[2])


def _apply_resolve_overrides(
    template: dict,
    resolve: dict,
    shards: tuple[int, int, int],
) -> list[int]:
    """Apply resolve and shard overrides to a rune page template.

    template: guide rune_page dict with 'selected_perk_ids', 'primary_style_id'
    resolve: {"row2": int|None, "row3": int|None, "code": str}
    shards: (shard1, shard2, shard3)

    Returns new list of 9 perk IDs.
    """
    perks = list(template["selected_perk_ids"])

    is_resolve_primary = template["primary_style_id"] == 8400  # Resolve

    if is_resolve_primary:
        # Grasp pages: perks[0]=keystone, [1]=Demolish, [2]=row2, [3]=row3, [4]=sec1, [5]=sec2
        if resolve.get("row2") is not None:
            perks[2] = resolve["row2"]
        if resolve.get("row3") is not None:
            perks[3] = resolve["row3"]
    else:
        # Non-Grasp: resolve is secondary -> perks[4]=Demolish, perks[5]=resolve slot
        if resolve.get("row2") is not None:
            perks[5] = resolve["row2"]

    # Apply shard overrides (last 3 slots)
    perks[6] = shards[0]
    perks[7] = shards[1]
    perks[8] = shards[2]

    return perks


# ---------------------------------------------------------------------------
# Resolve mapping resolution
# ---------------------------------------------------------------------------

# Rune ID constants for resolve rows
_RESOLVE_RUNE_IDS = {
    "SECOND_WIND": 8444,
    "BONE_PLATING": 8473,
    "REVITALIZE": 8453,
    "UNFLINCHING": 8242,
    "OVERGROWTH": 8451,
    "CONDITIONING": 8429,
    "FONT_OF_LIFE": 8463,
    "DEMOLISH": 8446,
    "SHIELD_BASH": 8401,
}


def _resolve_for_keystone(
    guide: dict,
    enemy: str,
    keystone: str,
    resolve_code: str,
) -> dict:
    """Compute the resolve override dict for a specific keystone + resolve code.

    Uses guide.data.resolve_overrides for per-champ overrides (Grasp only),
    then guide.data.resolve_mappings for code-to-rune-ID translation.

    Returns {"row2": int|None, "row3": int|None, "code": str}
    """
    data = guide.get("data", {})
    is_primary = keystone.startswith("Grasp")

    # Per-champion overrides only apply when resolve is primary (Grasp pages),
    # matching engine.py resolve_adaptation which checks is_primary first.
    overrides = data.get("resolve_overrides", {})
    if is_primary and enemy in overrides:
        ov = overrides[enemy]
        return {
            "row2": ov.get("row2"),
            "row3": ov.get("row3"),
            "code": ov.get("code", resolve_code),
        }

    # Use resolve_mappings keyed by "primary" vs "secondary"
    mappings = data.get("resolve_mappings", {})

    if is_primary:
        code_map = mappings.get("primary", {}).get(resolve_code, {})
        return {
            "row2": code_map.get("row2"),
            "row3": code_map.get("row3"),
            "code": resolve_code,
        }
    else:
        code_map = mappings.get("secondary", {}).get(resolve_code, {})
        return {
            "row2": code_map.get("row2"),
            "row3": None,
            "code": resolve_code,
        }


# ---------------------------------------------------------------------------
# Shard override application
# ---------------------------------------------------------------------------

def _apply_shard_override(shard_str: str, matchup: dict, ctx: _Context) -> str:
    """Apply matchup-level shard_override and bucket-based shard overrides.

    Mirrors rules.py shard_choice: checks matchup.shard_override first,
    then bucket membership (MS_SHARD_CHAMPS, ADAPTIVE_SHARD_CHAMPS).
    """
    override = matchup.get("shard_override")
    if not override:
        # Check bucket-based overrides (same as rules.py shard_choice)
        buckets = ctx.guide.get("data", {}).get("buckets", {})
        if ctx.enemy in buckets.get("MS_SHARD_CHAMPS", []):
            override = "MS"
        elif ctx.enemy in buckets.get("ADAPTIVE_SHARD_CHAMPS", []):
            override = "AF"

    if not override:
        return shard_str

    parts = [p.strip() for p in shard_str.split("/")]
    if len(parts) >= 2:
        parts[1] = override
    return " / ".join(parts)


# ---------------------------------------------------------------------------
# Find the resolve subtree for re-walking per keystone
# ---------------------------------------------------------------------------

def _find_resolve_group(node: dict) -> dict | None:
    """Find the GROUP node labeled 'Resolve Adaptation' in the tree."""
    if node.get("type") == "GROUP" and node.get("label") == "Resolve Adaptation":
        return node

    # Search children
    for child in node.get("children", []):
        found = _find_resolve_group(child)
        if found:
            return found

    # Search children_true / children_false for IF nodes
    for child in node.get("children_true", []):
        found = _find_resolve_group(child)
        if found:
            return found
    for child in node.get("children_false", []):
        found = _find_resolve_group(child)
        if found:
            return found

    # Search cases for SWITCH nodes
    for case in node.get("cases", []):
        for child in case.get("children", []):
            found = _find_resolve_group(child)
            if found:
                return found

    return None


# ---------------------------------------------------------------------------
# Core: recommend_from_guide
# ---------------------------------------------------------------------------

def recommend_from_guide(guide_json: dict, champion: str, enemy: str) -> list[BuildOption]:
    """Run a guide's decision tree for a single matchup.

    Returns ranked list of BuildOption objects. First option is primary recommendation.
    Produces identical results to engine.py recommend_builds() when the guide JSON
    encodes the same rules.
    """
    data = guide_json.get("data", {})
    rune_pages = data.get("rune_pages", {})
    item_builds = data.get("item_builds", {})
    rune_build_compat = data.get("rune_build_compat", {})

    # Step 1: Look up matchup
    matchup = _lookup_matchup(guide_json, enemy)

    # Step 2: Initialize context with matchup data
    ctx = _Context(champion, enemy, matchup, guide_json)

    # Pre-populate context from matchup (these may be overridden by tree walk)
    ctx.keystones = list(matchup.get("keystones", []))
    ctx.difficulty = matchup.get("difficulty", "Medium")
    ctx.advice = matchup.get("advice", "")
    ctx.special_note = matchup.get("special_note", "")
    ctx.tags = list(matchup.get("tags", []))
    ctx.shard_override = matchup.get("shard_override")
    ctx.exhaust_viable = matchup.get("exhaust_viable", False)
    ctx.summoners = matchup.get("summoner_spells", "Ghost/Ignite")
    ctx.item_category = matchup.get("item_category", "default")

    # Step 3: Walk the tree (depth-first)
    root = guide_json.get("root")
    if root:
        _walk_node(root, ctx)

    # Step 4: Apply shard override from matchup (overrides tree if matchup says MS/AF)
    ctx.shards = _apply_shard_override(ctx.shards, matchup, ctx)

    # Step 5: Apply summoner spell logic from matchup
    # The matchup summoner_spells field takes priority; if tree didn't change it,
    # we keep the matchup value. Also handle exhaust logic.
    ctx.summoners = _resolve_summoners(ctx, matchup)

    # Step 6: Apply starter item logic from matchup (only if tree didn't set it)
    default_starter = "Doran's Blade + Health Potion"
    if ctx.starter_info.get("name") == default_starter:
        ctx.starter_info = _resolve_starters(ctx, matchup)

    # Step 7: Apply item path from matchup category (if tree didn't set it differently)
    if ctx.item_build == "Default BBC" and ctx.item_category != "default":
        ctx.item_build = _item_category_to_build_name(ctx.item_category)
    # If still default and no category override, check bucket-based item path
    if ctx.item_build == "Default BBC" and ctx.item_category == "default":
        bucket_build = _item_path_from_buckets(ctx)
        if bucket_build:
            ctx.item_build = bucket_build

    # Step 8: Parse shards
    shards = _parse_shards(ctx.shards)

    # Step 9: For each keystone, build a BuildOption
    options = []
    resolve_group = _find_resolve_group(guide_json.get("root", {})) if guide_json.get("root") else None

    for keystone_name in ctx.keystones:
        rune_template = rune_pages.get(keystone_name)
        if not rune_template:
            continue

        # Re-walk the resolve subtree with current_keystone set
        resolve_ctx = _Context(champion, enemy, matchup, guide_json)
        resolve_ctx.current_keystone = keystone_name
        resolve_ctx.resolve_code = ctx.resolve_code  # Start with tree-determined code

        if resolve_group:
            _walk_node(resolve_group, resolve_ctx)

        # Compute resolve overrides from the code
        resolve = _resolve_for_keystone(
            guide_json, enemy, keystone_name, resolve_ctx.resolve_code
        )

        # Apply resolve + shard overrides to rune template
        final_perks = _apply_resolve_overrides(rune_template, resolve, shards)
        final_perks = precision_secondary_adaptation(final_perks, rune_template["sub_style_id"], enemy)

        # Get item build template (keystone-dependent routing for Jax/Trynd/ranged AD)
        primary_build_name = _keystone_item_override(ctx.item_build, ctx.item_category, keystone_name, ctx)
        item_template = item_builds.get(primary_build_name)
        if not item_template:
            item_template = item_builds.get("Default BBC", {})
            primary_build_name = "Default BBC"

        skill_id = resolve_skill_order(enemy, keystone_name, tuple(ctx.tags))
        skill = get_skill_order(skill_id)

        # Item system v2 fields
        boot_rec = boot_recommendation(enemy, keystone_name, primary_build_name)
        fb_key = first_back_recommendation(enemy, primary_build_name)
        first_back = FIRST_BACK_ITEMS.get(fb_key, FIRST_BACK_ITEMS["default"])
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
        bo_note = build_order_note(primary_build_name, enemy)
        lg_note = late_game_note(primary_build_name)

        options.append(BuildOption(
            keystone=keystone_name,
            rune_page_name=keystone_name,
            primary_style_id=rune_template["primary_style_id"],
            sub_style_id=rune_template["sub_style_id"],
            selected_perk_ids=final_perks,
            item_build_name=primary_build_name,
            starter=list(item_template.get("starter", [])),
            boots=list(item_template.get("boots", [])),
            core=list(item_template.get("core", [])),
            situational=list(item_template.get("situational", [])),
            difficulty=ctx.difficulty,
            summoners=ctx.summoners,
            starter_info=ctx.starter_info,
            resolve_code=resolve["code"],
            shard_info=_shard_display(shards),
            reasoning=ctx.advice,
            special_note=ctx.special_note,
            item_build_description=item_template.get("description", ""),
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

    # Step 10: Add alternative builds from rune_build_compat
    if ctx.keystones and len(options) > 0:
        primary_keystone = ctx.keystones[0]
        compatible_builds = rune_build_compat.get(primary_keystone, [])
        primary_build_name = options[0].item_build_name

        for alt_build_name in compatible_builds:
            if alt_build_name == primary_build_name:
                continue
            if alt_build_name not in item_builds:
                continue

            # Only add first 2 alternatives to avoid clutter
            alt_count = sum(
                1 for o in options
                if o.keystone == primary_keystone and o.item_build_name != primary_build_name
            )
            if alt_count >= 2:
                break

            alt_template = item_builds[alt_build_name]
            rune_template = rune_pages[primary_keystone]

            # Re-walk resolve for this keystone
            resolve_ctx = _Context(champion, enemy, matchup, guide_json)
            resolve_ctx.current_keystone = primary_keystone
            resolve_ctx.resolve_code = ctx.resolve_code
            if resolve_group:
                _walk_node(resolve_group, resolve_ctx)
            resolve = _resolve_for_keystone(
                guide_json, enemy, primary_keystone, resolve_ctx.resolve_code
            )

            final_perks = _apply_resolve_overrides(rune_template, resolve, shards)
            final_perks = precision_secondary_adaptation(final_perks, rune_template["sub_style_id"], enemy)

            alt_skill_id = resolve_skill_order(enemy, primary_keystone, tuple(ctx.tags))
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
                primary_style_id=rune_template["primary_style_id"],
                sub_style_id=rune_template["sub_style_id"],
                selected_perk_ids=final_perks,
                item_build_name=alt_build_name,
                starter=list(alt_template.get("starter", [])),
                boots=list(alt_template.get("boots", [])),
                core=list(alt_template.get("core", [])),
                situational=list(alt_template.get("situational", [])),
                difficulty=ctx.difficulty,
                summoners=_resolve_summoners(ctx, matchup),
                starter_info=_resolve_starters(ctx, matchup),
                resolve_code=resolve["code"],
                shard_info=_shard_display(shards),
                reasoning=f"Alternative build: {alt_template.get('description', '')[:100]}",
                special_note=ctx.special_note,
                item_build_description=alt_template.get("description", ""),
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


# ---------------------------------------------------------------------------
# Summoner spell resolution (mirrors rules.py summoner_spells)
# ---------------------------------------------------------------------------

def _resolve_summoners(ctx: _Context, matchup: dict) -> str:
    """Resolve summoner spells from matchup data and buckets."""
    matchup_spells = matchup.get("summoner_spells", "Ghost/Ignite")
    exhaust_viable = matchup.get("exhaust_viable", False)
    enemy = ctx.enemy
    buckets = ctx.guide.get("data", {}).get("buckets", {})

    if matchup_spells and matchup_spells != "Ghost/Ignite":
        return matchup_spells

    exhaust_primary = buckets.get("EXHAUST_PRIMARY", [])
    exhaust_with_ghost = buckets.get("EXHAUST_WITH_GHOST", [])
    exhaust_secondary = buckets.get("EXHAUST_SECONDARY", [])

    if enemy in exhaust_primary:
        return "Exhaust/TP"
    elif enemy in exhaust_with_ghost:
        return "Exhaust/Ghost"
    elif enemy in exhaust_secondary or exhaust_viable:
        return "Exhaust viable (Ghost/Ignite default)"
    else:
        return "Ghost/Ignite"


# ---------------------------------------------------------------------------
# Starter item resolution (mirrors rules.py starter_items)
# ---------------------------------------------------------------------------

def _resolve_starters(ctx: _Context, matchup: dict) -> dict:
    """Resolve starter items from matchup data and buckets."""
    enemy = ctx.enemy
    buckets = ctx.guide.get("data", {}).get("buckets", {})

    if enemy in buckets.get("BAD_AD_MATCHUPS", []):
        return {
            "name": "Cloth Armor + Refillable",
            "note": "D-Blade into Cloth rush also viable",
        }
    elif enemy in buckets.get("AP_MELEE_CHAMPS", []):
        return {
            "name": "Long Sword + Refillable",
            "note": "D-Blade into Magic Mantle rush also works",
        }
    elif enemy in buckets.get("AP_POKE_CHAMPS", []):
        return {
            "name": "Doran's Shield",
            "note": "Into Magic Mantle on first recall. Second Wind mandatory.",
        }
    elif enemy in buckets.get("RANGED_AD_CHAMPS", []):
        return {
            "name": "Doran's Shield",
            "note": "Bramble Vest rush. Aery + Bramble trick for free poke.",
        }
    elif enemy in buckets.get("RANGED_AP_CHAMPS", []):
        return {
            "name": "Doran's Shield",
            "note": "E max with Eclipse & Shojin + Comet/Aery for poke.",
        }
    elif enemy in buckets.get("AD_TANK_AGGRO", []):
        return {
            "name": "Cloth Armor + Refillable",
            "note": "Rush Black Cleaver into Liandry.",
        }
    elif enemy in buckets.get("AP_TANK_CHAMPS", []):
        return {
            "name": "Doran's Shield",
            "note": "Into Cull + Black Cleaver.",
        }
    else:
        return {
            "name": "Doran's Blade + Health Potion",
            "note": "Standard start for most matchups.",
        }


# ---------------------------------------------------------------------------
# Item path from category (mirrors rules.py item_path)
# ---------------------------------------------------------------------------

def _item_category_to_build_name(category: str) -> str:
    """Convert item_category string to item build template name."""
    mapping = {
        "iceborn_cleaver": "Iceborn Cleaver",
        "titanic_breaker": "Titanic Breaker",
        "eclipse_poke": "Eclipse Poke",
        "sundered_sky": "Sundered Sky Rush",
        "liandry_shred": "Liandry Tank Shred",
        "vs_morde": "VS Morde",
        "vs_trynd_conq": "VS Trynd (Conqueror)",
        "vs_trynd_iceborn": "VS Trynd (Iceborn Old)",
        "vs_jax_iceborn": "VS Jax (Iceborn)",
        "vs_jax_shojin": "VS Jax (Shojin)",
        "vs_trundle": "VS Trundle",
        "vs_irelia": "VS Irelia",
        "vs_ranged": "VS Ranged Top",
        "default_titanic": "Default Titanic Path",
        "anti_ap": "Anti-AP",
    }
    return mapping.get(category, "Default BBC")


def _keystone_item_override(
    current_build: str,
    item_category: str,
    keystone: str,
    ctx: _Context,
) -> str:
    """Apply keystone-dependent item routing (mirrors rules.py item_path logic).

    Certain matchups have different item paths depending on keystone:
      - Jax: Grasp → Iceborn, non-Grasp → Shojin
      - Tryndamere: Grasp → Iceborn Old, non-Grasp → Conqueror
      - Ranged AD + Aery → VS Ranged Top (Bramble trick)
    """
    is_grasp = keystone.startswith("Grasp")

    # Jax: Grasp → Iceborn, non-Grasp → Shojin
    if item_category in ("vs_jax_iceborn", "vs_jax_shojin"):
        return "VS Jax (Iceborn)" if is_grasp else "VS Jax (Shojin)"

    # Tryndamere: Grasp → Iceborn Old, non-Grasp → Conqueror
    if item_category in ("vs_trynd_conq", "vs_trynd_iceborn"):
        return "VS Trynd (Iceborn Old)" if is_grasp else "VS Trynd (Conqueror)"

    # Ranged AD + Aery → VS Ranged Top (Bramble trick)
    if keystone == "Aery" and current_build == "Eclipse Poke":
        buckets = ctx.guide.get("data", {}).get("buckets", {})
        ranged_ad = buckets.get("RANGED_AD_CHAMPS", [])
        if ctx.enemy in ranged_ad:
            return "VS Ranged Top"

    return current_build


def _item_path_from_buckets(ctx: _Context) -> str | None:
    """Check bucket membership for item path (mirrors rules.py item_path fallback)."""
    enemy = ctx.enemy
    buckets = ctx.guide.get("data", {}).get("buckets", {})

    if enemy in buckets.get("SHEEN_ICEBORN_CHAMPS", []):
        return "Iceborn Cleaver"
    elif enemy in buckets.get("TIAMAT_TITANIC_CHAMPS", []):
        return "Titanic Breaker"
    elif enemy in buckets.get("ECLIPSE_POKE_CHAMPS", []):
        return "Eclipse Poke"
    elif enemy in buckets.get("SUNDERED_SKY_CHAMPS", []):
        return "Sundered Sky Rush"
    elif enemy in buckets.get("LIANDRY_SHRED_CHAMPS", []):
        return "Liandry Tank Shred"

    return None


# ---------------------------------------------------------------------------
# Multi-enemy recommendation (mirrors engine.py recommend_builds_multi)
# ---------------------------------------------------------------------------

def recommend_from_guide_multi(
    guide_json: dict,
    champion: str,
    enemies: list[dict],
) -> list[BuildOption]:
    """Averaged build recommendation across multiple potential enemies.

    Each enemy dict: {"name": str, "weight": float} where weight is top-lane
    probability (0.0-1.0).

    Scores keystones and item builds by how often they appear as the PRIMARY
    (first) recommendation, weighted by enemy probability. Returns merged
    BuildOption list with the top combo as primary plus 1-2 alternatives.
    """
    data = guide_json.get("data", {})
    item_builds = data.get("item_builds", {})

    if not enemies:
        return []

    # Sort enemies by weight descending
    enemies_sorted = sorted(enemies, key=lambda e: e["weight"], reverse=True)
    highest_weight_enemy = enemies_sorted[0]

    # Check low-confidence edge case
    low_confidence = all(e["weight"] < 0.10 for e in enemies)

    # Collect per-enemy build results and score keystones/item builds
    keystone_scores: dict[str, float] = {}
    item_build_scores: dict[str, float] = {}
    enemy_builds: dict[str, list[BuildOption]] = {}

    for enemy in enemies:
        name = enemy["name"]
        weight = enemy["weight"]
        builds = recommend_from_guide(guide_json, champion, name)
        enemy_builds[name] = builds

        if not builds:
            continue

        primary = builds[0]
        keystone_scores[primary.keystone] = keystone_scores.get(primary.keystone, 0.0) + weight
        item_build_scores[primary.item_build_name] = item_build_scores.get(primary.item_build_name, 0.0) + weight

    if not keystone_scores:
        return []

    # Find top keystone and top item build
    best_keystone = max(keystone_scores, key=keystone_scores.get)
    best_item_build = max(item_build_scores, key=item_build_scores.get)

    # Build reasoning string
    parts = [f"{e['name']} ({e['weight']:.0%})" for e in enemies_sorted]
    reasoning = "Averaged: " + ", ".join(parts)
    if low_confidence:
        reasoning += " [LOW CONFIDENCE -- all enemies <10% probability]"

    # Use highest-weight enemy's build data for resolve, shards, summoners, starter
    ref_builds = enemy_builds.get(highest_weight_enemy["name"], [])

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

    # Find item template for best item build
    best_item_template = item_builds.get(best_item_build, {})
    if not best_item_template:
        best_item_template = item_builds.get("Default BBC", {})
        best_item_build = "Default BBC"

    # Build primary recommendation
    primary_option = BuildOption(
        keystone=best_keystone,
        rune_page_name=best_keystone,
        primary_style_id=ref_option.primary_style_id,
        sub_style_id=ref_option.sub_style_id,
        selected_perk_ids=list(ref_option.selected_perk_ids),
        item_build_name=best_item_build,
        starter=list(best_item_template.get("starter", [])),
        boots=list(best_item_template.get("boots", [])),
        core=list(best_item_template.get("core", [])),
        situational=list(best_item_template.get("situational", [])),
        difficulty=ref_option.difficulty,
        summoners=ref_option.summoners,
        starter_info=ref_option.starter_info,
        resolve_code=ref_option.resolve_code,
        shard_info=ref_option.shard_info,
        reasoning=reasoning,
        special_note=ref_option.special_note,
        item_build_description=best_item_template.get("description", ""),
        skill_order_id=ref_option.skill_order_id,
        skill_order_name=ref_option.skill_order_name,
        skill_order_levels=list(ref_option.skill_order_levels),
        skill_order_max=list(ref_option.skill_order_max),
        skill_order_description=ref_option.skill_order_description,
        skill_order_condition=ref_option.skill_order_condition,
    )

    options = [primary_option]

    # Alt 1: same keystone, second-best item build
    alt_items = sorted(item_build_scores, key=item_build_scores.get, reverse=True)
    for alt_item_name in alt_items:
        if alt_item_name == best_item_build:
            continue
        alt_template = item_builds.get(alt_item_name)
        if not alt_template:
            continue
        options.append(BuildOption(
            keystone=best_keystone,
            rune_page_name=best_keystone,
            primary_style_id=ref_option.primary_style_id,
            sub_style_id=ref_option.sub_style_id,
            selected_perk_ids=list(ref_option.selected_perk_ids),
            item_build_name=alt_item_name,
            starter=list(alt_template.get("starter", [])),
            boots=list(alt_template.get("boots", [])),
            core=list(alt_template.get("core", [])),
            situational=list(alt_template.get("situational", [])),
            difficulty=ref_option.difficulty,
            summoners=ref_option.summoners,
            starter_info=ref_option.starter_info,
            resolve_code=ref_option.resolve_code,
            shard_info=ref_option.shard_info,
            reasoning=f"Alt item build ({alt_item_name}, score {item_build_scores[alt_item_name]:.0%})",
            special_note="",
            item_build_description=alt_template.get("description", ""),
            skill_order_id=ref_option.skill_order_id,
            skill_order_name=ref_option.skill_order_name,
            skill_order_levels=list(ref_option.skill_order_levels),
            skill_order_max=list(ref_option.skill_order_max),
            skill_order_description=ref_option.skill_order_description,
            skill_order_condition=ref_option.skill_order_condition,
        ))
        break  # Only 1 alt item build

    # Alt 2: second-best keystone with best item build
    alt_keystones = sorted(keystone_scores, key=keystone_scores.get, reverse=True)
    for alt_ks in alt_keystones:
        if alt_ks == best_keystone:
            continue
        if len(options) >= 3:
            break
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
            starter=list(best_item_template.get("starter", [])),
            boots=list(best_item_template.get("boots", [])),
            core=list(best_item_template.get("core", [])),
            situational=list(best_item_template.get("situational", [])),
            difficulty=alt_ref.difficulty,
            summoners=ref_option.summoners,
            starter_info=ref_option.starter_info,
            resolve_code=ref_option.resolve_code,
            shard_info=ref_option.shard_info,
            reasoning=f"Alt keystone ({alt_ks}, score {keystone_scores[alt_ks]:.0%})",
            special_note="",
            item_build_description=best_item_template.get("description", ""),
            skill_order_id=ref_option.skill_order_id,
            skill_order_name=ref_option.skill_order_name,
            skill_order_levels=list(ref_option.skill_order_levels),
            skill_order_max=list(ref_option.skill_order_max),
            skill_order_description=ref_option.skill_order_description,
            skill_order_condition=ref_option.skill_order_condition,
        ))
        break  # Only 1 alt keystone

    return options
