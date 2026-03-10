"""Tests for multi-profile execution, guide manager, and API contract.

Covers:
- Guide manager CRUD (list, load, save, delete, import/export, active guide)
- Multi-profile API response structure (/api/build/query returns profiles[])
- Legacy fallback when no guides exist for a champion
- Tree executor Context.set mapping (starter_items → starter_info)
- Frontend data contract (profiles have required fields, options have required fields)
"""

import sys
import json
import copy
import uuid
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient

import guide_manager
from tree_executor import recommend_from_guide, _Context
from engine import recommend_builds, build_option_to_dict
from data.matchup_table import MATCHUP_TABLE, get_matchup


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

GUIDES_DIR = guide_manager.GUIDES_DIR


@pytest.fixture
def _backup_guides(tmp_path):
    """Backup and restore the guides directory around each test."""
    backup = tmp_path / "guides_backup"
    if GUIDES_DIR.exists():
        shutil.copytree(GUIDES_DIR, backup)
    yield
    # Restore
    if GUIDES_DIR.exists():
        shutil.rmtree(GUIDES_DIR)
    if backup.exists():
        shutil.copytree(backup, GUIDES_DIR)
    else:
        GUIDES_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def sample_guide():
    """A minimal valid guide for testing."""
    return {
        "guide_id": f"test-guide-{uuid.uuid4().hex[:6]}",
        "guide_name": "Test Guide",
        "champion": "Yorick",
        "author": "Tester",
        "root": {"id": "n_0", "type": "ROOT", "label": "Yorick", "children": []},
        "data": {
            "matchups": {
                "Jax": {
                    "difficulty": "HARD",
                    "keystones": ["Grasp-1", "Comet"],
                    "item_category": "sheen_iceborn",
                    "shard_override": "MS",
                    "exhaust_viable": True,
                }
            },
            "rune_pages": {},
            "item_builds": {},
            "buckets": {},
        },
    }


@pytest.fixture
def client():
    """FastAPI test client."""
    from app import app
    return TestClient(app)


# ============================================================================
# Guide Manager Unit Tests
# ============================================================================

class TestGuideManagerList:
    def test_list_guides_returns_list(self):
        result = guide_manager.list_guides()
        assert isinstance(result, list)

    def test_list_guides_has_kampsycho(self):
        """The Kampsycho guide should exist by default."""
        result = guide_manager.list_guides()
        names = [g["guide_name"] for g in result]
        assert any("Kampsycho" in n for n in names)

    def test_list_guides_for_yorick(self):
        result = guide_manager.list_guides_for_champion("Yorick")
        assert len(result) >= 1
        for g in result:
            assert g["champion"] == "Yorick"

    def test_list_guides_for_unknown_champion(self):
        result = guide_manager.list_guides_for_champion("Aatrox")
        assert result == []

    def test_list_guides_metadata_fields(self):
        """Each guide metadata should have required fields."""
        result = guide_manager.list_guides()
        for g in result:
            assert "guide_id" in g
            assert "guide_name" in g
            assert "champion" in g
            assert "author" in g
            assert "file" in g
            assert "matchup_count" in g
            assert isinstance(g["matchup_count"], int)


class TestGuideManagerLoad:
    def test_load_kampsycho_guide(self):
        guides = guide_manager.list_guides_for_champion("Yorick")
        assert len(guides) >= 1
        guide = guide_manager.load_guide(guides[0]["guide_id"])
        assert guide is not None
        assert "root" in guide
        assert "data" in guide

    def test_load_nonexistent_guide(self):
        result = guide_manager.load_guide("nonexistent-guide-id-xyz")
        assert result is None

    def test_loaded_guide_has_tree(self):
        guides = guide_manager.list_guides_for_champion("Yorick")
        guide = guide_manager.load_guide(guides[0]["guide_id"])
        root = guide["root"]
        assert root["type"] == "ROOT"
        assert len(root["children"]) >= 1


