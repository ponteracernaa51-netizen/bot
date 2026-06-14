"""
Loads ready-made phrases from Supabase with unique-per-user delivery.

Phrases are delivered without repetition: once a user has seen all phrases
for a given topic+level the history resets automatically and the cycle
restarts. AI generation is intentionally not used.
"""

import logging

from db.supabase_client import get_unique_phrase, mark_phrase_seen

logger = logging.getLogger(__name__)


class NoPhraseAvailable(Exception):
    pass


async def generate_phrase(
    user_id: int,
    topic_id: int,
    topic_name_ru: str,
    topic_name_uz: str,
    level: str,
) -> dict:
    """
    Returns a phrase that the user has not seen yet for this topic+level.
    Marks it as seen immediately so it won't repeat until the full cycle
    is exhausted and the history resets.
    """
    phrase = await get_unique_phrase(user_id=user_id, topic_id=topic_id, level=level)
    if not phrase:
        raise NoPhraseAvailable(
            f"No saved phrases for topic_id={topic_id}, level={level}"
        )

    # Mark as seen so the next call returns a different phrase
    await mark_phrase_seen(
        user_id=user_id,
        phrase_id=phrase["id"],
        topic_id=topic_id,
        level=level,
    )

    logger.info(
        "Phrase delivered: id=%s topic_id=%s level=%s user_id=%s",
        phrase["id"], topic_id, level, user_id,
    )
    return phrase
