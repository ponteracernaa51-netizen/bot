import logging
from datetime import datetime

from telegram import Bot
from telegram.error import Forbidden

import src.db.repository as repository
import src.utils.texts as texts

logger = logging.getLogger(__name__)


async def send_daily_notifications(bot: Bot) -> None:
    """
    Send daily notifications to users whose notification time matches the current time.
    Fetches eligible users from the database and sends a reminder message.
    Handles cases where users have blocked the bot by disabling their notifications.
    This function is designed to be run periodically by APScheduler.
    """
    current_time = datetime.utcnow().time().replace(second=0, microsecond=0)
    logger.info(f"Running notification job for time: {current_time}")

    telegram_ids = await repository.get_users_for_notification(current_time=current_time)

    if not telegram_ids:
        logger.info("No users eligible for notifications at this time.")
        return

    logger.info(f"Sending notifications to {len(telegram_ids)} users.")

    for telegram_id in telegram_ids:
        try:
            notification_text = texts.MESSAGES["notification_text"]["ru"]
            await bot.send_message(chat_id=telegram_id, text=notification_text)
            logger.info(f"Notification sent successfully to user {telegram_id}")
        except Forbidden:
            logger.warning(f"User {telegram_id} has blocked the bot. Disabling notifications for them.")
            await repository.update_user(telegram_id, notifications_enabled=False)
        except Exception as e:
            logger.error(f"Failed to send message to {telegram_id}: {e}")