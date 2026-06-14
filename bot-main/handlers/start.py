"""
Start, main menu, settings, and topic selection.
"""

import logging
from html import escape

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from db.supabase_client import (
    get_level_codes,
    get_levels,
    get_or_create_user,
    get_topic_by_id,
    get_topics,
)
from utils.keyboards import (
    direction_label,
    levels_keyboard,
    main_reply_keyboard,
    settings_direction_keyboard,
    settings_keyboard,
    settings_level_keyboard,
    topics_keyboard,
)

router = Router()
logger = logging.getLogger(__name__)


DEFAULT_LEVEL     = "B1"
DEFAULT_DIRECTION = "ru"


class PracticeState(StatesGroup):
    choosing_topic  = State()
    choosing_level  = State()
    waiting_answer  = State()


async def _ensure_settings(state: FSMContext) -> dict:
    data = await state.get_data()
    updates: dict = {}
    if not data.get("level"):
        updates["level"] = DEFAULT_LEVEL
    if not data.get("phrase_lang"):
        updates["phrase_lang"] = DEFAULT_DIRECTION
    if updates:
        await state.update_data(**updates)
        data.update(updates)
    return data


async def _settings_text(level: str, direction: str) -> str:
    levels = await get_levels()
    level_desc = levels.get(level, level)
    return (
        "⚙️ <b>Settings Panel</b>\n\n"
        f"🔄 <b>Direction:</b> {direction_label(direction)}\n"
        f"📈 <b>Level:</b> {level} — <i>{level_desc}</i>\n\n"
        "Select an option below to adjust:"
    )


HELP_TEXT = (
    "ℹ️ <b>Available Commands:</b>\n\n"
    "📚 /practice — Choose topic & start practice\n"
    "⚙️ /settings — Change direction/level\n"
    "📊 /stats — View your progress & statistics\n"
    "🔁 /repeat — Retry the last phrase with errors\n"
    "❓ /help — Show this help message"
)


# ─── /start ──────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(level=DEFAULT_LEVEL, phrase_lang=DEFAULT_DIRECTION)

    await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )

    await message.answer(
        "🎓 <b>English Practice Bot</b>\n\n"
        "Improve your English by translating phrases from Russian or Uzbek!\n\n"
        "✨ <b>How it works:</b>\n"
        "• Select a topic and difficulty level.\n"
        "• Translate phrases; get instant grammar & meaning scores.\n"
        "• No repetition: practice unique phrases, tracked per session.\n"
        "• Get clear, short AI explanations of your errors!\n\n"
        "🚀 Press <b>Practice</b> below to start!",
        reply_markup=main_reply_keyboard(),
        parse_mode="HTML",
    )


# ─── /help ───────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, reply_markup=main_reply_keyboard(), parse_mode="HTML")


# ─── /menu ───────────────────────────────────────────────────

@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await _ensure_settings(state)
    await message.answer(
        "📲 <b>Main Menu</b>\n\nUse the reply keyboard below to control the bot.",
        reply_markup=main_reply_keyboard(),
        parse_mode="HTML",
    )


# ─── /settings ───────────────────────────────────────────────

@router.message(Command("settings"))
@router.message(F.text == "Settings")
async def cmd_settings(message: Message, state: FSMContext):
    data = await _ensure_settings(state)
    await message.answer(
        await _settings_text(data["level"], data["phrase_lang"]),
        reply_markup=settings_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "settings")
async def callback_settings(callback: CallbackQuery, state: FSMContext):
    data = await _ensure_settings(state)
    await callback.message.edit_text(
        await _settings_text(data["level"], data["phrase_lang"]),
        reply_markup=settings_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Level settings ──────────────────────────────────────────

@router.callback_query(F.data == "settings:level")
async def callback_settings_level(callback: CallbackQuery, state: FSMContext):
    data = await _ensure_settings(state)
    await callback.message.edit_text(
        "📈 <b>Difficulty Level</b>\n\nChoose how hard the next phrases should be.",
        reply_markup=await settings_level_keyboard(data["level"]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings:level:"))
async def callback_set_level(callback: CallbackQuery, state: FSMContext):
    level = callback.data.split(":")[2]
    valid_codes = await get_level_codes()
    if level not in valid_codes:
        await callback.answer("Unknown level", show_alert=True)
        return

    await state.update_data(level=level)
    data = await _ensure_settings(state)
    await callback.message.edit_text(
        await _settings_text(data["level"], data["phrase_lang"]),
        reply_markup=settings_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer(f"Level set to {level}")


# ─── Direction settings ───────────────────────────────────────

@router.callback_query(F.data == "settings:direction")
async def callback_settings_direction(callback: CallbackQuery, state: FSMContext):
    data = await _ensure_settings(state)
    await callback.message.edit_text(
        "🔄 <b>Translation Direction</b>\n\n"
        "Choose the language shown by the bot. "
        "Your answers must always be in English.",
        reply_markup=settings_direction_keyboard(data["phrase_lang"]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings:direction:"))
async def callback_set_direction(callback: CallbackQuery, state: FSMContext):
    direction = callback.data.split(":")[2]
    if direction not in {"ru", "uz"}:
        await callback.answer("Unknown direction", show_alert=True)
        return

    await state.update_data(phrase_lang=direction)
    data = await _ensure_settings(state)
    await callback.message.edit_text(
        await _settings_text(data["level"], data["phrase_lang"]),
        reply_markup=settings_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer(f"Direction set to {direction_label(direction)}")


# ─── Practice ────────────────────────────────────────────────

@router.message(Command("practice"))
@router.message(F.text == "Practice")
async def cmd_practice(message: Message, state: FSMContext):
    await _ensure_settings(state)
    await show_topics(message, state)


@router.callback_query(F.data == "start_practice")
async def start_practice(callback: CallbackQuery, state: FSMContext):
    await _ensure_settings(state)
    await show_topics(callback.message, state)
    await callback.answer()


async def show_topics(message: Message, state: FSMContext):
    topics = await get_topics()
    if not topics:
        await message.answer("No topics are available yet. Please load topics first.")
        return

    data = await _ensure_settings(state)
    await state.set_state(PracticeState.choosing_topic)
    await message.answer(
        "📚 <b>Select Topic</b>\n\n"
        f"🔄 Direction: <b>{direction_label(data['phrase_lang'])}</b>\n"
        f"📈 Level: <b>{data['level']}</b>\n\n"
        "Choose one of the topics below to start:",
        reply_markup=topics_keyboard(topics),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "back:topics")
async def back_to_topics(callback: CallbackQuery, state: FSMContext):
    await show_topics(callback.message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("topic:"))
async def topic_chosen(callback: CallbackQuery, state: FSMContext):
    topic_id = int(callback.data.split(":")[1])
    topic = await get_topic_by_id(topic_id)
    if not topic:
        await callback.answer("Topic not found", show_alert=True)
        return

    data = await _ensure_settings(state)
    await state.update_data(
        topic_id=topic_id,
        topic_name_ru=topic["name_ru"],
        topic_name_uz=topic["name_uz"],
    )
    await state.set_state(PracticeState.choosing_level)

    topic_name = topic["name_uz"] if data["phrase_lang"] == "uz" else topic["name_ru"]
    await callback.message.edit_text(
        f"{topic['emoji']} <b>{escape(topic_name)}</b>\n\n"
        f"🔄 Direction: <b>{direction_label(data['phrase_lang'])}</b>\n\n"
        "Confirm or change the level for this practice session:",
        reply_markup=await levels_keyboard(topic_id, data["level"]),
        parse_mode="HTML",
    )
    await callback.answer()
