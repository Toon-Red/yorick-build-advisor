"""Import item sets into the LoL client via LCU API."""

from lcu.client import LCUClient


async def import_item_set(
    client: LCUClient,
    champion: str,
    starter: list[int],
    core: list[int],
    boots: int,
    situational: list[int],
    title: str = "Build Advisor v2",
) -> dict:
    if not client.connected:
        return {"success": False, "error": "Not connected to client"}

    resp = await client.get("/lol-summoner/v1/current-summoner")
    if not resp or resp.status_code != 200:
        return {"success": False, "error": "Failed to get summoner info"}

    summoner = resp.json()
    summoner_id = summoner.get("summonerId", 0)

    blocks = []
    if starter:
        blocks.append({
            "type": "Starter",
            "items": [{"id": str(item_id), "count": 1} for item_id in starter],
        })
    if boots:
        blocks.append({
            "type": "Boots",
            "items": [{"id": str(boots), "count": 1}],
        })
    if core:
        blocks.append({
            "type": "Core Build",
            "items": [{"id": str(item_id), "count": 1} for item_id in core],
        })
    if situational:
        blocks.append({
            "type": "Situational",
            "items": [{"id": str(item_id), "count": 1} for item_id in situational],
        })

    sets_resp = await client.get(f"/lol-item-sets/v1/item-sets/{summoner_id}/sets")
    existing_sets = []
    if sets_resp and sets_resp.status_code == 200:
        data = sets_resp.json()
        existing_sets = data.get("itemSets", [])

    existing_sets = [s for s in existing_sets if s.get("title") != title]

    new_set = {
        "title": title,
        "type": "custom",
        "map": "any",
        "mode": "any",
        "priority": False,
        "sortrank": 0,
        "blocks": blocks,
        "associatedChampions": [],
        "associatedMaps": [],
    }
    existing_sets.append(new_set)

    put_resp = await client.put(
        f"/lol-item-sets/v1/item-sets/{summoner_id}/sets",
        json={"itemSets": existing_sets},
    )

    if not put_resp or put_resp.status_code not in (200, 201):
        err = ""
        if put_resp:
            err = put_resp.text[:200]
        return {"success": False, "error": f"Failed to update item sets: {err}"}

    return {"success": True}
