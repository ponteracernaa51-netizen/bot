# main.py

import asyncio
import logging
import uvicorn
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application

from src.core.config import settings
from bot import setup_bot

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Настройка Вебхука ---
WEBHOOK_PATH = f"/{settings.bot_token}"
# Render предоставляет RENDER_EXTERNAL_URL автоматически.
# Если он не задан (локальный запуск), используется значение по умолчанию из config.py
WEBHOOK_URL = f"{settings.render_external_url.rstrip('/')}{WEBHOOK_PATH}"

# --- Создание экземпляров ---
ptb_app: Application = setup_bot()
fastapi_app = FastAPI()


@fastapi_app.on_event("startup")
async def on_startup():
    """Действия при запуске сервера: установка вебхука."""
    logger.info(f"Установка вебхука на URL: {WEBHOOK_URL}")
    await ptb_app.bot.set_webhook(
        url=WEBHOOK_URL,
        allowed_updates=Update.ALL_TYPES,
        secret_token=settings.webhook_secret  # Добавим секрет для безопасности
    )
    # Инициализируем приложение PTB
    await ptb_app.initialize()
    logger.info("Приложение PTB инициализировано.")


@fastapi_app.on_event("shutdown")
async def on_shutdown():
    """Действия при остановке сервера: удаление вебхука."""
    logger.info("Удаление вебхука...")
    await ptb_app.bot.delete_webhook()
    # Останавливаем приложение PTB
    await ptb_app.shutdown()
    logger.info("Приложение PTB остановлено.")


@fastapi_app.post(WEBHOOK_PATH)
async def handle_telegram_update(request: Request):
    """Принимает обновления от Telegram."""
    headers = request.headers
    # Проверяем секретный токен для безопасности
    if headers.get("X-Telegram-Bot-Api-Secret-Token") != settings.webhook_secret:
        return Response(status_code=403)
        
    body = await request.json()
    update = Update.de_json(data=body, bot=ptb_app.bot)
    await ptb_app.process_update(update)
    return Response(status_code=200)


@fastapi_app.get("/")
def health_check():
    """Проверка работоспособности."""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:fastapi_app", host="0.0.0.0", port=8000, reload=True)
