"""Tests for the decision tree engine.

Verifies that the engine produces correct builds for known matchups
based on the Kampsycho guide.
"""

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import recommend_builds, BuildOption
from data.matchup_table import MATCHUP_TABLE, get_matchup
from data.rune_pages import RUNE_PAGES, SHARD_MS, SHARD_AF, SHARD_HP, SHARD_AS, SHARD_TENACITY, SECOND_WIND, UNFLINCHING, BONE_PLATING
from data.item_builds import ITEM_BUILDS


# ============================================================================
# Core Engine Tests
# ============================================================================

class TestEngineBasics:
    def test_all_matchups_return_results(self):
        """Every matchup in the table should produce at least 1 build option."""
        for enemy in MATCHUP_TABLE:
            results = recommend_builds("Yorick", enemy)
            assert len(results) >= 1, f"{enemy}: no results returned"

    def test_all_results_have_9_perks(self):
        """Every build option should have exactly 9 perk IDs."""
        for enemy in MATCHUP_TABLE:
            results = recommend_builds("Yorick", enemy)
            for r in results:
                assert len(r.selected_perk_ids) == 9, (
                    f"{enemy}/{r.keystone}: got {len(r.selected_perk_ids)} perks"
                )

    def test_all_results_have_valid_rune_ids(self):
        """All rune IDs should be positive integers."""
        for enemy in MATCHUP_TABLE:
            results = recommend_builds("Yorick", enemy)
            for r in results:
                for pid in r.selected_perk_ids:
                    assert isinstance(pid, int) and pid > 0, (
                        f"{enemy}/{r.keystone}: invalid perk ID {pid}"
                    )

    def test_all_results_have_valid_item_ids(self):
        """All item IDs should be positive integers."""
        for enemy in MATCHUP_TABLE:
            results = recommend_builds("Yorick", enemy)
            for r in results:
                for iid in r.core:
                    assert isinstance(iid, int) and iid > 0, (
                        f"{enemy}/{r.keystone}: invalid core item ID {iid}"
                    )

    def test_unknown_enemy_returns_fallback(self):
        """Unknown enemies should fall back to archetype defaults."""
        results = recommend_builds("Yorick", "Bard")
        assert len(results) >= 1
        assert results[0].difficulty in ("Easy", "Medium", "Advanced", "HARD", "EXTREME")


# ============================================================================
# Specific Matchup Tests (Verification Criteria from Plan)
# ============================================================================

class TestJaxMatchup:
    def test_jax_returns_correct_keystones(self):
        results = recommend_builds("Yorick", "Jax")
        keystones = [r.keystone for r in results]
        assert "Grasp-1" in keystones
        assert "Comet" in keystones
        assert "Aery" in keystones

    def test_jax_gets_ms_shard(self):
        results = recommend_builds("Yorick", "Jax")
        for r in results:
            assert r.selected_perk_ids[7] == SHARD_MS, (
                f"Jax/{r.keystone}: expected MS shard, got {r.selected_perk_ids[7]}"
            )

    def test_jax_difficulty_is_hard(self):
        results = recommend_builds("Yorick", "Jax")
        assert results[0].difficulty == "HARD"

    def test_jax_primary_build_is_iceborn(self):
        results = recommend_builds("Yorick", "Jax")
        assert results[0].item_build_name == "Iceborn Cleaver"

    def test_jax_exhaust_mentioned(self):
        results = recommend_builds("Yorick", "Jax")
        assert "Exhaust" in results[0].summoners


class TestWarwickMatchup:
    def test_warwick_returns_comet_and_conqueror(self):
        results = recommend_builds("Yorick", "Warwick")
        keystones = [r.keystone for r in results]
        assert "Comet" in keystones
        assert "Conqueror" in keystones

    def test_warwick_difficulty_is_extreme(self):
        results = recommend_builds("Yorick", "Warwick")
        assert results[0].difficulty == "EXTREME"

    def test_warwick_default_summoners(self):
        results = recommend_builds("Yorick", "Warwick")
        assert "Ghost/Ignite" in results[0].summoners