class TestGuideManagerCRUD:
    def test_save_and_load(self, _backup_guides, sample_guide):
        guide_id = guide_manager.save_guide(sample_guide)
        loaded = guide_manager.load_guide(guide_id)
        assert loaded is not None
        assert loaded["guide_name"] == "Test Guide"
        assert loaded["author"] == "Tester"

    def test_save_adds_timestamps(self, _backup_guides, sample_guide):
        guide_id = guide_manager.save_guide(sample_guide)
        loaded = guide_manager.load_guide(guide_id)
        assert "created_at" in loaded
        assert "updated_at" in loaded

    def test_delete_guide(self, _backup_guides, sample_guide):
        guide_id = guide_manager.save_guide(sample_guide)
        assert guide_manager.load_guide(guide_id) is not None
        deleted = guide_manager.delete_guide(guide_id)
        assert deleted is True
        assert guide_manager.load_guide(guide_id) is None

    def test_delete_nonexistent(self):
        deleted = guide_manager.delete_guide("nonexistent-guide-xyz")
        assert deleted is False

    def test_import_guide(self, _backup_guides, sample_guide):
        guide_id = guide_manager.import_guide(sample_guide)
        loaded = guide_manager.load_guide(guide_id)
        assert loaded is not None
        assert loaded["champion"] == "Yorick"

    def test_import_guide_invalid_format(self, _backup_guides):
        with pytest.raises(ValueError, match="missing"):
            guide_manager.import_guide({"name": "bad"})

    def test_import_duplicate_gets_new_id(self, _backup_guides, sample_guide):
        id1 = guide_manager.save_guide(sample_guide)
        # Import same guide again — should get a different ID
        guide_copy = copy.deepcopy(sample_guide)
        id2 = guide_manager.import_guide(guide_copy)
        assert id1 != id2

    def test_export_guide(self, _backup_guides, sample_guide):
        guide_id = guide_manager.save_guide(sample_guide)
        exported = guide_manager.export_guide(guide_id)
        assert exported is not None
        assert exported["guide_id"] == guide_id
        assert "root" in exported
        assert "data" in exported

    def test_export_nonexistent(self):
        result = guide_manager.export_guide("nonexistent-xyz")
        assert result is None


class TestGuideManagerActiveGuide:
    def test_set_and_get_active(self, _backup_guides, sample_guide):
        guide_id = guide_manager.save_guide(sample_guide)
        guide_manager.set_active_guide("Yorick", guide_id)
        assert guide_manager.get_active_guide_id("Yorick") == guide_id

    def test_get_active_guide_loads(self, _backup_guides, sample_guide):
        guide_id = guide_manager.save_guide(sample_guide)
        guide_manager.set_active_guide("Yorick", guide_id)
        guide = guide_manager.get_active_guide("Yorick")
        assert guide is not None
        assert guide["guide_id"] == guide_id

    def test_active_fallback_to_first(self):
        """If no active is set, get_active_guide returns the first available."""
        guide = guide_manager.get_active_guide("Yorick")
        assert guide is not None  # Kampsycho guide exists

    def test_active_returns_none_for_unknown_champ(self):
        guide = guide_manager.get_active_guide("Aatrox")
        assert guide is None


# ============================================================================
# Tree Executor — Context.set Mapping Tests
# ============================================================================

class TestContextSetMapping:
    def test_starter_items_maps_to_starter_info(self):
        """Setting 'starter_items' should populate starter_info dict."""
        ctx = _Context("Yorick", "Jax", {}, {})
        ctx.set("starter_items", "Cloth Armor + Refillable")
        assert ctx.starter_info["name"] == "Cloth Armor + Refillable"
        assert isinstance(ctx.starter_info, dict)

    def test_direct_starter_info_still_works(self):
        ctx = _Context("Yorick", "Jax", {}, {})
        ctx.set("starter_info", {"name": "Doran's Shield", "note": "test"})
        assert ctx.starter_info["name"] == "Doran's Shield"

    def test_summoners_set(self):
        ctx = _Context("Yorick", "Jax", {}, {})
        ctx.set("summoners", "Exhaust/Ghost")
        assert ctx.summoners == "Exhaust/Ghost"

    def test_resolve_code_set(self):
        ctx = _Context("Yorick", "Jax", {}, {})
        ctx.set("resolve_code", "B")
        assert ctx.resolve_code == "B"

    def test_item_build_set(self):
        ctx = _Context("Yorick", "Jax", {}, {})
        ctx.set("item_build", "Iceborn Cleaver")
        assert ctx.item_build == "Iceborn Cleaver"

    def test_shards_set(self):
        ctx = _Context("Yorick", "Jax", {}, {})
        ctx.set("shards", "AS / MS / Tenacity")
        assert ctx.shards == "AS / MS / Tenacity"

    def test_context_defaults(self):
        """Verify all defaults are sensible."""
        ctx = _Context("Yorick", "Jax", {}, {})
        assert ctx.resolve_code == "A"
        assert ctx.summoners == "Ghost/Ignite"
        assert ctx.item_build == "Default BBC"
        assert ctx.shards == "AS / HP / Tenacity"
        assert ctx.starter_info["name"] == "Doran's Blade + Health Potion"


