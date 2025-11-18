# src/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Управляет конфигурацией проекта, автоматически загружая
    и валидируя переменные из .env файла.
    """
    bot_token: str
    database_url: str
    gemini_api_key: str

    class Config:
        # Указываем pydantic-settings, что нужно искать файл .env
        env_file = ".env"
        env_file_encoding = "utf-8"


# Создаем единственный экземпляр настроек, который будет использоваться во всем проекте
settings = Settings()