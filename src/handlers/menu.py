from telegram import Update
from telegram.ext import ContextTypes

from .profile import profile_handler as show_profile
from .settings import settings_handler as settings_menu
from .training import start_training


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Route messages from the main menu reply keyboard to appropriate handlers.
    """
    text = update.message.text

    if text == "💪 Тренировка":
        await start_training(update, context)
    elif text == "👤 Профиль":
        await show_profile(update, context)
    elif text == "⚙️ Настройки":
        await settings_menu(update, context)