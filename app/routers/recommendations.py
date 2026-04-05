from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app.services.collaborative_filtering import CollaborativeFiltering, get_default_cf

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


_cf_override: CollaborativeFiltering | None = None


def _active_cf() -> CollaborativeFiltering:
    return _cf_override if _cf_override is not None else get_default_cf()


@router.post("/build", status_code=204)
async def build_engine(req: BuildCFRequest) -> Response:
    """Подменить движок рекомендаций данными из запроса (для тестов/демо)."""
    global _cf_override
    tuples = [(i.user_id, i.recipe_id, i.rating) for i in req.interactions]
    _cf_override = CollaborativeFiltering(req.user_ids, req.recipe_ids, tuples)
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
