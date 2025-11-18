import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
# Функция вернет True, если файл .env был найден и загружен, иначе False
env_loaded = load_dotenv()

print(f"Файл .env найден и загружен: {env_loaded}\n")

# Пытаемся прочитать переменные
bot_token = os.getenv("BOT_TOKEN")
db_url = os.getenv("DATABASE_URL")
gemini_key = os.getenv("GEMINI_API_KEY")

print(f"BOT_TOKEN: {'Найден' if bot_token else '!!! НЕ НАЙДЕН !!!'}")
print(f"DATABASE_URL: {'Найден' if db_url else '!!! НЕ НАЙДЕН !!!'}")
print(f"GEMINI_API_KEY: {'Найден' if gemini_key else '!!! НЕ НАЙДЕН !!!'}")

# Показываем, какие переменные реально видит Pydantic-Settings
# (для этого нужна отдельная установка, но python-dotenv уже есть)
print("\n--- Проверка содержимого (первые 5 символов) ---")
if bot_token:
    print(f"BOT_TOKEN начинается с: {bot_token[:5]}...")
if db_url:
    print(f"DATABASE_URL начинается с: {db_url[:5]}...")
if gemini_key:
    print(f"GEMINI_API_KEY начинается с: {gemini_key[:5]}...")