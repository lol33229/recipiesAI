from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.nutrition_calc import compute_nutrition_per_100g
from app.services.recipe_store import (
    StoredIngredient,
    StoredRecipe,
    get_recipe,
    list_recipes,
    now_iso,
    upsert_recipe,
)

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


class IngredientInput(BaseModel):
    name: str = Field(..., min_length=1)
    grams: float = Field(..., gt=0)


class PublishRecipeRequest(BaseModel):
    recipe_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    ingredients: list[IngredientInput] = Field(..., min_length=1)
    steps: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class PublishRecipeResponse(BaseModel):
    recipe: StoredRecipe


@router.post("/publish", response_model=PublishRecipeResponse)
async def publish_recipe(req: PublishRecipeRequest) -> PublishRecipeResponse:
    items = [(i.name, i.grams) for i in req.ingredients]
    nutrition_per_100g, unknown_ingredients = compute_nutrition_per_100g(items)

    recipe = StoredRecipe(
        recipe_id=req.recipe_id,
        title=req.title,
        ingredients=[StoredIngredient(name=i.name, grams=i.grams) for i in req.ingredients],
        steps=req.steps,
        tags=req.tags,
        nutrition_per_100g=nutrition_per_100g,
        unknown_ingredients=unknown_ingredients,
        created_at=now_iso(),
    )
    return PublishRecipeResponse(recipe=upsert_recipe(recipe))


@router.get("", response_model=list[StoredRecipe])
async def get_recipes() -> list[StoredRecipe]:
    return list_recipes()


@router.get("/{recipe_id}", response_model=StoredRecipe)
async def get_recipe_by_id(recipe_id: str) -> StoredRecipe:
    recipe = get_recipe(recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="recipe_id не найден")
    return recipe
