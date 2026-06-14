"""
Keyboards for the Telegram bot.
Level-related keyboards are async because levels are loaded from the database.
"""

from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.supabase_client import get_levels


DIRECTION_LABELS = {
    "ru": "Russian → English",
    "uz": "Uzbek → English",
}


def direction_label(direction: str) -> str:
    return DIRECTION_LABELS.get(direction, DIRECTION_LABELS["ru"])


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Practice"), KeyboardButton(text="Settings")],
            [KeyboardButton(text="Statistics"), KeyboardButton(text="Repeat mistakes")],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Choose an action or type your translation",
    )


def settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Translation direction", callback_data="settings:direction")
    builder.button(text="Difficulty level",      callback_data="settings:level")
    builder.button(text="Start practice",        callback_data="start_practice")
    builder.adjust(1)
    return builder.as_markup()


async def settings_level_keyboard(selected_level: str = "B1") -> InlineKeyboardMarkup:
    """Builds level-selection keyboard using levels from DB."""
    levels = await get_levels()
    builder = InlineKeyboardBuilder()
    for code, desc in levels.items():
        marker = "✅ " if code == selected_level else ""
        name = desc.split(" — ")[0]          # show only short name
        builder.button(
            text=f"{marker}{code} · {name}",
            callback_data=f"settings:level:{code}",
        )
    builder.button(text="← Back to settings", callback_data="settings")
    builder.adjust(1)
    return builder.as_markup()


def settings_direction_keyboard(selected_direction: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, label in DIRECTION_LABELS.items():
        marker = "✅ " if code == selected_direction else ""
        builder.button(
            text=f"{marker}{label}",
            callback_data=f"settings:direction:{code}",
        )
    builder.button(text="← Back to settings", callback_data="settings")
    builder.adjust(1)
    return builder.as_markup()


def topics_keyboard(topics: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for topic in topics:
        builder.button(
            text=f"{topic['emoji']} {topic['name_ru']}",
            callback_data=f"topic:{topic['id']}",
        )
    builder.adjust(2)
    return builder.as_markup()


async def levels_keyboard(topic_id: int, selected_level: str = "B1") -> InlineKeyboardMarkup:
    """Builds topic-level selection keyboard using levels from DB."""
    levels = await get_levels()
    builder = InlineKeyboardBuilder()
    for code, desc in levels.items():
        marker = "✅ " if code == selected_level else ""
        name = desc.split(" — ")[0]
        builder.button(
            text=f"{marker}{code} · {name}",
            callback_data=f"level:{topic_id}:{code}",
        )
    builder.button(text="← Back to topics", callback_data="back:topics")
    builder.adjust(2, 1)
    return builder.as_markup()


def after_answer_keyboard(
    topic_id: int | None,
    level: str,
    include_repeat: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if include_repeat:
        builder.button(text="🔁 Repeat mistakes", callback_data="repeat_errors")
    builder.button(
        text="▶️ Next phrase",
        callback_data=f"next:{topic_id or 0}:{level}",
    )
    builder.button(text="📚 Change topic", callback_data="back:topics")
    builder.adjust(1)
    return builder.as_markup()
