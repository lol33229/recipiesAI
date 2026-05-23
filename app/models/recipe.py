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
