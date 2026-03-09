"""Import summoner spells into the LoL client via LCU API."""

from lcu.client import LCUClient

SPELL_IDS = {
    "Flash": 4,
    "TP": 12,
    "Teleport": 12,
    "Ghost": 6,
    "Exhaust": 3,
    "Ignite": 14,
    "Heal": 7,
    "Barrier": 21,
    "Cleanse": 1,
    "Smite": 11,
}


def parse_spell_pair(spells_str: str) -> tuple[int, int]:
    """Parse 'Ghost/TP' into (6, 12). Returns (4, 12) as fallback."""
    parts = spells_str.strip().split("/")
    if len(parts) != 2:
        return (4, 12)
    spell1 = SPELL_IDS.get(parts[0].strip(), 4)
    spell2 = SPELL_IDS.get(parts[1].strip(), 12)
    return (spell1, spell2)


async def import_summoner_spells(
    client: LCUClient,
    spell1_id: int,
    spell2_id: int,
) -> dict:
    if not client.connected:
        return {"success": False, "error": "Not connected to client"}

    body = {"spell1Id": spell1_id, "spell2Id": spell2_id}
    resp = await client.patch("/lol-champ-select/v1/session/my-selection", json=body)

    if not resp:
        return {"success": False, "error": "No response from client"}
    if resp.status_code in (200, 204):
        return {"success": True}
    return {"success": False, "error": f"Status {resp.status_code}: {resp.text[:200]}"}
