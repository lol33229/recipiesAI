import httpx

from app.config import get_settings


async def ollama_chat(messages: list[dict], system: str | None = None) -> str:
    settings = get_settings()
    if settings.mock_llm:
        return _mock_reply(messages, system)

    payload_messages = []
    if system:
        payload_messages.append({"role": "system", "content": system})
    payload_messages.extend(messages)

    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    body = {
        "model": settings.ollama_model,
        "messages": payload_messages,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
        r = await client.post(url, json=body)
        r.raise_for_status()
        data = r.json()
    msg = data.get("message") or {}
    return (msg.get("content") or "").strip()


def _mock_reply(messages: list[dict], system: str | None) -> str:
    last = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    return f"[MOCK LLM] Эхо: {last[:200]}{'…' if len(last) > 200 else ''}"
