# bot.py

import asyncio
import sys

# Этот блок абсолютно необходим. Оставляем его в самом верху.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv
load_dotenv()

import logging

from telegram.ext import Application, ApplicationBuilder

from src.core.config import settings
from src.handlers.common import register_handlers
from src.scheduler.scheduler_setup import setup_jobs

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Эта функция остается без изменений.
async def post_init_tasks(application: Application) -> None:
    logger.info("Настройка фоновых задач (планировщик)...")
    setup_jobs(application)
    logger.info("Фоновые задачи успешно настроены.")


# ==================== НАЧАЛО ФИНАЛЬНОГО ИСПРАВЛЕНИЯ ====================
# Мы полностью переписываем функцию main, чтобы использовать явный контроль
# над жизненным циклом приложения вместо проблемного run_polling().
async def main() -> None:
    """Основная функция для запуска бота."""
    
    # 1. Создаем, но не запускаем приложение.
    application = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .post_init(post_init_tasks)
        .build()
    )

    # 2. Регистрируем все обработчики.
    register_handlers(application)

    # 3. Используем менеджер контекста `async with`.
    # Он автоматически вызовет application.initialize() при входе
    # и application.shutdown() при выходе.
    async with application:
        logger.info("Запуск polling'а...")
        # Явно запускаем получение обновлений. Это неблокирующая операция.
        await application.start()
        await application.updater.start_polling()

        # Держим программу работающей, пока ее не прервут (например, Ctrl+C)
        await asyncio.Future()

        # Эти команды выполнятся после прерывания
        logger.info("Остановка polling'а...")
        await application.updater.stop()
        await application.stop()
        logger.info("Бот успешно остановлен.")

# ===================== КОНЕЦ ФИНАЛЬНОГО ИСПРАВЛЕНИЯ =====================


# Входная точка остается стандартной и самой правильной.
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Получен сигнал для остановки бота.")