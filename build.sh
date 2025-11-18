#!/usr/bin/env bash
# exit on error
set -o errexit

echo "--- Starting build script ---"

echo "Current directory: $(pwd)"
echo "Listing files in current directory:"
ls -la

# --- ВАЖНЫЙ БЛОК ---
# Проверяем, есть ли alembic.ini в текущей директории.
# Если нет, пытаемся найти его в поддиректории.
PROJECT_ROOT=$(pwd)
if [ ! -f "alembic.ini" ]; then
    echo "alembic.ini not found in $(pwd). Searching in subdirectories..."
    # Ищем alembic.ini в поддиректориях
    ALEMBIC_CONFIG_PATH=$(find . -name alembic.ini -print -quit)
    if [ -n "$ALEMBIC_CONFIG_PATH" ]; then
        # Нашли! Переходим в директорию, где он лежит.
        PROJECT_ROOT=$(dirname "$ALEMBIC_CONFIG_PATH")
        echo "Found alembic.ini at $ALEMBIC_CONFIG_PATH. Changing directory to $PROJECT_ROOT"
        cd "$PROJECT_ROOT"
    else
        echo "FATAL: alembic.ini not found anywhere. Build failed."
        exit 1
    fi
fi
# --------------------

echo "Current directory is now: $(pwd)"
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running Alembic migrations..."
# Запускаем миграции из правильной директории
alembic upgrade head

echo "--- Build script finished successfully ---"