class TestTryndamereMatchup:
    def test_tryndamere_gets_exhaust(self):
        results = recommend_builds("Yorick", "Tryndamere")
        assert "Exhaust" in results[0].summoners

    def test_tryndamere_gets_ms_shard(self):
        results = recommend_builds("Yorick", "Tryndamere")
        for r in results:
            assert r.selected_perk_ids[7] == SHARD_MS

    def test_tryndamere_difficulty_extreme(self):
        results = recommend_builds("Yorick", "Tryndamere")
        assert results[0].difficulty == "EXTREME"

    def test_tryndamere_has_multiple_options(self):
        results = recommend_builds("Yorick", "Tryndamere")
        assert len(results) >= 4  # Grasp-2, Grasp-1, Grasp-3, Conqueror


class TestIreliaMatchup:
    def test_irelia_ban_note(self):
        results = recommend_builds("Yorick", "Irelia")
        assert results[0].special_note == "BAN HER"

    def test_irelia_difficulty_extreme(self):
        results = recommend_builds("Yorick", "Irelia")
        assert results[0].difficulty == "EXTREME"

    def test_irelia_gets_exhaust(self):
        results = recommend_builds("Yorick", "Irelia")
        assert "Exhaust" in results[0].summoners

    def test_irelia_iceborn_build(self):
        results = recommend_builds("Yorick", "Irelia")
        assert results[0].item_build_name == "Iceborn Cleaver"


class TestTeemoMatchup:
    def test_teemo_gets_aery_or_comet(self):
        results = recommend_builds("Yorick", "Teemo")
        keystones = [r.keystone for r in results]
        assert "Aery" in keystones or "Comet" in keystones

    def test_teemo_eclipse_poke_build(self):
        results = recommend_builds("Yorick", "Teemo")
        assert results[0].item_build_name == "Eclipse Poke"


class TestShardOverrides:
    def test_jax_ms_shard(self):
        results = recommend_builds("Yorick", "Jax")
        assert results[0].selected_perk_ids[7] == SHARD_MS

    def test_kayle_adaptive_shard(self):
        results = recommend_builds("Yorick", "Kayle")
        assert results[0].selected_perk_ids[7] == SHARD_AF

    def test_nasus_adaptive_shard(self):
        results = recommend_builds("Yorick", "Nasus")
        assert results[0].selected_perk_ids[7] == SHARD_AF

    def test_aatrox_default_hp_shard(self):
        results = recommend_builds("Yorick", "Aatrox")
        assert results[0].selected_perk_ids[7] == SHARD_HP

    def test_yone_ms_shard(self):
        results = recommend_builds("Yorick", "Yone")
        assert results[0].selected_perk_ids[7] == SHARD_MS

    def test_all_matchups_have_as_shard_first(self):
        """Attack Speed shard should always be first."""
        for enemy in MATCHUP_TABLE:
            results = recommend_builds("Yorick", enemy)
            for r in results:
                assert r.selected_perk_ids[6] == SHARD_AS, (
                    f"{enemy}/{r.keystone}: shard1 should be AS"
                )


class TestResolveAdaptation:
    def test_ranged_enemy_gets_second_wind(self):
        """Ranged enemies should trigger Second Wind (B code)."""
        from data.rune_pages import SECOND_WIND
        results = recommend_builds("Yorick", "Teemo")
        # Aery is Sorcery primary → resolve secondary → slot 5 should be Second Wind
        aery_result = [r for r in results if r.keystone == "Aery"]
        if aery_result:
            assert aery_result[0].resolve_code == "B"

    def test_burst_enemy_gets_bone_plating(self):
        """Burst enemies should trigger Bone Plating (C code)."""
        results = recommend_builds("Yorick", "Riven")
        grasp_result = [r for r in results if r.keystone.startswith("Grasp")]
        if grasp_result:
            assert grasp_result[0].resolve_code == "C"


class TestItemPaths:
    def test_jax_gets_iceborn(self):
        results = recommend_builds("Yorick", "Jax")
        assert results[0].item_build_name == "Iceborn Cleaver"

    def test_mundo_gets_liandry(self):
        results = recommend_builds("Yorick", "Dr. Mundo")
        build_names = [r.item_build_name for r in results]
        assert "Liandry Tank Shred" in build_names

    def test_teemo_gets_eclipse(self):
        results = recommend_builds("Yorick", "Teemo")
        assert results[0].item_build_name == "Eclipse Poke"

    def test_jayce_gets_sundered_sky(self):
        results = recommend_builds("Yorick", "Jayce")
        build_names = [r.item_build_name for r in results]
        assert "Sundered Sky Rush" in build_names

    def test_mordekaiser_gets_vs_morde(self):
        results = recommend_builds("Yorick", "Mordekaiser")
        build_names = [r.item_build_name for r in results]
        assert "VS Morde" in build_names


