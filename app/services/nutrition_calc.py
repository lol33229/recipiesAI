from app.services.nutrition_data import INGREDIENTS_PER_100G, resolve_ingredient_key


def compute_nutrition_per_100g(
    items: list[tuple[str, float]],
) -> tuple[dict[str, float], list[dict]]:
    """
    items: (название ингредиента, граммы)
    Возвращает КБЖУ на 100 г готовой смеси (как если всё смешали) и список нераспознанных.
    """
    unknown: list[dict] = []
    total_g = 0.0
    kcal = protein = fat = carbs = 0.0

    for name, grams in items:
        if grams <= 0:
            unknown.append({"name": name, "reason": "grams_must_be_positive"})
            continue
        key = resolve_ingredient_key(name)
        if not key:
            unknown.append({"name": name, "reason": "not_in_reference"})
            continue
        ref = INGREDIENTS_PER_100G[key]
        w = grams / 100.0
        kcal += ref["kcal"] * w
        protein += ref["protein_g"] * w
        fat += ref["fat_g"] * w
        carbs += ref["carbs_g"] * w
        total_g += grams

    if total_g <= 0:
        return {
            "kcal": 0.0,
            "protein_g": 0.0,
            "fat_g": 0.0,
            "carbs_g": 0.0,
            "total_weight_g": 0.0,
        }, unknown

    scale = 100.0 / total_g
    return {
        "kcal": round(kcal * scale, 1),
        "protein_g": round(protein * scale, 2),
        "fat_g": round(fat * scale, 2),
        "carbs_g": round(carbs * scale, 2),
        "total_weight_g": round(total_g, 1),
    }, unknown
