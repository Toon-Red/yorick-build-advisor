"""Build the complete decision tree JSON encoding ALL engine logic."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def build_full_tree():
    n = [0]

    def nid():
        r = f"n_{n[0]}"
        n[0] += 1
        return r

    def set_node(key, value, ref_type="literal"):
        return {
            "id": nid(), "type": "SET",
            "assignments": [{"key": key, "value": value, "ref_type": ref_type}],
            "children": [],
        }

    def if_node(field, op, value, label, true_children, false_children):
        return {
            "id": nid(), "type": "IF",
            "condition": {"field": field, "op": op, "value": value},
            "label": label,
            "children_true": true_children,
            "children_false": false_children,
        }

    def switch_node(field, label, cases):
        return {
            "id": nid(), "type": "SWITCH",
            "field": field, "label": label,
            "cases": cases,
        }

    def case(label, match, children):
        return {"label": label, "match": match, "children": children}

    def group(label, children):
        return {
            "id": nid(), "type": "GROUP",
            "label": label, "collapsed": False,
            "children": children,
        }

    # ============================================================
    # GROUP 1: Summoner Spells
    # ============================================================
    g1 = group("Summoner Spells", [
        if_node("matchup_summoner_spells", "is_not_null", None,
                "Matchup has spell override?",
                true_children=[
                    set_node("summoners", "matchup.summoner_spells", "lookup"),
                ],
                false_children=[
                    if_node("enemy_bucket", "in", ["EXHAUST_PRIMARY"],
                            "Exhaust primary? (Tryndamere)",
                            true_children=[set_node("summoners", "Exhaust/TP")],
                            false_children=[
                                if_node("enemy_bucket", "in", ["EXHAUST_WITH_GHOST"],
                                        "Exhaust + Ghost? (Riven, Renekton)",
                                        true_children=[set_node("summoners", "Exhaust/Ghost")],
                                        false_children=[
                                            if_node("enemy_bucket", "in", ["EXHAUST_SECONDARY"],
                                                    "Exhaust viable? (Yasuo, Yone, Jax...)",
                                                    true_children=[set_node("summoners", "Exhaust viable (Ghost/Ignite default)")],
                                                    false_children=[set_node("summoners", "Ghost/Ignite")],
                                            ),
                                        ],
                                ),
                            ],
                    ),
                ],
        ),
    ])

    # ============================================================
    # GROUP 2: Resolve Adaptation
    # ============================================================
    # Grasp primary branch (2 resolve slots)
    grasp_branch = if_node("enemy_bucket", "in", ["RANGED_POKE_CHAMPS"],
        "Poke matchup?",
        true_children=[set_node("resolve_code", "B")],
        false_children=[
            if_node("enemy_bucket", "in", ["BURST_CC_CHAMPS"],
                    "Burst/CC?",
                    true_children=[set_node("resolve_code", "C")],
                    false_children=[set_node("resolve_code", "A")],
            ),
        ],
    )

    # Non-Grasp secondary branch (1 resolve slot)
    secondary_branch = if_node("enemy_bucket", "in", ["RANGED_POKE_CHAMPS"],
        "Poke matchup? (secondary)",
        true_children=[set_node("resolve_code", "B")],
        false_children=[
            if_node("enemy_bucket", "in", ["BURST_CHAMPS"],
                    "Burst? (secondary)",
                    true_children=[set_node("resolve_code", "C")],
                    false_children=[set_node("resolve_code", "A")],
            ),
        ],
    )

    g2 = group("Resolve Adaptation", [
        if_node("enemy_has_resolve_override", "eq", True,
                "Has per-champ resolve override? (e.g. Volibear)",
                true_children=[set_node("resolve_code", "override")],
                false_children=[
                    if_node("current_keystone", "starts_with", "Grasp",
                            "Is Grasp? (primary = 2 slots)",
                            true_children=[grasp_branch],
                            false_children=[secondary_branch],
                    ),
                ],
        ),
    ])

    # ============================================================
    # GROUP 3: Shard Selection
    # ============================================================
    g3 = group("Shard Selection", [
        if_node("matchup_shard_override", "is_not_null", None,
                "Matchup has shard override?",
                true_children=[set_node("shard_override", "matchup.shard_override", "lookup")],
                false_children=[
                    switch_node("enemy_bucket", "Shard by enemy type", [
                        case("MS champs (Jax, Tryndamere, Yone...)", "MS_SHARD_CHAMPS",
                             [set_node("shards", "AS / MS / Tenacity")]),
                        case("Adaptive champs (Vayne, Gwen, Kayle...)", "ADAPTIVE_SHARD_CHAMPS",
                             [set_node("shards", "AS / AF / Tenacity")]),
                        case("Default", "*",
                             [set_node("shards", "AS / HP / Tenacity")]),
                    ]),
                ],
        ),
    ])

    # ============================================================
    # GROUP 4: Starter Items
    # ============================================================
    g4 = group("Starter Items", [
        switch_node("enemy_bucket", "Starter by enemy type", [
            case("Bad AD (Riven, Jax, Irelia...)", "BAD_AD_MATCHUPS",
                 [set_node("starter_items", "Cloth Armor + Refillable")]),
            case("AP Melee (Gwen, Morde, Sylas)", "AP_MELEE_CHAMPS",
                 [set_node("starter_items", "Long Sword + Refillable")]),
            case("AP Poke (Teemo, Gragas...)", "AP_POKE_CHAMPS",
                 [set_node("starter_items", "Doran's Shield")]),
            case("Ranged AD (Vayne, Quinn...)", "RANGED_AD_CHAMPS",
                 [set_node("starter_items", "Doran's Shield")]),
            case("Ranged AP (Aurora, Akali...)", "RANGED_AP_CHAMPS",
                 [set_node("starter_items", "Doran's Shield")]),
            case("AD Tank (Shen, Sion)", "AD_TANK_AGGRO",
                 [set_node("starter_items", "Cloth Armor + Refillable")]),
            case("AP Tank (Malphite, Ornn...)", "AP_TANK_CHAMPS",
                 [set_node("starter_items", "Doran's Shield")]),
            case("Default", "*",
                 [set_node("starter_items", "Doran's Blade + HP Pot")]),
        ]),
    ])

    # ============================================================
    # GROUP 5: Item Path
    # ============================================================
    g5 = group("Item Path", [
        if_node("matchup_item_category", "is_not_null", None,
                "Matchup has item category override?",
                true_children=[set_node("item_build", "matchup.item_category", "lookup")],
                false_children=[
                    switch_node("enemy_bucket", "Item path by enemy type", [
                        case("Sheen/Iceborn (Jax, Fiora, Riven...)", "SHEEN_ICEBORN_CHAMPS",
                             [set_node("item_build", "Iceborn Cleaver")]),
                        case("Tiamat/Titanic (Tryndamere, Trundle...)", "TIAMAT_TITANIC_CHAMPS",
                             [set_node("item_build", "Titanic Breaker")]),
                        case("Eclipse Poke (Teemo, Quinn...)", "ECLIPSE_POKE_CHAMPS",
                             [set_node("item_build", "Eclipse Poke")]),
                        case("Sundered Sky (Jayce, Gragas...)", "SUNDERED_SKY_CHAMPS",
                             [set_node("item_build", "Sundered Sky Rush")]),
                        case("Liandry Shred (Cho, Mundo, Sion...)", "LIANDRY_SHRED_CHAMPS",
                             [set_node("item_build", "Liandry Tank Shred")]),
                        case("Default", "*",
                             [set_node("item_build", "Default BBC")]),
                    ]),
                ],
        ),
    ])

    root = {
        "id": "n_0",
        "type": "ROOT",
        "label": "Yorick",
        "children": [g1, g2, g3, g4, g5],
    }

    print(f"Total nodes: {n[0]}")
    print(f"Groups: {len(root['children'])}")
    for c in root["children"]:
        print(f"  - {c['label']}")
    return root


if __name__ == "__main__":
    tree = build_full_tree()

    # Now update the guide JSON with the full tree
    guide_path = Path(__file__).parent.parent / "data" / "guides" / "kampsycho_yorick.json"
    if guide_path.exists():
        with open(guide_path, "r") as f:
            guide = json.load(f)
        guide["root"] = tree
        with open(guide_path, "w") as f:
            json.dump(guide, f, indent=2)
        print(f"\nUpdated {guide_path.name} with full tree")
    else:
        print(f"\nGuide file not found at {guide_path}")
