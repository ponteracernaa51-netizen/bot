"""
AI-powered error explanation service.

Uses Groq API (llama-3.1-8b-instant) as primary provider — fast and free.
Falls back to Together.ai (Meta-Llama-3.1-8B) if Groq is unavailable.
Returns None gracefully if both providers fail, so the bot continues working.
"""

import asyncio
import logging

import httpx

from config import AI_TIMEOUT, GROQ_API_KEY, TOGETHER_API_KEY

logger = logging.getLogger(__name__)

_GROQ_URL    = "https://api.groq.com/openai/v1/chat/completions"
_TOGETHER_URL = "https://api.together.xyz/v1/chat/completions"

_GROQ_MODEL    = "llama-3.1-8b-instant"
_TOGETHER_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"


def _build_prompt(
    original_ru: str,
    original_uz: str,
    reference_english: str,
    user_answer: str,
    errors: list[str],
    level: str,
    phrase_lang: str = "ru",
) -> str:
    original = original_uz if phrase_lang == "uz" else original_ru
    lang_label = "Uzbek" if phrase_lang == "uz" else "Russian"
    errors_text = "\n".join(f"- {e}" for e in errors) if errors else "- No specific errors detected"

    return (
        f"You are an English tutor helping a {level} student.\n"
        f"Translate from {lang_label}: \"{original}\"\n"
        f"Correct translation: \"{reference_english}\"\n"
        f"Student answer: \"{user_answer}\"\n"
        f"Detected errors: {errors_text}\n\n"
        f"Instruction: In exactly 1 or 2 extremely short and clear sentences, point out the main error "
        f"and explain why the correct translation is preferred. Be direct and friendly. "
        f"Do not write introductory phrases. Keep it under 35 words. Write in English only."
    )


async def _call_api(url: str, api_key: str, model: str, prompt: str) -> str | None:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.4,
    }
    try:
        async with httpx.AsyncClient(timeout=AI_TIMEOUT) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.warning("AI provider %s failed: %s", url, exc)
        return None


async def explain_errors(
    original_ru: str,
    original_uz: str,
    reference_english: str,
    user_answer: str,
    errors: list[str],
    level: str,
    phrase_lang: str = "ru",
) -> str | None:
    """
    Returns an AI explanation string, or None if all providers failed.
    Never raises — the bot must continue working without AI.
    """
    prompt = _build_prompt(
        original_ru=original_ru,
        original_uz=original_uz,
        reference_english=reference_english,
        user_answer=user_answer,
        errors=errors,
        level=level,
        phrase_lang=phrase_lang,
    )

    # Try Groq first (fast, free tier)
    if GROQ_API_KEY:
        result = await _call_api(_GROQ_URL, GROQ_API_KEY, _GROQ_MODEL, prompt)
        if result:
            return result

    # Fallback: Together.ai
    if TOGETHER_API_KEY:
        result = await _call_api(_TOGETHER_URL, TOGETHER_API_KEY, _TOGETHER_MODEL, prompt)
        if result:
            return result

    logger.warning("All AI providers unavailable — skipping explanation")
    return None
