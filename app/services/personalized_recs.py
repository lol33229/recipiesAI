from dataclasses import dataclass

from app.models.recipe import StoredRecipe
from app.services.collaborative_filtering import CollaborativeFiltering
from app.services.recipe_store import list_recipes


@dataclass
class UserInteraction:
    user_id: str
    recipe_id: str
    rating: float


_INTERACTIONS: list[UserInteraction] = []


def add_interactions(items: list[tuple[str, str, float]]) -> None:
    for user_id, recipe_id, rating in items:
        _INTERACTIONS.append(UserInteraction(user_id=user_id, recipe_id=recipe_id, rating=rating))


def list_interactions() -> list[UserInteraction]:
    return list(_INTERACTIONS)


def _build_cf() -> CollaborativeFiltering | None:
    interactions = list_interactions()
    if not interactions:
        return None
    user_ids = sorted({x.user_id for x in interactions})
    recipe_ids = sorted({x.recipe_id for x in interactions})
    if not user_ids or not recipe_ids:
        return None
    tuples = [(x.user_id, x.recipe_id, x.rating) for x in interactions]
    return CollaborativeFiltering(user_ids=user_ids, recipe_ids=recipe_ids, interactions=tuples)


def _user_profile_ingredients(user_id: str, recipes_by_id: dict[str, StoredRecipe]) -> set[str]:
    liked = [x for x in _INTERACTIONS if x.user_id == user_id and x.rating >= 4.0]
    profile: set[str] = set()
    for inter in liked:
        recipe = recipes_by_id.get(inter.recipe_id)
        if not recipe:
            continue
        profile |= {i.name.strip().lower() for i in recipe.ingredients}
    return profile


def _popularity_score(recipe: StoredRecipe) -> float:
    """Популярность из основного API (рейтинг + лайки)."""
    rating_part = recipe.average_rating / 5.0 if recipe.average_rating > 0 else 0.0
    likes_part = min(recipe.likes_count / 10.0, 1.0) if recipe.likes_count > 0 else 0.0
    return round(0.7 * rating_part + 0.3 * likes_part, 4)


def _cold_start_feed(recipes: list[StoredRecipe], top_k: int) -> list[tuple[str, float]]:
    """Лента «Для вас», если нет оценок пользователя в AI-сервисе."""
    ranked = sorted(
        recipes,
        key=lambda r: (_popularity_score(r), r.ratings_count, r.likes_count, r.created_at),
        reverse=True,
    )
    return [(r.recipe_id, _popularity_score(r) or 0.1) for r in ranked[:top_k]]


async def personalized_recommendations(
    user_id: str,
    top_k: int = 5,
    prefer_ingredients: list[str] | None = None,
    exclude_ingredients: list[str] | None = None,
) -> list[tuple[str, float]]:
    recipes = await list_recipes()
    if not recipes:
        return []

    prefer = {x.strip().lower() for x in (prefer_ingredients or []) if x.strip()}
    exclude = {x.strip().lower() for x in (exclude_ingredients or []) if x.strip()}
    recipes_by_id = {r.recipe_id: r for r in recipes}

    rating_buckets: dict[str, list[float]] = {}
    for inter in _INTERACTIONS:
        rating_buckets.setdefault(inter.recipe_id, []).append(inter.rating)
    popularity = {
        rid: (sum(vals) / len(vals)) / 5.0 for rid, vals in rating_buckets.items() if vals
    }

    rated_by_user = {x.recipe_id for x in _INTERACTIONS if x.user_id == user_id}
    profile = _user_profile_ingredients(user_id, recipes_by_id)
    has_user_signals = bool(rated_by_user or profile)

    cf = _build_cf()
    cf_scores: dict[str, float] = {}
    if cf and user_id in cf.user_index:
        cf_scores = {x.recipe_id: x.score / 5.0 for x in cf.recommend_for_user(user_id, top_k=100)}

    scored: list[tuple[str, float]] = []
    for recipe in recipes:
        rid = recipe.recipe_id
        if rid in rated_by_user:
            continue
        ingredient_set = {i.name.strip().lower() for i in recipe.ingredients}
        if exclude and ingredient_set & exclude:
            continue

        profile_affinity = 0.0
        if profile and ingredient_set:
            profile_affinity = len(profile & ingredient_set) / len(ingredient_set)

        prefer_boost = 0.0
        if prefer and ingredient_set:
            prefer_boost = len(prefer & ingredient_set) / len(prefer)

        cf_part = cf_scores.get(rid, 0.0)
        popularity_part = popularity.get(rid, 0.0)
        api_popularity = _popularity_score(recipe)

        if has_user_signals:
            score = (0.6 * cf_part) + (0.3 * profile_affinity) + (0.1 * popularity_part) + (0.1 * prefer_boost)
        else:
            # Холодный старт: опираемся на рейтинг/лайки из основного API
            score = api_popularity + (0.15 * prefer_boost)

        if score > 0:
            scored.append((rid, round(score, 4)))

    scored.sort(key=lambda x: x[1], reverse=True)
    if scored:
        return scored[:top_k]

    return _cold_start_feed(recipes, top_k)
