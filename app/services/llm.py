import httpx

from app.config import get_settings


async def llm_chat(messages: list[dict], system: str | None = None) -> str:
    """точка вызова LLM"""
    settings = get_settings()
    if settings.mock_llm:
        return _mock_reply(messages, system)

    payload_messages: list[dict] = []
    if system:
        payload_messages.append({"role": "system", "content": system})
    payload_messages.extend(messages)

    provider = settings.llm_provider
    if provider == "mistral":
        return await _openai_compatible_chat(
            base_url=settings.mistral_base_url,
            api_key=settings.mistral_api_key,
            model=settings.mistral_model,
            messages=payload_messages,
            provider_label="Mistral API",
        )
    if provider == "openrouter":
        headers = {"HTTP-Referer": "https://kulinarai.local", "X-Title": "KulinarAI"}
        return await _openai_compatible_chat(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            messages=payload_messages,
            provider_label="OpenRouter",
            extra_headers=headers,
        )
    return await _ollama_chat(payload_messages)


async def ollama_chat(messages: list[dict], system: str | None = None) -> str:
    """Обратная совместимость — делегирует в llm_chat."""
    return await llm_chat(messages, system=system)


async def _openai_compatible_chat(
    *,
    base_url: str,
    api_key: str | None,
    model: str,
    messages: list[dict],
    provider_label: str,
    extra_headers: dict[str, str] | None = None,
) -> str:
    if not api_key:
        raise ValueError(f"Не задан API-ключ для {provider_label} (см. .env)")

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)

    settings = get_settings()
    body = {"model": model, "messages": messages, "temperature": 0.7}

    async with httpx.AsyncClient(timeout=settings.llm_timeout_sec) as client:
        r = await client.post(url, json=body, headers=headers)
        r.raise_for_status()
        data = r.json()

    choices = data.get("choices") or []
    if not choices:
        raise ValueError(f"{provider_label}: пустой ответ")
    content = (choices[0].get("message") or {}).get("content") or ""
    return content.strip()


async def _ollama_chat(messages: list[dict]) -> str:
    settings = get_settings()
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    body = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=settings.llm_timeout_sec, trust_env=False) as client:
        r = await client.post(url, json=body)
        r.raise_for_status()
        data = r.json()
    msg = data.get("message") or {}
    return (msg.get("content") or "").strip()


def _mock_reply(messages: list[dict], system: str | None) -> str:
    last = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    return f"[MOCK LLM] Эхо: {last[:200]}{'…' if len(last) > 200 else ''}"
