"""
User statistics.
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from db.supabase_client import get_or_create_user, get_user_stats
from utils.keyboards import main_reply_keyboard

router = Router()


async def send_stats(message: Message, telegram_id: int, username: str | None):
    db_user = await get_or_create_user(telegram_id, username)
    stats = await get_user_stats(db_user["id"])

    if stats["total"] == 0:
        text = (
            "📊 <b>Your Statistics</b>\n\n"
            "<i>No translations yet.</i>\n\n"
            "🚀 Start practicing to see your progress here!"
        )
    else:
        avg = stats["avg"]
        if avg >= 85:
            status = "Strong ⚡"
        elif avg >= 65:
            status = "Steady 📈"
        else:
            status = "Building up 🌱"

        text = (
            "📊 <b>Your Statistics</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Total translations:</b> {stats['total']}\n"
            f"• <b>Average score:</b> {avg}/100 ({status})\n"
            f"• <b>Best score:</b> {stats['best']}/100"
        )

    await message.answer(text, reply_markup=main_reply_keyboard(), parse_mode="HTML")


@router.message(Command("stats"))
@router.message(F.text == "Statistics")
async def cmd_stats(message: Message):
    await send_stats(message, message.from_user.id, message.from_user.username)


@router.callback_query(F.data == "stats")
async def callback_stats(callback: CallbackQuery):
    await send_stats(
        callback.message,
        callback.from_user.id,
        callback.from_user.username,
    )
    await callback.answer()
