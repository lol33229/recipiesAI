# КБЖУ на 100 г продукта (примерный справочник для прототипа)
INGREDIENTS_PER_100G: dict[str, dict[str, float]] = {
    "курица": {"kcal": 165, "protein_g": 31.0, "fat_g": 3.6, "carbs_g": 0.0},
    "рис": {"kcal": 365, "protein_g": 7.1, "fat_g": 0.7, "carbs_g": 78.9},
    "масло_растительное": {"kcal": 884, "protein_g": 0.0, "fat_g": 100.0, "carbs_g": 0.0},
    "яйцо": {"kcal": 157, "protein_g": 12.7, "fat_g": 11.5, "carbs_g": 0.7},
    "молоко": {"kcal": 64, "protein_g": 3.2, "fat_g": 3.6, "carbs_g": 4.7},
    "мука_пшеничная": {"kcal": 334, "protein_g": 10.3, "fat_g": 1.1, "carbs_g": 68.0},
    "картофель": {"kcal": 77, "protein_g": 2.0, "fat_g": 0.4, "carbs_g": 16.3},
    "лук": {"kcal": 40, "protein_g": 1.1, "fat_g": 0.1, "carbs_g": 9.3},
    "помидор": {"kcal": 18, "protein_g": 0.9, "fat_g": 0.2, "carbs_g": 3.9},
    "сыр": {"kcal": 350, "protein_g": 25.0, "fat_g": 27.0, "carbs_g": 0.0},
}

# Алиасы для поиска без учёта регистра
ALIASES: dict[str, str] = {
    "куриная грудка": "курица",
    "курица филе": "курица",
    "растительное масло": "масло_растительное",
    "подсолнечное масло": "масло_растительное",
    "яйца": "яйцо",
    "пшеничная мука": "мука_пшеничная",
    "мука": "мука_пшеничная",
}


def resolve_ingredient_key(name: str) -> str | None:
    key = name.strip().lower().replace(" ", "_")
    if key in INGREDIENTS_PER_100G:
        return key
    alias = ALIASES.get(name.strip().lower())
    if alias:
        return alias
    # нормализация под ключи словаря
    for k in INGREDIENTS_PER_100G:
        if k.replace("_", " ") == name.strip().lower():
            return k
    return None