# ============================================================================
# Multi-Profile API Contract Tests
# ============================================================================

class TestMultiProfileAPI:
    def test_query_returns_profiles_array(self, client):
        resp = client.post("/api/build/query", json={"champion": "Yorick", "enemy": "Jax"})
        assert resp.status_code == 200
        data = resp.json()
        assert "profiles" in data
        assert isinstance(data["profiles"], list)
        assert len(data["profiles"]) >= 1

    def test_query_has_profile_count(self, client):
        resp = client.post("/api/build/query", json={"champion": "Yorick", "enemy": "Jax"})
        data = resp.json()
        assert data["profile_count"] == len(data["profiles"])

    def test_query_has_champion_enemy_difficulty(self, client):
        resp = client.post("/api/build/query", json={"champion": "Yorick", "enemy": "Jax"})
        data = resp.json()
        assert data["champion"] == "Yorick"
        assert data["enemy"] == "Jax"
        assert data["difficulty"] == "HARD"

    def test_query_irelia_has_special_note(self, client):
        resp = client.post("/api/build/query", json={"champion": "Yorick", "enemy": "Irelia"})
        data = resp.json()
        assert data["special_note"] == "BAN HER"

    def test_profile_has_required_fields(self, client):
        """Each profile must have guide_id, guide_name, author, options, count."""
        resp = client.post("/api/build/query", json={"champion": "Yorick", "enemy": "Teemo"})
        data = resp.json()
        for profile in data["profiles"]:
            assert "guide_id" in profile
            assert "guide_name" in profile
            assert "author" in profile
            assert "options" in profile
            assert "count" in profile
            assert isinstance(profile["options"], list)
            assert profile["count"] == len(profile["options"])

    def test_profile_options_have_required_fields(self, client):
        """Each option in a profile must have the fields the frontend needs."""
        resp = client.post("/api/build/query", json={"champion": "Yorick", "enemy": "Jax"})
        data = resp.json()
        required_fields = [
            "keystone", "item_build_name", "summoners", "difficulty",
            "selected_perk_ids", "primary_style_id", "sub_style_id",
            "starter", "boots", "core", "situational",
            "rune_details", "shard_details", "item_details",
            "starter_info", "resolve_code", "shard_info", "reasoning",
        ]
        for profile in data["profiles"]:
            for opt in profile["options"]:
                for field in required_fields:
                    assert field in opt, f"Missing '{field}' in option {opt.get('keystone', '?')}"

    def test_rune_details_have_icon_and_name(self, client):
        resp = client.post("/api/build/query", json={"champion": "Yorick", "enemy": "Jax"})
        data = resp.json()
        opt = data["profiles"][0]["options"][0]
        assert len(opt["rune_details"]) == 6  # 6 rune perks
        for rd in opt["rune_details"]:
            assert "id" in rd
            assert "name" in rd
            assert "icon" in rd
            assert isinstance(rd["id"], int)

    def test_shard_details_have_icon_and_name(self, client):
        resp = client.post("/api/build/query", json={"champion": "Yorick", "enemy": "Jax"})
        data = resp.json()
        opt = data["profiles"][0]["options"][0]
        assert len(opt["shard_details"]) == 3  # 3 shard slots
        for sd in opt["shard_details"]:
            assert "id" in sd
            assert "name" in sd
            assert "icon" in sd

    def test_item_details_keyed_by_string_id(self, client):
        resp = client.post("/api/build/query", json={"champion": "Yorick", "enemy": "Jax"})
        data = resp.json()
        opt = data["profiles"][0]["options"][0]
        assert isinstance(opt["item_details"], dict)
        for key, val in opt["item_details"].items():
            assert key.isdigit(), f"item_details key should be string digit, got {key}"
            assert "id" in val
            assert "name" in val
            assert "icon" in val

    def test_selected_perk_ids_has_9_entries(self, client):
        resp = client.post("/api/build/query", json={"champion": "Yorick", "enemy": "Jax"})
        data = resp.json()
        for profile in data["profiles"]:
            for opt in profile["options"]:
                assert len(opt["selected_perk_ids"]) == 9, (
                    f"{opt['keystone']}: expected 9 perks, got {len(opt['selected_perk_ids'])}"
                )

    def test_all_perk_ids_are_positive_ints(self, client):
        resp = client.post("/api/build/query", json={"champion": "Yorick", "enemy": "Jax"})
        data = resp.json()
        for profile in data["profiles"]:
            for opt in profile["options"]:
                for pid in opt["selected_perk_ids"]:
                    assert isinstance(pid, int) and pid > 0


