from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app.services.collaborative_filtering import CollaborativeFiltering, get_default_cf
from app.services.personalized_recs import add_interactions, personalized_recommendations
from app.services.recipe_store import get_recipe, list_recipes

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


class InteractionIn(BaseModel):
    user_id: str
    recipe_id: str
    rating: float = Field(ge=0.5, le=5.0)


class BuildCFRequest(BaseModel):
    user_ids: list[str] = Field(..., min_length=1)
    recipe_ids: list[str] = Field(..., min_length=1)
    interactions: list[InteractionIn] = Field(..., min_length=1)


class RecommendUserRequest(BaseModel):
    user_id: str
    top_k: int = Field(default=5, ge=1, le=50)


class SimilarRecipeRequest(BaseModel):
    recipe_id: str
    top_k: int = Field(default=5, ge=1, le=50)


class ScoredRecipe(BaseModel):
    recipe_id: str
    score: float


class RecommendResponse(BaseModel):
    items: list[ScoredRecipe]


class PersonalizedRecommendRequest(BaseModel):
    user_id: str
    top_k: int = Field(default=5, ge=1, le=50)
    prefer_ingredients: list[str] = Field(default_factory=list)
    exclude_ingredients: list[str] = Field(default_factory=list)


_cf_override: CollaborativeFiltering | None = None


def _active_cf() -> CollaborativeFiltering:
    return _cf_override if _cf_override is not None else get_default_cf()


@router.post("/build", status_code=204)
async def build_engine(req: BuildCFRequest) -> Response:
    """Подменить движок рекомендаций данными из запроса (для тестов)."""
    global _cf_override
    tuples = [(i.user_id, i.recipe_id, i.rating) for i in req.interactions]
    _cf_override = CollaborativeFiltering(req.user_ids, req.recipe_ids, tuples)
    return Response(status_code=204)


@router.post("/interactions", status_code=204)
async def add_user_interactions(req: BuildCFRequest) -> Response:
    tuples = [(i.user_id, i.recipe_id, i.rating) for i in req.interactions]
    add_interactions(tuples)
    return Response(status_code=204)


@router.post("/for-user", response_model=RecommendResponse)
async def recommend_for_user(req: RecommendUserRequest) -> RecommendResponse:
    cf = _active_cf()
    if req.user_id not in cf.user_index:
        raise HTTPException(status_code=404, detail="user_id не найден в матрице оценок")
    items = cf.recommend_for_user(req.user_id, top_k=req.top_k)
    return RecommendResponse(items=[ScoredRecipe(recipe_id=x.recipe_id, score=x.score) for x in items])


@router.post("/similar-recipes", response_model=RecommendResponse)
async def similar_recipes(req: SimilarRecipeRequest) -> RecommendResponse:
    cf = _active_cf()
    if req.recipe_id not in cf.recipe_index:
        raise HTTPException(status_code=404, detail="recipe_id не найден в матрице оценок")
    items = cf.similar_recipes(req.recipe_id, top_k=req.top_k)
    return RecommendResponse(items=[ScoredRecipe(recipe_id=x.recipe_id, score=x.score) for x in items])


@router.post("/similar-by-ingredients", response_model=RecommendResponse)
async def similar_by_ingredients(req: SimilarRecipeRequest) -> RecommendResponse:
    base = await get_recipe(req.recipe_id)
    if base is None:
        raise HTTPException(status_code=404, detail="recipe_id не найден среди опубликованных рецептов")

    base_set = {x.name.strip().lower() for x in base.ingredients}
    if not base_set:
        return RecommendResponse(items=[])

    scored: list[ScoredRecipe] = []
    for recipe in await list_recipes():
        if recipe.recipe_id == base.recipe_id:
            continue
        other_set = {x.name.strip().lower() for x in recipe.ingredients}
        if not other_set:
            continue
        union = base_set | other_set
        if not union:
            continue
        score = len(base_set & other_set) / len(union)
        if score > 0:
            scored.append(ScoredRecipe(recipe_id=recipe.recipe_id, score=round(score, 4)))

    scored.sort(key=lambda x: x.score, reverse=True)
    return RecommendResponse(items=scored[: req.top_k])


@router.post("/personalized", response_model=RecommendResponse)
async def personalized(req: PersonalizedRecommendRequest) -> RecommendResponse:
    items = await personalized_recommendations(
        user_id=req.user_id,
        top_k=req.top_k,
        prefer_ingredients=req.prefer_ingredients,
        exclude_ingredients=req.exclude_ingredients,
    )
    return RecommendResponse(items=[ScoredRecipe(recipe_id=rid, score=score) for rid, score in items])
