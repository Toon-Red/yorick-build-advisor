"""Import rune pages into the LoL client via LCU API."""

from lcu.client import LCUClient


async def import_rune_page(
    client: LCUClient,
    name: str,
    primary_style_id: int,
    sub_style_id: int,
    selected_perk_ids: list[int],
) -> dict:
    if not client.connected:
        return {"success": False, "error": "Not connected to client"}

    resp = await client.get("/lol-perks/v1/pages")
    if not resp or resp.status_code != 200:
        return {"success": False, "error": "Failed to get rune pages"}

    pages = resp.json()
    editable_page = None
    for page in pages:
        if page.get("isDeletable", False):
            editable_page = page
            break

    if editable_page:
        del_resp = await client.delete(f"/lol-perks/v1/pages/{editable_page['id']}")
        if not del_resp or del_resp.status_code not in (200, 204):
            return {"success": False, "error": f"Failed to delete page {editable_page['id']}"}

    new_page = {
        "name": name,
        "primaryStyleId": primary_style_id,
        "subStyleId": sub_style_id,
        "selectedPerkIds": selected_perk_ids,
        "current": True,
    }

    create_resp = await client.post("/lol-perks/v1/pages", json=new_page)
    if not create_resp or create_resp.status_code not in (200, 201):
        err = ""
        if create_resp:
            err = create_resp.text[:200]
        return {"success": False, "error": f"Failed to create rune page: {err}"}

    created = create_resp.json()
    return {"success": True, "page_id": created.get("id")}
