import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.llm import ollama_chat
from app.services.recipe_store import get_recipe

router = APIRouter(prefix="/api/chat", tags=["chat"])

CHAT_SYSTEM = """Ты ИИ-помощник кулинарного сервиса. Отвечай по-русски, кратко и по делу.
Помогаешь с продуктами, рецептами и готовкой. Не выдумывай опасные советы (например сырой мясо/яйца без термообработки)."""


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    recipe_id: str | None = None


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    settings = get_settings()
    messages = [m.model_dump() for m in req.messages]
    if req.recipe_id:
        recipe = get_recipe(req.recipe_id)
        if recipe:
            recipe_context = (
                f"Контекст рецепта:\n"
                f"- ID: {recipe.recipe_id}\n"
                f"- Название: {recipe.title}\n"
                f"- Ингредиенты: {', '.join([f'{x.name} ({x.grams}г)' for x in recipe.ingredients])}\n"
                f"- КБЖУ на 100г: {recipe.nutrition_per_100g}\n"
                f"- Шаги: {' | '.join(recipe.steps) if recipe.steps else '—'}"
            )
            messages.insert(0, {"role": "user", "content": recipe_context})
    try:
        reply = await ollama_chat(messages, system=CHAT_SYSTEM)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Ollama HTTP error: {e.response.status_code}") from e
    except httpx.RequestError as e:
        if not settings.mock_llm:
            raise HTTPException(
                status_code=503,
                detail="Не удалось подключиться к Ollama. Запустите Ollama или установите MOCK_LLM=true.",
            ) from e
        raise
    return ChatResponse(reply=reply)
