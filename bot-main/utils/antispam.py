"""
Simple in-memory anti-spam middleware.

It is intentionally local-process only. For multiple bot replicas, move this
state to Redis or Supabase RPC.
"""

import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from config import ANTISPAM_MAX_EVENTS, ANTISPAM_WINDOW_SECONDS


class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self):
        self._events: dict[int, deque[float]] = defaultdict(deque)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        now = time.monotonic()
        bucket = self._events[user.id]
        while bucket and now - bucket[0] > ANTISPAM_WINDOW_SECONDS:
            bucket.popleft()

        if len(bucket) >= ANTISPAM_MAX_EVENTS:
            await self._reply(event)
            return None

        bucket.append(now)
        return await handler(event, data)

    async def _reply(self, event: TelegramObject) -> None:
        if isinstance(event, Message):
            await event.answer("Please slow down a little.")
        elif isinstance(event, CallbackQuery):
            await event.answer("Please slow down a little.", show_alert=False)
