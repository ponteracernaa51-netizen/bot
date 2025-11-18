# src/handlers/settings.py

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from src.db import repository
from src.utils import keyboards, texts

logger = logging.getLogger(__name__)

# Состояния
SHOWING_SETTINGS, CHOOSING_LANGUAGE = range(2)

async def _display_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await repository.get_user(update.effective_user.id)
    lang = user.language_code or 'ru'
    show_repeat_errors_button = True
    keyboard = keyboards.get_settings_keyboard(
        lang=lang,
        is_notifications_enabled=user.notifications_enabled,
        is_repeating_errors=user.is_repeating_errors
    )
    if update.callback_query:
        await update.callback_query.edit_message_text("⚙️ Настройки", reply_markup=keyboard)
    else:
        await update.message.reply_text("⚙️ Настройки", reply_markup=keyboard)

async def settings_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await _display_settings(update, context)
    return SHOWING_SETTINGS

async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = await repository.get_user(query.from_user.id)
    new_state = not user.notifications_enabled
    await repository.update_user(user.telegram_id, notifications_enabled=new_state)
    await _display_settings(update, context)
    return SHOWING_SETTINGS

async def repeat_errors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = await repository.get_user(query.from_user.id)
    lang = user.language_code or 'ru'
    if not all([user.topic_id, user.level_id]):
        await query.answer("Сначала выберите тему и уровень в профиле.", show_alert=True)
        return SHOWING_SETTINGS
    errors = await repository.get_phrases_for_repetition(user.id, user.topic_id, user.level_id)
    if not errors:
        await query.answer(texts.MESSAGES['no_errors_to_repeat'][lang], show_alert=True)
        return SHOWING_SETTINGS
    await repository.update_user(user.telegram_id, is_repeating_errors=True)
    await query.answer(texts.MESSAGES['repeat_errors_on'][lang], show_alert=True)
    await _display_settings(update, context)
    return SHOWING_SETTINGS

async def repeat_errors_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await repository.update_user(query.from_user.id, is_repeating_errors=False)
    lang = (await repository.get_user(query.from_user.id)).language_code or 'ru'
    await query.answer(texts.MESSAGES['repeat_errors_off_msg'][lang])
    await _display_settings(update, context)
    return SHOWING_SETTINGS

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = (await repository.get_user(query.from_user.id)).language_code or 'ru'
    keyboard = keyboards.get_language_keyboard(lang)
    await query.edit_message_text(texts.MESSAGES['choose_language'][lang], reply_markup=keyboard)
    return CHOOSING_LANGUAGE

async def save_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    new_lang = query.data.split(':')[2]
    telegram_id = query.from_user.id
    await repository.update_user(telegram_id, language_code=new_lang)
    await query.answer(texts.MESSAGES['language_updated'][new_lang])
    return await settings_start(update, context)

async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.message.delete()
    logger.info("Диалог настроек завершен.")
    return ConversationHandler.END

settings_conversation_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex(f"^({texts.BUTTONS['settings']['ru']}|{texts.BUTTONS['settings']['en']}|{texts.BUTTONS['settings']['uz']})$"),
            settings_start
        ),
    ],
    states={
        SHOWING_SETTINGS: [
            CallbackQueryHandler(toggle_notifications, pattern="^settings:toggle_notifications$"),
            CallbackQueryHandler(repeat_errors, pattern="^settings:repeat_errors$"),
            CallbackQueryHandler(repeat_errors_off, pattern="^settings:repeat_errors_off$"),
            CallbackQueryHandler(choose_language, pattern="^settings:edit_language$"),
        ],
        CHOOSING_LANGUAGE: [
            CallbackQueryHandler(save_language, pattern="^settings:lang:"),
            CallbackQueryHandler(settings_start, pattern="^settings:back$"),
        ],
    },
    fallbacks=[CommandHandler("start", end_conversation)],
    per_message=False,
    per_user=True,
    per_chat=True,
    allow_reentry=True,
)