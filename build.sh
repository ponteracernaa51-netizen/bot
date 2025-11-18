#!/usr/bin/env bash
# exit on error
set -o errexit

# Установка зависимостей
pip install -r requirements.txt

# Запуск миграций Alembic
# Мы явно указываем путь к конфигурационному файлу
alembic -c alembic.ini upgrade head
