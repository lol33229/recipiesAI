import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.ingredient_substitution import SubstitutionSuggestion, optimize_substitutions
from app.models.recipe import StoredRecipe
from app.services.recipe_store import get_recipe, list_recipes, recipe_source

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


class OptimizeSubstitutionsRequest(BaseModel):
    recipe_id: str = Field(..., min_length=1)
    goal: str = Field(default="balanced", pattern="^(balanced|lower_kcal|higher_protein|lower_fat|lower_carbs)$")
    max_replacements: int = Field(default=3, ge=1, le=10)


class OptimizeSubstitutionsResponse(BaseModel):
    recipe_id: str
    goal: str
    suggestions: list[SubstitutionSuggestion]


@router.get("", response_model=list[StoredRecipe])
async def get_recipes() -> list[StoredRecipe]:
    try:
        return await list_recipes()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Основной API: HTTP {e.response.status_code}") from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@router.post("/optimize-substitutions", response_model=OptimizeSubstitutionsResponse)
async def optimize_recipe_substitutions(req: OptimizeSubstitutionsRequest) -> OptimizeSubstitutionsResponse:
    try:
        recipe = await get_recipe(req.recipe_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Основной API: HTTP {e.response.status_code}") from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    if recipe is None:
        raise HTTPException(status_code=404, detail="recipe_id не найден")

    suggestions = optimize_substitutions(
        ingredients=[(i.name, i.grams) for i in recipe.ingredients],
        goal=req.goal,
        max_replacements=req.max_replacements,
    )
    return OptimizeSubstitutionsResponse(
        recipe_id=req.recipe_id,
        goal=req.goal,
        suggestions=suggestions,
    )


@router.get("/meta/source")
async def recipes_data_source() -> dict[str, str]:
    return {"recipe_source": recipe_source()}


@router.get("/{recipe_id}", response_model=StoredRecipe)
async def get_recipe_by_id(recipe_id: str) -> StoredRecipe:
    try:
        recipe = await get_recipe(recipe_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Основной API: HTTP {e.response.status_code}") from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    if recipe is None:
        raise HTTPException(status_code=404, detail="recipe_id не найден")
    return recipe
