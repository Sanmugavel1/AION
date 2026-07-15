"""
AION LLM Client — OpenAI / Claude-compatible language model interface
Provides structured completion and streaming capabilities
"""
from __future__ import annotations

import json
from typing import Any, AsyncIterator, Optional

import httpx
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import LLMError
from app.core.logging import get_logger

logger = get_logger(__name__)

_openai_client: Optional[AsyncOpenAI] = None

# Groq exposes an OpenAI-compatible API, so the same SDK works — just point
# base_url at Groq and use a Groq model name instead of OpenAI's.
_PROVIDER_CONFIG = {
    "groq": {"base_url": "https://api.groq.com/openai/v1", "api_key_attr": "GROQ_API_KEY", "model_attr": "GROQ_MODEL"},
    "openai": {"base_url": None, "api_key_attr": "OPENAI_API_KEY", "model_attr": "OPENAI_MODEL"},
}


def get_llm_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        provider = _PROVIDER_CONFIG.get(settings.LLM_PROVIDER, _PROVIDER_CONFIG["openai"])
        _openai_client = AsyncOpenAI(
            api_key=getattr(settings, provider["api_key_attr"]),
            base_url=provider["base_url"],
            timeout=60.0,
        )
    return _openai_client


def default_model() -> str:
    provider = _PROVIDER_CONFIG.get(settings.LLM_PROVIDER, _PROVIDER_CONFIG["openai"])
    return getattr(settings, provider["model_attr"])


async def complete(
    prompt: str,
    system: str = "You are Axon, AION's AI organizational intelligence analyst.",
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> str:
    """
    Single-turn LLM completion. Returns the assistant message text.
    """
    client = get_llm_client()
    _model = model or default_model()
    kwargs: dict[str, Any] = {
        "model": _model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error("LLM completion failed", error=str(e), model=_model)
        raise LLMError(f"LLM completion failed: {e}") from e


async def chat(
    messages: list[dict[str, str]],
    system: str = "You are Axon, AION's AI organizational intelligence analyst.",
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 1536,
) -> str:
    """
    Multi-turn chat completion. `messages` is a list of {"role", "content"}
    dicts (role "user"/"assistant") for prior conversation turns, NOT
    including the system prompt.
    """
    client = get_llm_client()
    _model = model or default_model()
    try:
        response = await client.chat.completions.create(
            model=_model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system}, *messages],
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error("LLM chat failed", error=str(e), model=_model)
        raise LLMError(f"LLM chat failed: {e}") from e


async def complete_json(
    prompt: str,
    system: str = "You are Axon, AION's AI analyst. Always respond with valid JSON.",
    model: Optional[str] = None,
) -> dict:
    """Complete and parse a JSON response from the LLM."""
    text = await complete(prompt, system=system, model=model, json_mode=True)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning("LLM returned invalid JSON, attempting extraction", error=str(e))
        # Attempt to extract JSON block
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
        raise LLMError(f"LLM returned non-JSON response: {text[:200]}") from e


async def generate_summary(content: str, max_words: int = 150) -> str:
    """Generate a concise summary of organizational content."""
    prompt = f"Summarize the following in under {max_words} words for an executive audience:\n\n{content}"
    return await complete(prompt, temperature=0.2)


async def generate_recommendations(
    context: str, focus_area: str, count: int = 5
) -> list[str]:
    """Generate actionable recommendations given organizational context."""
    prompt = (
        f"Focus area: {focus_area}\n\n"
        f"Context:\n{context}\n\n"
        f"Generate exactly {count} specific, actionable recommendations. "
        f"Return as a JSON array of strings."
    )
    result = await complete_json(prompt)
    items = result.get("recommendations", result.get("items", []))
    if isinstance(items, list):
        return [str(r) for r in items[:count]]
    return []


async def analyze_disease_pattern(disease_type: str, evidence: dict) -> str:
    """Generate natural-language analysis of an organizational disease."""
    prompt = (
        f"Organizational Disease: {disease_type}\n"
        f"Evidence: {json.dumps(evidence, indent=2)}\n\n"
        "Explain this disease pattern, its root causes, and immediate risks in 3-4 sentences."
    )
    return await complete(prompt, temperature=0.2)


async def generate_board_narrative(metrics: dict, risks: list, opportunities: list) -> str:
    """Generate a board-level executive narrative from structured data."""
    prompt = (
        f"Organizational Intelligence Metrics:\n{json.dumps(metrics, indent=2)}\n\n"
        f"Top Risks: {json.dumps(risks, indent=2)}\n\n"
        f"Top Opportunities: {json.dumps(opportunities, indent=2)}\n\n"
        "Write a 3-paragraph executive briefing suitable for a board of directors. "
        "Be factual, concise, and focus on business impact."
    )
    return await complete(prompt, temperature=0.4, max_tokens=1536)


async def close_llm_client() -> None:
    global _openai_client
    if _openai_client:
        await _openai_client.close()
        _openai_client = None
    logger.info("LLM client closed")
