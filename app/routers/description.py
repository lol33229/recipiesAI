import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.llm import ollama_chat

router = APIRouter(prefix="/api/recipes", tags=["description"])

DESCRIPTION_SYSTEM = """Ты редактор кулинарного сайта. По данным рецепта напиши одно короткое описание (2–4 предложения)
для карточки рецепта: аппетитно, без клише, без нумерации шагов. Только текст описания, без заголовков."""


class DescriptionRequest(BaseModel):
    title: str = Field(..., min_length=1)
    ingredients: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    tone: str | None = Field(default=None, description="например: нейтрально, дружелюбно")


class DescriptionResponse(BaseModel):
    description: str


@router.post("/generate-description", response_model=DescriptionResponse)
async def generate_description(req: DescriptionRequest) -> DescriptionResponse:
    settings = get_settings()
    parts = [
        f"Название: {req.title}",
        f"Ингредиенты: {', '.join(req.ingredients) if req.ingredients else '—'}",
        f"Шаги: {' | '.join(req.steps) if req.steps else '—'}",
        f"Теги: {', '.join(req.tags) if req.tags else '—'}",
    ]
    if req.tone:
        parts.append(f"Тон: {req.tone}")
    user_content = "\n".join(parts)
    messages = [{"role": "user", "content": user_content}]
    try:
        text = await ollama_chat(messages, system=DESCRIPTION_SYSTEM)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Ollama HTTP error: {e.response.status_code}") from e
    except httpx.RequestError as e:
        if not settings.mock_llm:
            raise HTTPException(
                status_code=503,
                detail="Не удалось подключиться к Ollama. Запустите Ollama или установите MOCK_LLM=true.",
            ) from e
        raise
    return DescriptionResponse(description=text)
