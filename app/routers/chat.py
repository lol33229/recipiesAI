import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.llm import ollama_chat

router = APIRouter(prefix="/api/chat", tags=["chat"])

CHAT_SYSTEM = """Ты ИИ-помощник кулинарного сервиса. Отвечай по-русски, кратко и по делу.
Помогаешь с продуктами, рецептами и готовкой. Не выдумывай опасные советы (например сырой мясо/яйца без термообработки)."""


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    settings = get_settings()
    messages = [m.model_dump() for m in req.messages]
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