class TestLegacyFallback:
    def test_non_yorick_uses_legacy_engine(self, client):
        """Champions without guides should fall back to Built-in Engine."""
        resp = client.post("/api/build/query", json={"champion": "Garen", "enemy": "Jax"})
        data = resp.json()
        assert len(data["profiles"]) == 1
        assert data["profiles"][0]["guide_id"] == "_legacy"
        assert data["profiles"][0]["guide_name"] == "Built-in Engine"
        assert data["profiles"][0]["author"] == "System"

    def test_legacy_fallback_still_returns_options(self, client):
        resp = client.post("/api/build/query", json={"champion": "Garen", "enemy": "Jax"})
        data = resp.json()
        assert data["profiles"][0]["count"] >= 1

    def test_yorick_uses_guide_profile(self, client):
        """Yorick should use the Kampsycho guide, not legacy."""
        resp = client.post("/api/build/query", json={"champion": "Yorick", "enemy": "Jax"})
        data = resp.json()
        assert data["profiles"][0]["guide_id"] != "_legacy"
        assert "Kampsycho" in data["profiles"][0]["guide_name"]


class TestMultiProfileAllMatchups:
    def test_every_matchup_returns_profiles(self, client):
        """Every known matchup should return at least 1 profile with options."""
        failures = []
        for enemy in sorted(MATCHUP_TABLE.keys()):
            resp = client.post("/api/build/query", json={"champion": "Yorick", "enemy": enemy})
            if resp.status_code != 200:
                failures.append(f"{enemy}: HTTP {resp.status_code}")
                continue
            data = resp.json()
            if not data.get("profiles") or data["profiles"][0]["count"] == 0:
                failures.append(f"{enemy}: no options returned")
        assert not failures, f"Failures:\n" + "\n".join(failures)


# ============================================================================
# Guide API Endpoint Tests
# ============================================================================

class TestGuideAPIEndpoints:
    def test_list_guides_endpoint(self, client):
        resp = client.get("/api/guides")
        assert resp.status_code == 200
        data = resp.json()
        assert "guides" in data
        assert isinstance(data["guides"], list)

    def test_list_guides_filter_by_champion(self, client):
        resp = client.get("/api/guides?champion=Yorick")
        assert resp.status_code == 200
        data = resp.json()
        for g in data["guides"]:
            assert g["champion"] == "Yorick"

    def test_get_guide_by_id(self, client):
        # First get the list to find a valid ID
        resp = client.get("/api/guides?champion=Yorick")
        guides = resp.json()["guides"]
        assert len(guides) >= 1
        guide_id = guides[0]["guide_id"]

        resp = client.get(f"/api/guides/{guide_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["guide_id"] == guide_id
        assert "root" in data
        assert "data" in data

    def test_get_nonexistent_guide(self, client):
        resp = client.get("/api/guides/nonexistent-xyz")
        assert resp.status_code == 404

    def test_execute_guide(self, client):
        resp = client.get("/api/guides?champion=Yorick")
        guide_id = resp.json()["guides"][0]["guide_id"]

        resp = client.post(f"/api/guides/{guide_id}/execute", json={"enemy": "Jax"})
        assert resp.status_code == 200
        data = resp.json()
        assert "builds" in data
        assert len(data["builds"]) >= 1

    def test_execute_guide_missing_enemy(self, client):
        resp = client.get("/api/guides?champion=Yorick")
        guide_id = resp.json()["guides"][0]["guide_id"]

        resp = client.post(f"/api/guides/{guide_id}/execute", json={})
        assert resp.status_code == 400
