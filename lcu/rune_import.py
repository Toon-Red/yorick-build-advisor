"""Import rune pages into the LoL client via LCU API."""

import asyncio

from lcu.client import LCUClient

_V2_TAG = "(v2)"


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

    # Strategy: find a page to replace, prioritizing:
    # 1. An existing v2-created page (we made it, safe to overwrite)
    # 2. Any deletable (custom) page
    v2_page = None
    deletable_page = None
    for page in pages:
        if not page.get("isDeletable", False):
            continue
        if deletable_page is None:
            deletable_page = page
        if _V2_TAG in page.get("name", ""):
            v2_page = page
            break  # Prefer our own page

    page_to_delete = v2_page or deletable_page

    if page_to_delete:
        del_resp = await client.delete(f"/lol-perks/v1/pages/{page_to_delete['id']}")
        if not del_resp or del_resp.status_code not in (200, 204):
            return {"success": False, "error": f"Failed to delete page {page_to_delete['id']}"}
        # Wait for LCU to process the deletion before creating
        await asyncio.sleep(0.3)
    # If no deletable page exists, try creating anyway (will fail if at max)

    new_page = {
        "name": name if _V2_TAG in name else f"{name} {_V2_TAG}",
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
