import httpx

from app.clients.main_api import fetch_all_recipes, fetch_recipe
from app.config import get_settings
from app.models.recipe import StoredRecipe
from app.services.main_api_mapper import map_main_api_recipe


def recipe_source() -> str:
    return "main_api"


def _ensure_main_api() -> None:
    if not get_settings().main_api_base_url.strip():
        raise RuntimeError("Задайте MAIN_API_BASE_URL в .env (основной Recipes.API)")


async def get_recipe(recipe_id: str) -> StoredRecipe | None:
    _ensure_main_api()
    try:
        data = await fetch_recipe(recipe_id)
    except httpx.HTTPStatusError:
        raise
    except httpx.RequestError as e:
        raise RuntimeError(f"Не удалось связаться с основным API: {e}") from e
    if data is None:
        return None
    return map_main_api_recipe(data)


async def list_recipes() -> list[StoredRecipe]:
    _ensure_main_api()
    try:
        items = await fetch_all_recipes()
    except httpx.RequestError as e:
        raise RuntimeError(f"Не удалось связаться с основным API: {e}") from e
    return [map_main_api_recipe(item) for item in items]
