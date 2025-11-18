# src/core/config.py

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Управляет конфигурацией проекта, автоматически загружая
    и валидируя переменные из .env файла (для локальной разработки)
    или из переменных окружения (на сервере).
    """
    
    # --- Основные секреты ---
    bot_token: str
    database_url: str
    gemini_api_key: str

    # --- Настройки для Webhook на Render ---
    # Эта переменная будет автоматически предоставлена Render.
    # `Field` используется для указания, что мы ищем переменную окружения RENDER_EXTERNAL_URL.
    # `default` нужен для того, чтобы код не падал при локальном запуске,
    # где этой переменной окружения нет.
    render_external_url: str = Field(default="http://localhost:8000", env="RENDER_EXTERNAL_URL")

    class Config:
        # Указываем pydantic-settings, что нужно искать файл .env
        env_file = ".env"
        env_file_encoding = "utf-8"


# Создаем единственный экземпляр настроек, который будет использоваться во всем проекте.
settings = Settings()
