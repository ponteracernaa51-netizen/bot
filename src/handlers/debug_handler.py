# src/handlers/debug_handler.py

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def debug_all_updates_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Этот обработчик логирует АБСОЛЮТНО ВСЕ входящие апдейты.
    """
    
    logger.info("="*50)
    logger.info(">>> DEBUG: ПОЛУЧЕН НОВЫЙ UPDATE <<<")
    
    if update.message:
        logger.info(f"Тип: Message, Текст: '{update.message.text}'")
    elif update.callback_query:
        logger.info(f"Тип: CallbackQuery, Данные: '{update.callback_query.data}'")
    else:
        logger.info(f"Тип: {type(update)}")
        
    logger.info(f"Полный объект Update: {update.to_json()}")
    logger.info("="*50)