# ============================================================================
# Video Audit Bug Fix Tests
# ============================================================================

class TestVideoAuditFixes:
    """Tests for the 7 bugs found during video transcript audit."""

    def test_yasuo_gets_second_wind(self):
        """Bug #1: Yasuo should get resolve B (Second Wind) — video says 'Grasp-B'."""
        from data.rules import resolve_adaptation
        r = resolve_adaptation("Grasp-1", "Yasuo")
        assert r["code"] == "B"
        assert r["row2"] == SECOND_WIND

    def test_fiora_nongrasp_gets_second_wind(self):
        """Bug #2: Fiora should get Second Wind when on non-Grasp keystone."""
        from data.rules import resolve_adaptation
        r = resolve_adaptation("Conqueror", "Fiora")
        assert r["code"] == "B"
        assert r["row2"] == SECOND_WIND

    def test_volibear_gets_second_wind_plus_unflinching(self):
        """Bug #3: Volibear needs special resolve combo (Second Wind + Unflinching)."""
        from data.rules import resolve_adaptation
        r = resolve_adaptation("Grasp-2", "Volibear")
        assert r["row2"] == SECOND_WIND
        assert r["row3"] == UNFLINCHING

    def test_riven_gets_exhaust_ghost(self):
        """Bug #4: Riven should get Exhaust/Ghost, not Exhaust/TP."""
        from data.rules import summoner_spells
        assert summoner_spells("Riven") == "Exhaust/Ghost"

    def test_renekton_gets_exhaust_ghost(self):
        """Bug #4b: Renekton should get Exhaust/Ghost, not Exhaust/TP."""
        from data.rules import summoner_spells
        assert summoner_spells("Renekton") == "Exhaust/Ghost"

    def test_tryndamere_still_gets_exhaust_tp(self):
        """Tryndamere should still get Exhaust/TP (unchanged)."""
        from data.rules import summoner_spells
        assert summoner_spells("Tryndamere") == "Exhaust/TP"

    def test_gangplank_has_aery(self):
        """Bug #5: Gangplank should have Aery as a keystone option."""
        results = recommend_builds("Yorick", "Gangplank")
        keystones = [r.keystone for r in results]
        assert "Aery" in keystones

    def test_nocturne_has_hob(self):
        """Bug #6: Nocturne should have Hail of Blades as a keystone option."""
        results = recommend_builds("Yorick", "Nocturne")
        keystones = [r.keystone for r in results]
        assert "Hail of Blades" in keystones

    def test_urgot_has_aery(self):
        """Bug #7: Urgot should have Aery as a keystone option."""
        results = recommend_builds("Yorick", "Urgot")
        keystones = [r.keystone for r in results]
        assert "Aery" in keystones


# ============================================================================
# Update Check Tests
# ============================================================================

class TestUpdateCheck:
    def test_is_newer_detects_update(self):
        from updater import is_newer
        assert is_newer("1.1.0", "1.0.0") is True
        assert is_newer("2.0.0", "1.9.9") is True
        assert is_newer("1.0.1", "1.0.0") is True

    def test_is_newer_same_version(self):
        from updater import is_newer
        assert is_newer("1.0.0", "1.0.0") is False

    def test_is_newer_older_version(self):
        from updater import is_newer
        assert is_newer("1.0.0", "1.1.0") is False


# ============================================================================
# Titlebar / UI Tests
# ============================================================================

class TestNoCustomTitlebar:
    def test_no_custom_titlebar_in_index(self):
        """index.html should not have custom titlebar (Edge app mode provides one)."""
        from pathlib import Path
        html = (Path(__file__).parent.parent / "static" / "index.html").read_text()
        assert 'class="titlebar"' not in html

    def test_no_custom_titlebar_in_flow(self):
        """flow.html should not have custom titlebar (Edge app mode provides one)."""
        from pathlib import Path
        html = (Path(__file__).parent.parent / "static" / "flow.html").read_text()
        assert 'class="titlebar"' not in html
