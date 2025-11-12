import logging
import asyncio
import sys
from telegram import Update
from telegram.ext import Application
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

import config
import database
from handlers import start_handler, topic_handler, difficulty_handler, feedback_handler

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def post_init(application: Application):
    await database.connect_db()

async def post_shutdown(application: Application):
    await database.close_db_pool()

def main() -> None:
    if not config.TELEGRAM_TOKEN:
        logger.critical("TELEGRAM_TOKEN не найден! Завершение работы.")
        return

    application = (
        Application.builder()
        .token(config.TELEGRAM_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_handler.start)],
        states={
            config.SELECTING_LANG: [
                CallbackQueryHandler(topic_handler.select_language, pattern="^lang_"),
            ],
            config.SELECTING_TOPIC: [
                CallbackQueryHandler(topic_handler.select_topic, pattern="^topic_"),
            ],
            config.SELECTING_DIFFICULTY: [
                CallbackQueryHandler(difficulty_handler.select_difficulty, pattern="^difficulty_"),
                CallbackQueryHandler(topic_handler.back_to_topics, pattern="^back_to_topics$"),
            ],
            config.SELECTING_DIRECTION: [
                CallbackQueryHandler(difficulty_handler.select_direction, pattern="^direction_"),
                CallbackQueryHandler(topic_handler.back_to_topics, pattern="^back_to_topics$"),
            ],
            config.AWAITING_TRANSLATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_handler.handle_translation),
                CallbackQueryHandler(feedback_handler.next_phrase, pattern="^next_phrase$"),
                CallbackQueryHandler(topic_handler.back_to_topics, pattern="^change_topic$"),
            ],
        },
        fallbacks=[
            CommandHandler("start", start_handler.start),
            CommandHandler("cancel", start_handler.cancel)
        ],
    )

    application.add_handler(conv_handler)
    logger.info("Бот запускается...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()