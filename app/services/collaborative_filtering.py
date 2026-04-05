"""
Item–item collaborative filtering по явным оценкам user × recipe.
Матрица: строки — пользователи, столбцы — рецепты, значение — оценка (0 = нет оценки).
Предсказание для (user, item): взвешенная сумма оценок пользователя по похожим item.
"""

from dataclasses import dataclass

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class CFResult:
    recipe_id: str
    score: float


class CollaborativeFiltering:
    def __init__(
        self,
        user_ids: list[str],
        recipe_ids: list[str],
        interactions: list[tuple[str, str, float]],
    ):
        self.user_index = {u: i for i, u in enumerate(user_ids)}
        self.recipe_index = {r: i for i, r in enumerate(recipe_ids)}
        self.user_ids = user_ids
        self.recipe_ids = recipe_ids
        n_u, n_r = len(user_ids), len(recipe_ids)
        self.matrix = np.zeros((n_u, n_r), dtype=np.float64)
        for uid, rid, rating in interactions:
            if uid in self.user_index and rid in self.recipe_index:
                self.matrix[self.user_index[uid], self.recipe_index[rid]] = rating

        # Косинус между столбцами (рецептами); неизвестные = 0
        self._item_sim = cosine_similarity(self.matrix.T)

    def similar_recipes(self, recipe_id: str, top_k: int = 5) -> list[CFResult]:
        if recipe_id not in self.recipe_index:
            return []
        j = self.recipe_index[recipe_id]
        sims = self._item_sim[j].copy()
        sims[j] = -1.0
        order = np.argsort(-sims)[:top_k]
        return [
            CFResult(recipe_id=self.recipe_ids[i], score=float(sims[i]))
            for i in order
            if sims[i] > 0
        ]

    def recommend_for_user(self, user_id: str, top_k: int = 5) -> list[CFResult]:
        if user_id not in self.user_index:
            return []
        u = self.user_index[user_id]
        rated = np.where(self.matrix[u] > 0)[0]
        if len(rated) == 0:
            return []

        scores = np.zeros(len(self.recipe_ids), dtype=np.float64)
        denom = np.zeros(len(self.recipe_ids), dtype=np.float64)

        for j in rated:
            r_uj = self.matrix[u, j]
            sim_row = self._item_sim[j]
            mask = sim_row > 0
            scores += sim_row * r_uj * mask
            denom += np.abs(sim_row) * mask

        with np.errstate(divide="ignore", invalid="ignore"):
            pred = np.divide(scores, denom, out=np.zeros_like(scores), where=denom > 0)

        # не рекомендуем уже оценённые
        for j in rated:
            pred[j] = -1.0

        order = np.argsort(-pred)[: top_k + len(rated)]
        out: list[CFResult] = []
        for i in order:
            if pred[i] < 0:
                continue
            out.append(CFResult(recipe_id=self.recipe_ids[i], score=float(pred[i])))
            if len(out) >= top_k:
                break
        return out


# Демо-данные для прототипа (без файла на диске)
DEFAULT_USER_IDS = ["u1", "u2", "u3", "u4"]
DEFAULT_RECIPE_IDS = ["r_borscht", "r_pasta", "r_soup", "r_salad", "r_pancake"]
DEFAULT_INTERACTIONS: list[tuple[str, str, float]] = [
    ("u1", "r_borscht", 5.0),
    ("u1", "r_pasta", 4.0),
    ("u1", "r_soup", 4.5),
    ("u2", "r_borscht", 4.0),
    ("u2", "r_salad", 5.0),
    ("u2", "r_pancake", 3.0),
    ("u3", "r_pasta", 5.0),
    ("u3", "r_soup", 3.0),
    ("u3", "r_salad", 4.0),
    ("u4", "r_pancake", 5.0),
    ("u4", "r_soup", 4.0),
]


_default_cf: CollaborativeFiltering | None = None


def get_default_cf() -> CollaborativeFiltering:
    global _default_cf
    if _default_cf is None:
        _default_cf = CollaborativeFiltering(
            DEFAULT_USER_IDS,
            DEFAULT_RECIPE_IDS,
            DEFAULT_INTERACTIONS,
        )
    return _default_cf
