# src/core/config.py
import secrets
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    bot_token: str
    database_url: str
    gemini_api_key: str
    
    render_external_url: str = Field(default="http://localhost:8000", env="RENDER_EXTERNAL_URL")
    
    # Новый секрет. Генерируется автоматически, если не задан.
    webhook_secret: str = Field(default_factory=secrets.token_hex)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
