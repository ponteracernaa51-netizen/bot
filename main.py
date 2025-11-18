# main.py

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application

from src.core.config import settings
from bot import setup_bot # Мы создадим этот файл/функцию на следующем шаге

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Переменные для вебхука ---
# URL должен быть вида https://your-app-name.onrender.com
# Render автоматически предоставит переменную окружения RENDER_EXTERNAL_URL
WEBHOOK_URL = f"{settings.render_external_url}/{settings.bot_token}"
WEBHOOK_PATH = f"/{settings.bot_token}"


# --- Создание экземпляров бота и FastAPI ---
# Создаем приложение бота, но не запускаем его
ptb_app: Application = setup_bot()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для управления жизненным циклом.
    Выполняется при старте и остановке сервера.
    """
    logger.info("Запуск приложения...")
    # Устанавливаем вебхук при старте
    await ptb_app.bot.set_webhook(url=WEBHOOK_URL, allowed_updates=Update.ALL_TYPES)
    logger.info(f"Вебхук установлен на URL: {WEBHOOK_URL}")
    yield
    # Отключаем вебхук при остановке
    logger.info("Остановка приложения...")
    await ptb_app.bot.delete_webhook()
    logger.info("Вебхук удален.")

# Создаем FastAPI приложение с lifespan-менеджером
fastapi_app = FastAPI(lifespan=lifespan)


@fastapi_app.post(WEBHOOK_PATH)
async def handle_telegram_update(request: Request):
    """
    Принимает обновления от Telegram и передает их в ptb_app.
    """
    body = await request.json()
    update = Update.de_json(data=body, bot=ptb_app.bot)
    await ptb_app.process_update(update)
    return Response(status_code=200)


@fastapi_app.get("/")
def health_check():
    """Простая проверка работоспособности, чтобы Render был доволен."""
    return {"status": "ok"}


if __name__ == "__main__":
    # Эта часть для локального тестирования
    uvicorn.run(
        "main:fastapi_app",
        host="0.0.0.0",
        port=8000,
        reload=True # Автоматическая перезагрузка при изменениях кода
    )
