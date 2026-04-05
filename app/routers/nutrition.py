from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.nutrition_calc import compute_nutrition_per_100g

router = APIRouter(prefix="/api/recipes", tags=["nutrition"])


class IngredientInput(BaseModel):
    name: str = Field(..., min_length=1)
    grams: float = Field(..., gt=0)


class NutritionRequest(BaseModel):
    ingredients: list[IngredientInput] = Field(..., min_length=1)


class NutritionResponse(BaseModel):
    per_100g: dict[str, float]
    unknown_ingredients: list[dict]


@router.post("/nutrition-per-100g", response_model=NutritionResponse)
async def nutrition_per_100g(req: NutritionRequest) -> NutritionResponse:
    items = [(i.name, i.grams) for i in req.ingredients]
    per_100g, unknown = compute_nutrition_per_100g(items)
    # убираем total_weight_g из "кбжу" в отдельное поле можно — оставим в словаре для простоты
    return NutritionResponse(per_100g=per_100g, unknown_ingredients=unknown)
