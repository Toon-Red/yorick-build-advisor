"""Build a guide JSON from existing Python data for parity testing."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.matchup_table import MATCHUP_TABLE
from data.rune_pages import (
    RUNE_PAGES, SECOND_WIND, BONE_PLATING, REVITALIZE, UNFLINCHING,
)
from data.item_builds import ITEM_BUILDS
from data.rules import (
    RUNE_BUILD_COMPAT, RESOLVE_OVERRIDE_CHAMPS,
    RANGED_POKE_CHAMPS, BURST_CC_CHAMPS, BURST_CHAMPS,
    MS_SHARD_CHAMPS, ADAPTIVE_SHARD_CHAMPS,
    EXHAUST_PRIMARY, EXHAUST_WITH_GHOST, EXHAUST_SECONDARY,
    BAD_AD_MATCHUPS, AP_MELEE_CHAMPS, AP_POKE_CHAMPS,
    RANGED_AD_CHAMPS, RANGED_AP_CHAMPS, AD_TANK_AGGRO, AP_TANK_CHAMPS,
    SHEEN_ICEBORN_CHAMPS, TIAMAT_TITANIC_CHAMPS, ECLIPSE_POKE_CHAMPS,
    SUNDERED_SKY_CHAMPS, LIANDRY_SHRED_CHAMPS,
)


def build_guide_json() -> dict:
    """Build a complete guide JSON that encodes all the Python rules."""
    guide = {
        "schema_version": 2,
        "guide_id": "kampsycho-yorick-v1",
        "guide_name": "Kampsycho Guide",
        "champion": "Yorick",
        "author": "Kampsycho",
        "data": {
            "matchups": {},
            "rune_pages": {},
            "item_builds": {},
            "buckets": {},
            "rune_build_compat": {},
            "resolve_overrides": {},
            "resolve_mappings": {
                "primary": {
                    "A": {"row2": BONE_PLATING, "row3": REVITALIZE},
                    "B": {"row2": SECOND_WIND, "row3": REVITALIZE},
                    "C": {"row2": BONE_PLATING, "row3": UNFLINCHING},
                },
                "secondary": {
                    "A": {"row2": REVITALIZE},
                    "B": {"row2": SECOND_WIND},
                    "C": {"row2": BONE_PLATING},
                },
            },
        },
        "root": {
            "id": "n_0",
            "type": "ROOT",
            "label": "Yorick",
            "children": [
                {
                    "id": "n_1",
                    "type": "GROUP",
                    "label": "Resolve Adaptation",
                    "collapsed": False,
                    "children": [
                        {
                            "id": "n_2",
                            "type": "IF",
                            "condition": {
                                "field": "current_keystone",
                                "op": "starts_with",
                                "value": "Grasp",
                            },
                            "label": "Is Grasp?",
                            "children_true": [
                                {
                                    "id": "n_3",
                                    "type": "IF",
                                    "condition": {
                                        "field": "enemy_bucket",
                                        "op": "in",
                                        "value": ["RANGED_POKE_CHAMPS"],
                                    },
                                    "label": "Poke matchup?",
                                    "children_true": [
                                        {
                                            "id": "n_4",
                                            "type": "SET",
                                            "assignments": [
                                                {
                                                    "key": "resolve_code",
                                                    "value": "B",
                                                    "ref_type": "literal",
                                                }
                                            ],
                                            "children": [],
                                        }
                                    ],
                                    "children_false": [
                                        {
                                            "id": "n_5",
                                            "type": "IF",
                                            "condition": {
                                                "field": "enemy_bucket",
                                                "op": "in",
                                                "value": ["BURST_CC_CHAMPS"],
                                            },
                                            "label": "Burst/CC?",
                                            "children_true": [
                                                {
                                                    "id": "n_6",
                                                    "type": "SET",
                                                    "assignments": [
                                                        {
                                                            "key": "resolve_code",
                                                            "value": "C",
                                                            "ref_type": "literal",
                                                        }
                                                    ],
                                                    "children": [],
                                                }
                                            ],
                                            "children_false": [
                                                {
                                                    "id": "n_7",
                                                    "type": "SET",
                                                    "assignments": [
                                                        {
                                                            "key": "resolve_code",
                                                            "value": "A",
                                                            "ref_type": "literal",
                                                        }
                                                    ],
                                                    "children": [],
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                            "children_false": [
                                {
                                    "id": "n_8",
                                    "type": "IF",
                                    "condition": {
                                        "field": "enemy_bucket",
                                        "op": "in",
                                        "value": ["RANGED_POKE_CHAMPS"],
                                    },
                                    "label": "Poke matchup? (secondary)",
                                    "children_true": [
                                        {
                                            "id": "n_9",
                                            "type": "SET",
                                            "assignments": [
                                                {
                                                    "key": "resolve_code",
                                                    "value": "B",
                                                    "ref_type": "literal",
                                                }
                                            ],
                                            "children": [],
                                        }
                                    ],
                                    "children_false": [
                                        {
                                            "id": "n_10",
                                            "type": "IF",
                                            "condition": {
                                                "field": "enemy_bucket",
                                                "op": "in",
                                                "value": ["BURST_CHAMPS"],
                                            },
                                            "label": "Burst? (secondary)",
                                            "children_true": [
                                                {
                                                    "id": "n_11",
                                                    "type": "SET",
                                                    "assignments": [
                                                        {
                                                            "key": "resolve_code",
                                                            "value": "C",
                                                            "ref_type": "literal",
                                                        }
                                                    ],
                                                    "children": [],
                                                }
                                            ],
                                            "children_false": [
                                                {
                                                    "id": "n_12",
                                                    "type": "SET",
                                                    "assignments": [
                                                        {
                                                            "key": "resolve_code",
                                                            "value": "A",
                                                            "ref_type": "literal",
                                                        }
                                                    ],
                                                    "children": [],
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        },
    }

    # Fill matchups
    for name, info in MATCHUP_TABLE.items():
        guide["data"]["matchups"][name] = {
            "difficulty": info.difficulty,
            "keystones": list(info.keystones),
            "item_category": info.item_category,
            "tags": list(info.tags),
            "shard_override": info.shard_override,
            "exhaust_viable": info.exhaust_viable,
            "summoner_spells": info.summoner_spells,
            "special_note": info.special_note,
            "advice": info.advice,
        }

    # Fill rune pages
    for name, page in RUNE_PAGES.items():
        guide["data"]["rune_pages"][name] = {
            "name": page.name,
            "primary_style_id": page.primary_style_id,
            "sub_style_id": page.sub_style_id,
            "selected_perk_ids": list(page.selected_perk_ids),
            "description": page.description,
        }

    # Fill item builds
    for name, build in ITEM_BUILDS.items():
        guide["data"]["item_builds"][name] = {
            "name": build.name,
            "starter": list(build.starter),
            "boots": list(build.boots),
            "core": list(build.core),
            "situational": list(build.situational),
            "description": build.description,
        }

    # Fill buckets
    guide["data"]["buckets"] = {
        "RANGED_POKE_CHAMPS": sorted(RANGED_POKE_CHAMPS),
        "BURST_CC_CHAMPS": sorted(BURST_CC_CHAMPS),
        "BURST_CHAMPS": sorted(BURST_CHAMPS),
        "MS_SHARD_CHAMPS": sorted(MS_SHARD_CHAMPS),
        "ADAPTIVE_SHARD_CHAMPS": sorted(ADAPTIVE_SHARD_CHAMPS),
        "EXHAUST_PRIMARY": sorted(EXHAUST_PRIMARY),
        "EXHAUST_WITH_GHOST": sorted(EXHAUST_WITH_GHOST),
        "EXHAUST_SECONDARY": sorted(EXHAUST_SECONDARY),
        "BAD_AD_MATCHUPS": sorted(BAD_AD_MATCHUPS),
        "AP_MELEE_CHAMPS": sorted(AP_MELEE_CHAMPS),
        "AP_POKE_CHAMPS": sorted(AP_POKE_CHAMPS),
        "RANGED_AD_CHAMPS": sorted(RANGED_AD_CHAMPS),
        "RANGED_AP_CHAMPS": sorted(RANGED_AP_CHAMPS),
        "AD_TANK_AGGRO": sorted(AD_TANK_AGGRO),
        "AP_TANK_CHAMPS": sorted(AP_TANK_CHAMPS),
        "SHEEN_ICEBORN_CHAMPS": sorted(SHEEN_ICEBORN_CHAMPS),
        "TIAMAT_TITANIC_CHAMPS": sorted(TIAMAT_TITANIC_CHAMPS),
        "ECLIPSE_POKE_CHAMPS": sorted(ECLIPSE_POKE_CHAMPS),
        "SUNDERED_SKY_CHAMPS": sorted(SUNDERED_SKY_CHAMPS),
        "LIANDRY_SHRED_CHAMPS": sorted(LIANDRY_SHRED_CHAMPS),
    }

    # Fill rune_build_compat
    guide["data"]["rune_build_compat"] = dict(RUNE_BUILD_COMPAT)

    # Fill resolve_overrides
    for champ, ov in RESOLVE_OVERRIDE_CHAMPS.items():
        guide["data"]["resolve_overrides"][champ] = dict(ov)

    return guide


if __name__ == "__main__":
    guide = build_guide_json()
    out_path = Path(__file__).parent.parent / "test_guide.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(guide, f, indent=2)
    print(f"Guide JSON written to {out_path}")
    print(f"  Matchups: {len(guide['data']['matchups'])}")
    print(f"  Rune pages: {len(guide['data']['rune_pages'])}")
    print(f"  Item builds: {len(guide['data']['item_builds'])}")
    print(f"  Buckets: {len(guide['data']['buckets'])}")
