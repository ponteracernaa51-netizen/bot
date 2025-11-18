# src/handlers/callback_dispatcher.py

from telegram import Update
from telegram.ext import ContextTypes

from .profile import profile_callback_handler
from .settings import settings_callback_handler
from .training import training_callback_handler


async def main_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Главный обработчик, который распределяет все callback-запросы
    по нужным функциям в зависимости от префикса в callback_data.
    """
    query = update.callback_query
    
    # Мы используем ":" как разделитель
    prefix = query.data.split(':')[0]

    # ==================== ИСПРАВЛЕННАЯ ЛОГИКА ЗДЕСЬ ====================
    if prefix == "profile":
        await profile_callback_handler(update, context)
        
    elif prefix == "settings":
        await settings_callback_handler(update, context)
        
    elif query.data in ["next_phrase", "change_topic"]:
        # Обрабатываем кнопки из тренировки, у которых нет префикса
        await training_callback_handler(update, context)
        
    else:
        # Если ни один раздел не подошел, просто отвечаем на колбэк
        await query.answer("Неизвестная команда.")
    # ===================================================================