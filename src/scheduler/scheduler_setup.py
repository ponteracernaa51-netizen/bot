# src/scheduler/scheduler_setup.py

import logging
from telegram.ext import Application

from .jobs import send_daily_notifications

logger = logging.getLogger(__name__)

def setup_jobs(application: Application) -> None:
    """
    Настраивает повторяющиеся задачи с помощью встроенного JobQueue.
    """
    job_queue = application.job_queue

    # Убедимся, что задача с таким именем еще не добавлена
    if not job_queue.get_jobs_by_name("send_daily_notifications"):
        # Запускаем задачу send_daily_notifications каждые 60 секунд (для теста)
        # Задача начнется через 10 секунд после запуска бота
        job_queue.run_repeating(
            callback=send_daily_notifications,
            interval=60,  # 60 секунд. Для 24 часов используйте: 60 * 60 * 24
            first=10,     # Запустить через 10 секунд после старта
            name="send_daily_notifications",
        )
        logger.info("Задача 'send_daily_notifications' успешно добавлена в очередь.")
    else:
        logger.info("Задача 'send_daily_notifications' уже существует в очереди.")