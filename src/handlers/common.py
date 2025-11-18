# src/handlers/common.py

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from src.db import repository
from src.utils import keyboards, texts

from .profile import profile_conversation_handler
from .settings import settings_conversation_handler
from .training import handle_translation, training_callback_handler, start_training


async def start(update, context):
    user = await repository.get_or_create_user(update.effective_user.id)
    lang = user.language_code or 'ru'
    keyboard = keyboards.get_main_menu_keyboard(lang)
    await update.message.reply_text("Добро пожаловать!", reply_markup=keyboard)


def register_handlers(application: Application) -> None:
    # 1. Сначала регистрируем обработчики диалогов. Они имеют приоритет.
    application.add_handler(profile_conversation_handler)
    application.add_handler(settings_conversation_handler)

    # 2. Затем регистрируем остальные команды и кнопки меню
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(
        filters.Regex(f"^({texts.BUTTONS['training']['ru']}|{texts.BUTTONS['training']['en']}|{texts.BUTTONS['training']['uz']})$"),
        start_training
    ))
    
    # Обработчик для кнопок "Следующая фраза" и "Сменить тему"
    application.add_handler(CallbackQueryHandler(training_callback_handler, pattern="^(next_phrase|change_topic)$"))
    
    # 3. В самом конце регистрируем "жадный" обработчик для всех остальных текстов (переводов)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_translation
    ))