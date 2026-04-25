from pydantic import BaseModel

from app.services.nutrition_data import INGREDIENTS_PER_100G, resolve_ingredient_key


class SubstitutionSuggestion(BaseModel):
    original: str
    replacement: str
    grams: float
    nutrition_delta: dict[str, float]
    score: float


_GROUPS: dict[str, str] = {
    "курица": "protein",
    "сыр": "protein",
    "яйцо": "protein",
    "рис": "starch",
    "мука_пшеничная": "starch",
    "картофель": "starch",
    "лук": "vegetable",
    "помидор": "vegetable",
    "масло_растительное": "fat",
    "молоко": "dairy",
}


def _objective_delta(goal: str, old: dict[str, float], new: dict[str, float]) -> float:
    dk = old["kcal"] - new["kcal"]
    dp = new["protein_g"] - old["protein_g"]
    df = old["fat_g"] - new["fat_g"]
    dc = old["carbs_g"] - new["carbs_g"]
    if goal == "lower_kcal":
        return dk
    if goal == "higher_protein":
        return dp
    if goal == "lower_fat":
        return df
    if goal == "lower_carbs":
        return dc
    return (0.5 * dk) + (0.3 * dp) + (0.1 * df) + (0.1 * dc)


def optimize_substitutions(
    ingredients: list[tuple[str, float]],
    goal: str = "balanced",
    max_replacements: int = 3,
) -> list[SubstitutionSuggestion]:
    suggestions: list[SubstitutionSuggestion] = []

    for name, grams in ingredients:
        key = resolve_ingredient_key(name)
        if not key or key not in INGREDIENTS_PER_100G:
            continue
        group = _GROUPS.get(key)
        if not group:
            continue
        old_n = INGREDIENTS_PER_100G[key]

        best_key: str | None = None
        best_score = 0.0
        for cand_key, cand_n in INGREDIENTS_PER_100G.items():
            if cand_key == key:
                continue
            if _GROUPS.get(cand_key) != group:
                continue
            score = _objective_delta(goal, old_n, cand_n)
            if score > best_score:
                best_score = score
                best_key = cand_key

        if not best_key:
            continue

        new_n = INGREDIENTS_PER_100G[best_key]
        factor = grams / 100.0
        delta = {
            "kcal": round((new_n["kcal"] - old_n["kcal"]) * factor, 1),
            "protein_g": round((new_n["protein_g"] - old_n["protein_g"]) * factor, 2),
            "fat_g": round((new_n["fat_g"] - old_n["fat_g"]) * factor, 2),
            "carbs_g": round((new_n["carbs_g"] - old_n["carbs_g"]) * factor, 2),
        }
        suggestions.append(
            SubstitutionSuggestion(
                original=name,
                replacement=best_key.replace("_", " "),
                grams=grams,
                nutrition_delta=delta,
                score=round(best_score, 3),
            )
        )

    suggestions.sort(key=lambda x: x.score, reverse=True)
    return suggestions[:max_replacements]
