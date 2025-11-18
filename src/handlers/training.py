# src/handlers/training.py

import logging
import random
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.db import repository
from src.ai import gemini_client
from src.utils import keyboards, texts
from .profile import profile_start

logger = logging.getLogger(__name__)


async def start_training(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    telegram_id = update.effective_user.id
    user = await repository.get_user(telegram_id)
    lang = user.language_code or 'ru'

    if not all([user.topic_id, user.level_id, user.direction]):
        await message.reply_text("Пожалуйста, сначала настройте тему, уровень и направление в профиле.")
        return

    phrase = None

    if user.is_repeating_errors:
        phrases_to_repeat = await repository.get_phrases_for_repetition(
            user_id=user.id,
            topic_id=user.topic_id,
            level_id=user.level_id
        )
        if phrases_to_repeat:
            phrase = random.choice(phrases_to_repeat)
        else:
            await repository.update_user(telegram_id, is_repeating_errors=False)
            await message.reply_text(texts.MESSAGES['no_errors_to_repeat'][lang])
            return
    else:
        phrase = await repository.get_next_phrase(user.id, user.topic_id, user.level_id)

    if phrase is None:
        await message.reply_text(texts.MESSAGES['topic_finished'][lang])
        context.user_data.pop('current_phrase_id', None)
        context.user_data.pop('awaiting_translation', None)
        return

    context.user_data['current_phrase_id'] = phrase.id
    lang_from, _ = user.direction.split('-')
    original_text = getattr(phrase, f'text_{lang_from}')
    context.user_data['awaiting_translation'] = True
    await message.reply_text(f"Переведите фразу: *{original_text}*", parse_mode=ParseMode.MARKDOWN)


async def handle_translation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get('awaiting_translation'):
        return
    context.user_data.pop('awaiting_translation', None)
    
    phrase_id = context.user_data.get('current_phrase_id')
    if not phrase_id:
        return

    user_translation = update.message.text
    telegram_id = update.effective_user.id
    user = await repository.get_user(telegram_id)
    lang = user.language_code or 'ru'
    
    phrase = await repository.get_phrase_by_id(phrase_id)
    if not phrase:
        await update.message.reply_text(texts.MESSAGES['error_occurred'][lang])
        return

    lang_from, lang_to = user.direction.split('-')
    original_phrase = getattr(phrase, f'text_{lang_from}')
    correct_translation_example = getattr(phrase, f'text_{lang_to}')
    
    await update.message.reply_text("🧠 Анализирую ваш перевод...", quote=True)
    
    # ==================== ИСПРАВЛЕНИЕ ЗДЕСЬ ====================
    # Заменяем "..." на реальные аргументы функции
    ai_result = await gemini_client.evaluate_translation(
        original_phrase=original_phrase,
        user_translation=user_translation,
        correct_translation_example=correct_translation_example,
        user_lang=lang,
        direction=user.direction
    )
    # ==========================================================

    score = ai_result.get('score', 0)
    await repository.save_score(user.id, phrase_id, score)

    if not user.is_repeating_errors:
        await repository.update_user_topic_progress(user.id, user.topic_id, phrase_id)

    explanation = ai_result.get('explanation', 'Нет объяснения.')
    corrected_translation = ai_result.get('corrected_translation', correct_translation_example)
    
    response_text = (
        f"📝 **Результат проверки**\n\n⭐ **Ваша оценка:** {score}/100\n\n"
        f"💬 **Комментарий:** {explanation}\n\n✅ **Правильный вариант:** {corrected_translation}"
    )
    
    keyboard = keyboards.get_after_answer_keyboard(lang)
    await update.message.reply_text(response_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
    
    context.user_data.pop('current_phrase_id', None)


async def training_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data
    
    if action == "next_phrase":
        await query.message.delete()
        await start_training(update, context)
    elif action == "change_topic":
        await query.message.delete()
        await profile_start(update, context)