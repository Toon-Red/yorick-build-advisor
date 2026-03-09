"""Parity test: tree_executor must produce IDENTICAL results to engine.py for all matchups."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import recommend_builds, build_option_to_dict
from tree_executor import recommend_from_guide
from data.matchup_table import MATCHUP_TABLE
from tests.build_test_guide import build_guide_json


GUIDE = build_guide_json()


def _compare_options(engine_opts, tree_opts, enemy):
    """Compare two lists of BuildOption, return list of differences."""
    diffs = []

    if len(engine_opts) != len(tree_opts):
        diffs.append(
            f"  Count mismatch: engine={len(engine_opts)}, tree={len(tree_opts)}"
        )
        # Compare up to the shorter length
        n = min(len(engine_opts), len(tree_opts))
    else:
        n = len(engine_opts)

    for i in range(n):
        e = engine_opts[i]
        t = tree_opts[i]
        ed = build_option_to_dict(e)
        td = build_option_to_dict(t)

        for key in ed:
            if ed[key] != td[key]:
                diffs.append(
                    f"  [{i}] {key}: engine={ed[key]!r}, tree={td[key]!r}"
                )

    return diffs


def test_all_matchups_parity():
    """Every matchup must produce identical BuildOption lists."""
    failures = {}

    for enemy in sorted(MATCHUP_TABLE.keys()):
        engine_results = recommend_builds("Yorick", enemy)
        tree_results = recommend_from_guide(GUIDE, "Yorick", enemy)

        diffs = _compare_options(engine_results, tree_results, enemy)
        if diffs:
            failures[enemy] = diffs

    if failures:
        msg_parts = []
        for enemy, diffs in sorted(failures.items()):
            msg_parts.append(f"\n{enemy}:")
            msg_parts.extend(diffs)
        assert False, "Parity failures:" + "\n".join(msg_parts)


def test_jax_parity():
    """Spot check: Jax matchup must be identical."""
    engine_results = recommend_builds("Yorick", "Jax")
    tree_results = recommend_from_guide(GUIDE, "Yorick", "Jax")

    assert len(engine_results) == len(tree_results), (
        f"Jax: count mismatch engine={len(engine_results)} tree={len(tree_results)}"
    )

    for i, (e, t) in enumerate(zip(engine_results, tree_results)):
        ed = build_option_to_dict(e)
        td = build_option_to_dict(t)
        assert ed == td, f"Jax option [{i}] differs:\n  engine={ed}\n  tree={td}"


def test_irelia_parity():
    """Spot check: Irelia matchup must be identical."""
    engine_results = recommend_builds("Yorick", "Irelia")
    tree_results = recommend_from_guide(GUIDE, "Yorick", "Irelia")

    assert len(engine_results) == len(tree_results)
    for i, (e, t) in enumerate(zip(engine_results, tree_results)):
        ed = build_option_to_dict(e)
        td = build_option_to_dict(t)
        assert ed == td, f"Irelia option [{i}] differs"


def test_teemo_parity():
    """Spot check: Teemo matchup must be identical."""
    engine_results = recommend_builds("Yorick", "Teemo")
    tree_results = recommend_from_guide(GUIDE, "Yorick", "Teemo")

    assert len(engine_results) == len(tree_results)
    for i, (e, t) in enumerate(zip(engine_results, tree_results)):
        ed = build_option_to_dict(e)
        td = build_option_to_dict(t)
        assert ed == td, f"Teemo option [{i}] differs"


if __name__ == "__main__":
    # Quick standalone run
    total = 0
    passed = 0
    failed_enemies = []

    for enemy in sorted(MATCHUP_TABLE.keys()):
        total += 1
        engine_results = recommend_builds("Yorick", enemy)
        tree_results = recommend_from_guide(GUIDE, "Yorick", enemy)
        diffs = _compare_options(engine_results, tree_results, enemy)

        if diffs:
            failed_enemies.append(enemy)
            print(f"FAIL {enemy}:")
            for d in diffs:
                print(d)
        else:
            passed += 1

    print(f"\n{passed}/{total} matchups pass parity ({len(failed_enemies)} failures)")
    if failed_enemies:
        print(f"Failed: {', '.join(failed_enemies)}")
