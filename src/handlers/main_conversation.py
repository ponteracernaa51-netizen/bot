# src/handlers/main_conversation.py

from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from src.utils import texts, keyboards
from src.db import repository

# Импортируем ВСЕ функции, которые будут использоваться в диалогах
from .training import start_training
from .profile import (
    profile_start, edit_profile_menu, choose_topic, choose_level, choose_direction,
    save_topic, save_level, save_direction,
    SHOWING_PROFILE, EDITING_PROFILE, CHOOSING_TOPIC, CHOOSING_LEVEL, CHOOSING_DIRECTION
)
from .settings import (
    settings_start, toggle_notifications, repeat_errors, choose_language, save_language,
    SHOWING_SETTINGS, CHOOSING_LANGUAGE
)

# Определяем общее состояние для главного меню
MAIN_MENU = -1 # Используем -1 как специальное значение для возврата

async def start(update, context):
    user = await repository.get_or_create_user(update.effective_user.id)
    lang = user.language_code or 'ru'
    keyboard = keyboards.get_main_menu_keyboard(lang)
    await update.message.reply_text("Добро пожаловать!", reply_markup=keyboard)
    return MAIN_MENU

# Точка выхода из любого диалога
async def cancel(update, context):
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END

main_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        MAIN_MENU: [
            # Эти обработчики будут работать только в главном меню
            MessageHandler(filters.Regex(f"^({texts.BUTTONS['training']['ru']}|...)$"), start_training),
            MessageHandler(filters.Regex(f"^({texts.BUTTONS['profile']['ru']}|...)$"), profile_start),
            MessageHandler(filters.Regex(f"^({texts.BUTTONS['settings']['ru']}|...)$"), settings_start),
        ],
        # ... (все состояния из profile.py и settings.py)
    },
    fallbacks=[CommandHandler("start", start)], # /start в любом месте возвращает в главное меню
    per_message=False, per_user=True, per_chat=True, name="main_conversation", persistent=True,
)