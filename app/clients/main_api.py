from typing import Any

import httpx

from app.config import get_settings

_MAX_PAGE_SIZE = 100


def _client() -> httpx.AsyncClient:
    settings = get_settings()
    base = settings.main_api_base_url.strip()
    if not base:
        raise RuntimeError("MAIN_API_BASE_URL не задан")
    headers: dict[str, str] = {}
    if settings.main_api_bearer_token:
        headers["Authorization"] = f"Bearer {settings.main_api_bearer_token}"
    return httpx.AsyncClient(
        base_url=base.rstrip("/"),
        headers=headers,
        timeout=settings.main_api_timeout_sec,
    )


async def fetch_recipe(recipe_id: str) -> dict[str, Any] | None:
    async with _client() as client:
        r = await client.get(f"/api/recipes/{recipe_id}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()


async def fetch_recipes_page(page: int = 1, page_size: int = _MAX_PAGE_SIZE) -> dict[str, Any]:
    async with _client() as client:
        r = await client.get(
            "/api/recipes",
            params={"page": page, "pageSize": page_size},
        )
        r.raise_for_status()
        return r.json()


async def fetch_all_recipes() -> list[dict[str, Any]]:
    first = await fetch_recipes_page(page=1, page_size=_MAX_PAGE_SIZE)
    items = list(first.get("items") or [])
    total_pages = int(first.get("totalPages") or 1)
    for page in range(2, total_pages + 1):
        data = await fetch_recipes_page(page=page, page_size=_MAX_PAGE_SIZE)
        items.extend(data.get("items") or [])
    return items
