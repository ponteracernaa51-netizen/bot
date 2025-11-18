# src/handlers/profile.py

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
from telegram.constants import ParseMode
from src.db import repository
from src.utils import texts, keyboards

logger = logging.getLogger(__name__)

# Состояния
SHOWING_PROFILE, EDITING_PROFILE, CHOOSING_TOPIC, CHOOSING_LEVEL, CHOOSING_DIRECTION = range(5)

async def _display_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, prefix_text: str = None):
    user = await repository.get_or_create_user(update.effective_user.id)
    lang = user.language_code or 'ru'
    
    avg_score = await repository.get_user_average_score(user.id)
    topic_name = "Не выбрана"
    if user.topic_id:
        topic = await repository.get_topic_by_id(user.topic_id)
        if topic: topic_name = getattr(topic, f'name_{lang}', topic.name_ru)
            
    level_name = "Не выбран"
    if user.level_id:
        level = await repository.get_level_by_id(user.level_id)
        if level: level_name = getattr(level, f'name_{lang}', level.name_ru)
            
    lang_display = {'ru': 'Русский', 'en': 'English', 'uz': "O'zbekcha"}.get(lang, lang.capitalize())
    direction_display = user.direction or "Не выбрано"

    profile_text = texts.MESSAGES['profile_format'][lang].format(
        lang=lang_display,
        topic=topic_name,
        level=level_name,
        avg_score=avg_score,
        direction=direction_display,
    )

    if prefix_text:
        profile_text = f"{prefix_text}\n\n{profile_text}"

    keyboard = keyboards.get_profile_keyboard(lang)

    if update.callback_query:
        await update.callback_query.edit_message_text(profile_text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    else:
        await update.message.reply_text(profile_text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

async def profile_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await _display_profile(update, context)
    return SHOWING_PROFILE

async def edit_profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = (await repository.get_user(query.from_user.id)).language_code or 'ru'
    keyboard = keyboards.get_profile_edit_keyboard(lang)
    await query.edit_message_text("Что вы хотите изменить?", reply_markup=keyboard)
    return EDITING_PROFILE

async def choose_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = (await repository.get_user(query.from_user.id)).language_code or 'ru'
    topics = await repository.get_topics()
    keyboard = keyboards.get_topics_keyboard(topics, lang)
    await query.edit_message_text(texts.MESSAGES['choose_topic'][lang], reply_markup=keyboard)
    return CHOOSING_TOPIC

async def choose_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = (await repository.get_user(query.from_user.id)).language_code or 'ru'
    levels = await repository.get_levels()
    keyboard = keyboards.get_levels_keyboard(levels, lang)
    await query.edit_message_text(texts.MESSAGES['choose_level'][lang], reply_markup=keyboard)
    return CHOOSING_LEVEL

async def choose_direction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = (await repository.get_user(query.from_user.id)).language_code or 'ru'
    keyboard = keyboards.get_directions_keyboard(lang)
    await query.edit_message_text(texts.MESSAGES['choose_direction'][lang], reply_markup=keyboard)
    return CHOOSING_DIRECTION

async def save_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    topic_id = int(query.data.split(':')[2])
    telegram_id = query.from_user.id
    await repository.update_user(telegram_id, topic_id=topic_id)
    lang = (await repository.get_user(telegram_id)).language_code or 'ru'
    await _display_profile(update, context, prefix_text=texts.MESSAGES['profile_updated'][lang])
    return SHOWING_PROFILE

async def save_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    level_id = int(query.data.split(':')[2])
    telegram_id = query.from_user.id
    await repository.update_user(telegram_id, level_id=level_id)
    lang = (await repository.get_user(telegram_id)).language_code or 'ru'
    await _display_profile(update, context, prefix_text=texts.MESSAGES['profile_updated'][lang])
    return SHOWING_PROFILE

async def save_direction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    direction = query.data.split(':')[2]
    telegram_id = query.from_user.id
    await repository.update_user(telegram_id, direction=direction)
    lang = (await repository.get_user(telegram_id)).language_code or 'ru'
    await _display_profile(update, context, prefix_text=texts.MESSAGES['profile_updated'][lang])
    return SHOWING_PROFILE

async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.delete()
    logger.info("Диалог профиля завершен.")
    return ConversationHandler.END

profile_conversation_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex(f"^({texts.BUTTONS['profile']['ru']}|{texts.BUTTONS['profile']['en']}|{texts.BUTTONS['profile']['uz']})$"),
            profile_start
        ),
    ],
    states={
        SHOWING_PROFILE: [CallbackQueryHandler(edit_profile_menu, pattern="^profile:edit$")],
        EDITING_PROFILE: [
            CallbackQueryHandler(choose_topic, pattern="^profile:edit_topic$"),
            CallbackQueryHandler(choose_level, pattern="^profile:edit_level$"),
            CallbackQueryHandler(choose_direction, pattern="^profile:edit_direction$"),
            CallbackQueryHandler(profile_start, pattern="^profile:show$"),
        ],
        CHOOSING_TOPIC: [
            CallbackQueryHandler(save_topic, pattern="^profile:topic:"),
            CallbackQueryHandler(edit_profile_menu, pattern="^profile:edit$"),
        ],
        CHOOSING_LEVEL: [
            CallbackQueryHandler(save_level, pattern="^profile:level:"),
            CallbackQueryHandler(edit_profile_menu, pattern="^profile:edit$"),
        ],
        CHOOSING_DIRECTION: [
            CallbackQueryHandler(save_direction, pattern="^profile:direction:"),
            CallbackQueryHandler(edit_profile_menu, pattern="^profile:edit$"),
        ],
    },
    fallbacks=[CommandHandler("start", end_conversation)],
    per_message=False,
    per_user=True,
    per_chat=True,
    allow_reentry=True,
)