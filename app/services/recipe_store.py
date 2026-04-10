from datetime import datetime, timezone

from pydantic import BaseModel, Field


class StoredIngredient(BaseModel):
    name: str = Field(..., min_length=1)
    grams: float = Field(..., gt=0)


class StoredRecipe(BaseModel):
    recipe_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    ingredients: list[StoredIngredient] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    nutrition_per_100g: dict[str, float]
    unknown_ingredients: list[dict] = Field(default_factory=list)
    created_at: str


_RECIPES: dict[str, StoredRecipe] = {}


def upsert_recipe(recipe: StoredRecipe) -> StoredRecipe:
    _RECIPES[recipe.recipe_id] = recipe
    return recipe


def get_recipe(recipe_id: str) -> StoredRecipe | None:
    return _RECIPES.get(recipe_id)


def list_recipes() -> list[StoredRecipe]:
    return list(_RECIPES.values())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
