from typing import Any

from app.models.recipe import StoredIngredient, StoredRecipe


def map_main_api_recipe(data: dict[str, Any]) -> StoredRecipe:
    recipe_id = str(data.get("id") or data.get("Id") or "")
    title = str(data.get("title") or data.get("Title") or "").strip()

    ingredients: list[StoredIngredient] = []
    for item in data.get("ingredients") or data.get("Ingredients") or []:
        name = (
            item.get("ingredientTitle")
            or item.get("IngredientTitle")
            or item.get("title")
            or item.get("name")
            or "ингредиент"
        )
        weight = float(item.get("weight") or item.get("Weight") or 0)
        if weight <= 0:
            weight = 1.0
        ingredients.append(StoredIngredient(name=str(name).strip(), grams=weight))

    steps: list[str] = []
    for step in data.get("steps") or data.get("Steps") or []:
        if isinstance(step, str):
            steps.append(step)
        elif isinstance(step, dict):
            text = step.get("description") or step.get("Description")
            if text:
                steps.append(str(text).strip())

    tags: list[str] = []
    for key in ("dishType", "mealType", "DishType", "MealType"):
        val = data.get(key)
        if val and str(val).strip():
            tags.append(str(val).strip())

    # КБЖУ из основного API -на всё блюдо.
    nutrition_per_100g = {
        "kcal": float(data.get("caloricValue") or data.get("CaloricValue") or 0),
        "protein_g": float(data.get("proteins") or data.get("Proteins") or 0),
        "fat_g": float(data.get("fats") or data.get("Fats") or 0),
        "carbs_g": float(data.get("carbohydrates") or data.get("Carbohydrates") or 0),
    }

    created_at = str(data.get("createdAt") or data.get("CreatedAt") or "")

    return StoredRecipe(
        recipe_id=recipe_id,
        title=title or recipe_id,
        ingredients=ingredients,
        steps=steps,
        tags=tags,
        nutrition_per_100g=nutrition_per_100g,
        unknown_ingredients=[],
        created_at=created_at,
        average_rating=float(data.get("averageRating") or data.get("AverageRating") or 0),
        ratings_count=int(data.get("ratingsCount") or data.get("RatingsCount") or 0),
        likes_count=int(data.get("likesCount") or data.get("LikesCount") or 0),
    )
