"""Champion select session tracker."""

from dataclasses import dataclass, field
from lcu.client import LCUClient


@dataclass
class ChampSelectState:
    active: bool = False
    my_champion_id: int = 0
    my_position: str = ""
    my_team: list[dict] = field(default_factory=list)
    their_team: list[dict] = field(default_factory=list)
    lane_opponent_id: int = 0
    game_phase: str = ""


class ChampSelectTracker:
    def __init__(self, client: LCUClient):
        self.client = client
        self._champion_map: dict[int, str] = {}

    def set_champion_map(self, champions: dict):
        self._champion_map = {}
        for name, data in champions.items():
            key = data.get("key")
            if key:
                self._champion_map[int(key)] = data["name"]

    def champion_name(self, champion_id: int) -> str:
        if champion_id == 0:
            return ""
        return self._champion_map.get(champion_id, f"Champion {champion_id}")

    async def get_state(self) -> ChampSelectState:
        state = ChampSelectState()
        resp = await self.client.get("/lol-champ-select/v1/session")
        if not resp or resp.status_code != 200:
            return state

        data = resp.json()
        state.active = True
        local_cell = data.get("localPlayerCellId", -1)
        timer = data.get("timer", {})
        state.game_phase = timer.get("phase", "")

        for player in data.get("myTeam", []):
            entry = {
                "champion_id": player.get("championId", 0),
                "champion_name": self.champion_name(player.get("championId", 0)),
                "position": player.get("assignedPosition", "").upper(),
                "cell_id": player.get("cellId", -1),
                "summoner_id": player.get("summonerId", 0),
            }
            state.my_team.append(entry)
            if player.get("cellId") == local_cell:
                state.my_champion_id = player.get("championId", 0)
                state.my_position = player.get("assignedPosition", "").upper()

        for player in data.get("theirTeam", []):
            entry = {
                "champion_id": player.get("championId", 0),
                "champion_name": self.champion_name(player.get("championId", 0)),
                "position": player.get("assignedPosition", "").upper(),
                "cell_id": player.get("cellId", -1),
            }
            state.their_team.append(entry)

        state.lane_opponent_id = self._guess_lane_opponent(state)
        return state

    def _guess_lane_opponent(self, state: ChampSelectState) -> int:
        if not state.my_position or not state.their_team:
            return 0
        for enemy in state.their_team:
            if enemy["position"] == state.my_position and enemy["champion_id"] > 0:
                return enemy["champion_id"]
        return 0

    async def get_game_phase(self) -> str:
        resp = await self.client.get("/lol-gameflow/v1/gameflow-phase")
        if not resp or resp.status_code != 200:
            return "None"
        return resp.json() if resp.text else "None"
