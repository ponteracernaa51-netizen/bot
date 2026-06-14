"""
Supabase access layer.

The official Supabase client is synchronous, so every database call is
wrapped with asyncio.to_thread to avoid blocking aiogram's event loop.
"""

import asyncio
import random
import re
import time
from typing import Optional

from supabase import Client, create_client

from config import (
    LEVELS_FALLBACK,
    PHRASE_SIMILARITY_THRESHOLD,
    SUPABASE_KEY,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_URL,
)

_client: Client | None = None

# ─── Simple in-memory cache for levels ───────────────────────
_levels_cache: dict[str, str] | None = None
_levels_cache_ts: float = 0.0
_LEVELS_TTL = 600  # 10 минут


def get_client() -> Client:
    global _client
    if _client is None:
        key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY
        _client = create_client(SUPABASE_URL, key)
    return _client


async def _run_db(fn):
    return await asyncio.to_thread(fn)


# ─── Helpers ──────────────────────────────────────────────────

def _phrase_key(text: str) -> str:
    value = text.lower()
    value = re.sub(r"[^a-z0-9\s']", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _similarity(left: str, right: str) -> float:
    try:
        from rapidfuzz import fuzz

        left_key = _phrase_key(left)
        right_key = _phrase_key(right)
        return float(
            max(
                fuzz.token_set_ratio(left_key, right_key),
                fuzz.token_sort_ratio(left_key, right_key),
                fuzz.partial_ratio(left_key, right_key),
            )
        )
    except Exception:
        left_words = set(_phrase_key(left).split())
        right_words = set(_phrase_key(right).split())
        if not left_words or not right_words:
            return 0.0
        return 100.0 * len(left_words & right_words) / len(left_words | right_words)


def _normalize_phrase_row(row: dict, alternative_answers: list[str] | None = None) -> dict:
    row.setdefault("alternative_answers", alternative_answers or [])
    return row


# ─── Levels ───────────────────────────────────────────────────

async def get_levels() -> dict[str, str]:
    """Return {code: description} from DB, with in-memory TTL cache.
    Falls back to LEVELS_FALLBACK if DB is unavailable."""
    global _levels_cache, _levels_cache_ts

    now = time.monotonic()
    if _levels_cache is not None and (now - _levels_cache_ts) < _LEVELS_TTL:
        return _levels_cache

    def query():
        res = (
            get_client()
            .table("levels")
            .select("code, name_en, description")
            .eq("is_active", True)
            .order("sort_order")
            .execute()
        )
        return res.data or []

    try:
        rows = await _run_db(query)
        if rows:
            result = {r["code"]: f"{r['name_en']} — {r['description']}" for r in rows}
            _levels_cache = result
            _levels_cache_ts = now
            return result
    except Exception:
        pass

    return LEVELS_FALLBACK


async def get_level_codes() -> list[str]:
    """Return ordered list of active level codes (e.g. ['A2','B1','B2','C1'])."""
    levels = await get_levels()
    return list(levels.keys())


# ─── Users ────────────────────────────────────────────────────

async def get_or_create_user(telegram_id: int, username: str | None) -> dict:
    def query():
        db = get_client()
        res = (
            db.table("users")
            .select("id, telegram_id, username")
            .eq("telegram_id", telegram_id)
            .limit(1)
            .execute()
        )
        if res.data:
            return res.data[0]
        new = (
            db.table("users")
            .insert({"telegram_id": telegram_id, "username": username or ""})
            .execute()
        )
        return new.data[0]

    return await _run_db(query)


# ─── Topics ───────────────────────────────────────────────────

async def get_topics() -> list[dict]:
    def query():
        return (
            get_client()
            .table("topics")
            .select("id, name_ru, name_uz, emoji")
            .eq("is_active", True)
            .order("name_ru")
            .execute()
            .data
            or []
        )

    return await _run_db(query)


async def get_topic_by_id(topic_id: int) -> dict | None:
    def query():
        res = (
            get_client()
            .table("topics")
            .select("id, name_ru, name_uz, emoji")
            .eq("id", topic_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    return await _run_db(query)


# ─── Phrases ──────────────────────────────────────────────────

async def save_phrase(
    topic_id: int,
    text_ru: str,
    text_uz: str,
    english_answer: str,
    level: str,
    alternative_answers: list[str] | None = None,
) -> dict:
    payload = {
        "topic_id": topic_id,
        "text_ru": text_ru,
        "text_uz": text_uz,
        "english_answer": english_answer,
        "alternative_answers": alternative_answers or [],
        "phrase_key": _phrase_key(english_answer),
        "level": level,
    }

    def query():
        db = get_client()
        existing_candidates = (
            db.table("phrases")
            .select("id, text_ru, text_uz, english_answer, alternative_answers, level")
            .eq("topic_id", topic_id)
            .eq("level", level)
            .limit(100)
            .execute()
            .data
            or []
        )
        for candidate in existing_candidates:
            score = _similarity(english_answer, candidate["english_answer"])
            if score >= PHRASE_SIMILARITY_THRESHOLD:
                return _normalize_phrase_row(candidate, alternative_answers)

        try:
            existing = (
                db.table("phrases")
                .select("id, text_ru, text_uz, english_answer, alternative_answers, level")
                .eq("topic_id", topic_id)
                .eq("level", level)
                .eq("phrase_key", payload["phrase_key"])
                .limit(1)
                .execute()
            )
            if existing.data:
                return _normalize_phrase_row(existing.data[0], alternative_answers)
        except Exception:
            existing = (
                db.table("phrases")
                .select("id, text_ru, text_uz, english_answer, alternative_answers, level")
                .eq("topic_id", topic_id)
                .eq("level", level)
                .eq("english_answer", english_answer)
                .limit(1)
                .execute()
            )
            if existing.data:
                return _normalize_phrase_row(existing.data[0], alternative_answers)

        try:
            res = db.table("phrases").insert(payload).execute()
        except Exception:
            try:
                existing = (
                    db.table("phrases")
                    .select("id, text_ru, text_uz, english_answer, alternative_answers, level")
                    .eq("topic_id", topic_id)
                    .eq("level", level)
                    .eq("phrase_key", payload["phrase_key"])
                    .limit(1)
                    .execute()
                )
                if existing.data:
                    return _normalize_phrase_row(existing.data[0], alternative_answers)
            except Exception:
                pass

            fallback = dict(payload)
            fallback.pop("alternative_answers", None)
            fallback.pop("phrase_key", None)
            try:
                res = db.table("phrases").insert(fallback).execute()
            except Exception as second_error:
                raise RuntimeError(
                    "Could not save phrase to Supabase. "
                    "Add SUPABASE_SERVICE_ROLE_KEY or configure RLS insert policy for phrases."
                ) from second_error

        phrase = res.data[0]
        return _normalize_phrase_row(phrase, alternative_answers)

    return await _run_db(query)


async def get_recent_phrase_answers(
    topic_id: int,
    level: str,
    limit: int = 25,
) -> list[str]:
    def query():
        res = (
            get_client()
            .table("phrases")
            .select("english_answer")
            .eq("topic_id", topic_id)
            .eq("level", level)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [row["english_answer"] for row in (res.data or []) if row.get("english_answer")]

    return await _run_db(query)


# ─── Unique phrase (без повторов) ────────────────────────────

async def mark_phrase_seen(user_id: int, phrase_id: int, topic_id: int, level: str) -> None:
    """Записываем факт просмотра фразы пользователем."""
    def query():
        try:
            get_client().table("user_phrase_history").insert(
                {
                    "user_id": user_id,
                    "phrase_id": phrase_id,
                    "topic_id": topic_id,
                    "level": level,
                }
            ).execute()
        except Exception as e:
            err_msg = str(e)
            # 23505 is PostgreSQL unique constraint violation code
            if "23505" not in err_msg and "duplicate key" not in err_msg.lower():
                logger.error("Failed to mark phrase %s seen for user %s: %s", phrase_id, user_id, e)

    await _run_db(query)


async def _reset_phrase_history(user_id: int, topic_id: int, level: str) -> None:
    """Сбросить историю просмотров — когда все фразы уже показаны."""
    def query():
        try:
            get_client().table("user_phrase_history").delete().eq("user_id", user_id).eq("topic_id", topic_id).eq("level", level).execute()
        except Exception as e:
            logger.error("Failed to reset phrase history for user %s, topic %s, level %s: %s", user_id, topic_id, level, e)

    await _run_db(query)


async def get_unique_phrase(user_id: int, topic_id: int, level: str) -> dict | None:
    """
    Возвращает случайную фразу, которую пользователь ещё не видел.
    Если все фразы пройдены — сбрасывает историю и начинает заново.
    Возвращает None если фраз вообще нет.
    """
    def _fetch_all():
        res = (
            get_client()
            .table("phrases")
            .select("id, text_ru, text_uz, english_answer, alternative_answers, level")
            .eq("topic_id", topic_id)
            .eq("level", level)
            .execute()
        )
        return res.data or []

    def _fetch_seen_ids():
        res = (
            get_client()
            .table("user_phrase_history")
            .select("phrase_id")
            .eq("user_id", user_id)
            .eq("topic_id", topic_id)
            .eq("level", level)
            .execute()
        )
        return {row["phrase_id"] for row in (res.data or [])}

    def query():
        all_phrases = _fetch_all()
        if not all_phrases:
            return None, False  # (phrase, was_reset)

        seen_ids = _fetch_seen_ids()
        unseen = [p for p in all_phrases if p["id"] not in seen_ids]

        if not unseen:
            # Все фразы просмотрены — вернём флаг для сброса
            return None, True

        phrase = random.choice(unseen)
        phrase.setdefault("alternative_answers", [])
        return phrase, False

    phrase, needs_reset = await _run_db(query)

    if needs_reset:
        await _reset_phrase_history(user_id, topic_id, level)
        # После сброса берём любую фразу
        phrase, _ = await _run_db(query)

    return phrase


# ─── Scores ───────────────────────────────────────────────────

async def save_score(
    user_id: int,
    phrase_id: int | None,
    user_answer: str,
    score: int,
    errors: list[str],
    feedback: str,
) -> dict:
    def query():
        res = (
            get_client()
            .table("scores")
            .insert(
                {
                    "user_id": user_id,
                    "phrase_id": phrase_id,
                    "user_answer": user_answer,
                    "score": score,
                    "errors_json": errors,
                    "feedback": feedback,
                }
            )
            .execute()
        )
        return res.data[0]

    return await _run_db(query)


async def get_user_stats(user_id: int) -> dict:
    def query():
        res = (
            get_client()
            .table("scores")
            .select("score")
            .eq("user_id", user_id)
            .execute()
        )
        scores = [row["score"] for row in (res.data or [])]
        if not scores:
            return {"total": 0, "avg": 0, "best": 0}
        return {
            "total": len(scores),
            "avg": round(sum(scores) / len(scores), 1),
            "best": max(scores),
        }

    return await _run_db(query)
