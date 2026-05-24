"""Соответствие классов ONNX (англ.) → отображаемые названия на русском."""

# Ключи — как в labels.txt (нижний регистр)
LABEL_RU: dict[str, str] = {
    "apple": "яблоко",
    "banana": "банан",
    "blue berry": "голубика",
    "bread": "хлеб",
    "brinjal": "баклажан",
    "butter": "сливочное масло",
    "cabbage": "капуста",
    "capsicum": "болгарский перец",
    "carrot": "морковь",
    "cheese": "сыр",
    "chicken": "курица",
    "chocolate": "шоколад",
    "corn": "кукуруза",
    "cucumber": "огурец",
    "egg": "яйцо",
    "flour": "мука",
    "fresh cream": "сливки",
    "ginger": "имбирь",
    "green beans": "стручковая фасоль",
    "green chilly": "острый перец",
    "green leaves": "зелень",
    "lemon": "лимон",
    "meat": "мясо",
    "milk": "молоко",
    "mushroom": "грибы",
    "potato": "картофель",
    "shrimp": "креветки",
    "stawberry": "клубника",
    "strawberry": "клубника",
    "sweet potato": "батат",
    "tomato": "помидор",
}


def label_to_russian(english_label: str) -> str:
    key = english_label.strip().lower()
    return LABEL_RU.get(key, english_label)
