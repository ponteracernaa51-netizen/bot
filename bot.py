# bot.py

import logging
from telegram.ext import Application, ApplicationBuilder
from src.core.config import settings
from src.handlers.common import register_handlers
from src.scheduler.scheduler_setup import setup_jobs

logger = logging.getLogger(__name__)

def setup_bot() -> Application:
    """
    Создает, настраивает и возвращает экземпляр PTB Application.
    """
    logger.info("Настройка экземпляра бота...")
    
    application = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .post_init(post_init_tasks)
        .build()
    )

    register_handlers(application)
    
    logger.info("Экземпляр бота успешно настроен.")
    return application

async def post_init_tasks(application: Application) -> None:
    """
    Запускает фоновые задачи (планировщик) после инициализации бота.
    """
    logger.info("Настройка фоновых задач (планировщик)...")
    setup_jobs(application)
    logger.info("Фоновые задачи успешно настроены.")

# Весь код запуска (`async def main`, `if __name__ == "__main__"`) отсюда УДАЛЕН.
