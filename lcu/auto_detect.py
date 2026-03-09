"""Auto-detect enemy champions during champ select with lane prediction."""

import asyncio
from dataclasses import dataclass, field

from data.role_rates import get_top_probability


@dataclass
class DetectedEnemy:
    champion_id: int
    champion_name: str
    top_probability: float  # 0.0 to 1.0


@dataclass
class ChampSelectSnapshot:
    active: bool = False
    my_champion_id: int = 0
    my_champion_name: str = ""
    enemies: list[DetectedEnemy] = field(default_factory=list)
    predicted_opponent: str = ""  # highest top% enemy
    game_phase: str = ""

    def to_dict(self) -> dict:
        return {
            "active": self.active,
            "my_champion_id": self.my_champion_id,
            "my_champion_name": self.my_champion_name,
            "enemies": [
                {
                    "champion_id": e.champion_id,
                    "champion_name": e.champion_name,
                    "top_probability": round(e.top_probability, 3),
                }
                for e in self.enemies
            ],
            "predicted_opponent": self.predicted_opponent,
            "game_phase": self.game_phase,
        }


async def poll_champ_select(
    lcu_client, champion_id_to_name: dict[int, str]
) -> ChampSelectSnapshot:
    """Single poll of champ select state. Returns snapshot."""
    snapshot = ChampSelectSnapshot()

    # 1. Check game phase
    phase_resp = await lcu_client.get("/lol-gameflow/v1/gameflow-phase")
    if not phase_resp or phase_resp.status_code != 200:
        return snapshot

    phase = phase_resp.json() if phase_resp.text else "None"
    snapshot.game_phase = phase

    # 2. If not in champ select, return inactive snapshot
    if phase != "ChampSelect":
        return snapshot

    # 3. Fetch champ select session
    session_resp = await lcu_client.get("/lol-champ-select/v1/session")
    if not session_resp or session_resp.status_code != 200:
        return snapshot

    session = session_resp.json()
    snapshot.active = True

    local_cell = session.get("localPlayerCellId", -1)

    # 4. Find our champion from myTeam
    for player in session.get("myTeam", []):
        if player.get("cellId") == local_cell:
            champ_id = player.get("championId", 0)
            snapshot.my_champion_id = champ_id
            snapshot.my_champion_name = champion_id_to_name.get(champ_id, "")
            break

    # 5. Parse theirTeam for enemy champion IDs
    enemies: list[DetectedEnemy] = []
    for player in session.get("theirTeam", []):
        champ_id = player.get("championId", 0)
        if champ_id <= 0:
            continue

        champ_name = champion_id_to_name.get(champ_id, f"Champion {champ_id}")
        assigned_position = player.get("assignedPosition", "")

        # 6. Determine top probability
        # In ranked, if enemy is assigned "top", their top probability is 1.0
        if assigned_position and assigned_position.lower() == "top":
            top_prob = 1.0
        else:
            top_prob = get_top_probability(champ_name)

        enemies.append(
            DetectedEnemy(
                champion_id=champ_id,
                champion_name=champ_name,
                top_probability=top_prob,
            )
        )

    # 7. Sort enemies by top_probability descending
    enemies.sort(key=lambda e: e.top_probability, reverse=True)
    snapshot.enemies = enemies

    # 8. Set predicted_opponent to highest top% enemy
    if enemies:
        snapshot.predicted_opponent = enemies[0].champion_name

    return snapshot


def has_state_changed(
    old: ChampSelectSnapshot, new: ChampSelectSnapshot
) -> bool:
    """Check if the snapshot changed enough to emit an update."""
    # Active state changed
    if old.active != new.active:
        return True

    # Predicted opponent changed
    if old.predicted_opponent != new.predicted_opponent:
        return True

    # Enemy list changed (different count or different champion IDs)
    old_ids = {e.champion_id for e in old.enemies}
    new_ids = {e.champion_id for e in new.enemies}
    if old_ids != new_ids:
        return True

    return False
