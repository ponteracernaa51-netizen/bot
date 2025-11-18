# src/utils/keyboards.py

from typing import List
from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
)
from src.utils import texts
from src.db.models import Topic, Level

# get_main_menu_keyboard и get_after_answer_keyboard без изменений...

def get_main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    button_texts = texts.BUTTONS
    keyboard = [
        [KeyboardButton(button_texts['training'][lang])],
        [KeyboardButton(button_texts['profile'][lang]), KeyboardButton(button_texts['settings'][lang])],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_after_answer_keyboard(lang: str) -> InlineKeyboardMarkup:
    button_texts = texts.BUTTONS
    keyboard = [[
        InlineKeyboardButton(text=button_texts['next_phrase'][lang], callback_data="next_phrase"),
        InlineKeyboardButton(text=button_texts['change_topic'][lang], callback_data="change_topic"),
    ]]
    return InlineKeyboardMarkup(keyboard)

# --- Проверяем и исправляем все callback_data здесь ---

def get_profile_keyboard(lang: str) -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton(texts.BUTTONS['edit_profile'][lang], callback_data='profile:edit')]]
    return InlineKeyboardMarkup(keyboard)

def get_profile_edit_keyboard(lang: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(texts.BUTTONS['edit_topic'][lang], callback_data='profile:edit_topic')],
        [InlineKeyboardButton(texts.BUTTONS['edit_level'][lang], callback_data='profile:edit_level')],
        [InlineKeyboardButton(texts.BUTTONS['edit_direction'][lang], callback_data='profile:edit_direction')],
        [InlineKeyboardButton(texts.BUTTONS['back_to_profile'][lang], callback_data='profile:show')],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_directions_keyboard(lang: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский -> 🇬🇧 Английский", callback_data="profile:direction:ru-en"),
            InlineKeyboardButton("🇬🇧 Английский -> 🇷🇺 Русский", callback_data="profile:direction:en-ru"),
            InlineKeyboardButton("uz Узбекский -> 🇬🇧 Английский", callback_data="profile:direction:uz-en"),
            InlineKeyboardButton("🇬🇧 Английский -> uz Узбекский", callback_data="profile:direction:en-uz"),
        ],
        [InlineKeyboardButton(texts.BUTTONS['back_to_edit_profile'][lang], callback_data='profile:edit')],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_topics_keyboard(topics: List[Topic], lang: str) -> InlineKeyboardMarkup:
    keyboard = []
    for topic in topics:
        topic_name = getattr(topic, f'name_{lang}', topic.name_ru)
        button = InlineKeyboardButton(text=topic_name, callback_data=f"profile:topic:{topic.id}")
        keyboard.append([button])
    keyboard.append([InlineKeyboardButton(texts.BUTTONS['back_to_edit_profile'][lang], callback_data='profile:edit')])
    return InlineKeyboardMarkup(keyboard)

def get_levels_keyboard(levels: List[Level], lang: str) -> InlineKeyboardMarkup:
    keyboard = []
    for level in levels:
        level_name = getattr(level, f'name_{lang}', level.name_ru)
        button = InlineKeyboardButton(text=level_name, callback_data=f"profile:level:{level.id}")
        keyboard.append([button])
    keyboard.append([InlineKeyboardButton(texts.BUTTONS['back_to_edit_profile'][lang], callback_data='profile:edit')])
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard(
    lang: str, 
    is_notifications_enabled: bool, 
    is_repeating_errors: bool  # <-- 1. ПРИНИМАЕМ НОВЫЙ АРГУМЕНТ
) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для меню настроек с учетом состояния пользователя.
    """
    button_texts = texts.BUTTONS
    keyboard = []

    # 2. ИСПОЛЬЗУЕМ НОВЫЙ АРГУМЕНТ В ЛОГИКЕ
    # Кнопка меняется в зависимости от того, включен ли режим
    if is_repeating_errors:
        keyboard.append([InlineKeyboardButton(
            text=button_texts['repeat_errors_off'][lang], # Показываем кнопку "Выключить"
            callback_data="settings:repeat_errors_off"
        )])
    else:
        keyboard.append([InlineKeyboardButton(
            text=button_texts['repeat_errors'][lang], # Показываем кнопку "Включить"
            callback_data="settings:repeat_errors"
        )])
    
    # Остальные кнопки без изменений
    keyboard.append([InlineKeyboardButton(
        text=button_texts['edit_language'][lang], 
        callback_data="settings:edit_language"
    )])
    
    notification_text_key = 'notifications_on' if is_notifications_enabled else 'notifications_off'
    keyboard.append([InlineKeyboardButton(
        text=button_texts[notification_text_key][lang], 
        callback_data="settings:toggle_notifications"
    )])
    
    return InlineKeyboardMarkup(keyboard)


def get_language_keyboard(lang: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="settings:lang:ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="settings:lang:en"),
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="settings:lang:uz"),
        ],
        [InlineKeyboardButton(texts.BUTTONS['back_to_settings'][lang], callback_data="settings:back")],
    ]
    return InlineKeyboardMarkup(keyboard)