from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.languages import get_text, get_topic_name, get_difficulty_name, get_direction_name
from config import TOPICS, DIFFICULTY_LEVELS

def get_language_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Русский 🇷🇺", callback_data='lang_ru')],
        [InlineKeyboardButton("O'zbek 🇺🇿", callback_data='lang_uz')],
        [InlineKeyboardButton("English 🇬🇧", callback_data='lang_en')],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_direction_keyboard(lang_code: str) -> InlineKeyboardMarkup:
    directions = ['ru_en', 'en_ru', 'uz_en', 'en_uz']
    keyboard = []
    row = []
    for key in directions:
        row.append(InlineKeyboardButton(
            get_direction_name(lang_code, key),
            callback_data=f'direction_{key}'
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(f"« {get_text(lang_code, 'back_to_topics')}", callback_data='back_to_topics')])
    return InlineKeyboardMarkup(keyboard)

def get_topics_keyboard(lang_code: str) -> InlineKeyboardMarkup:
    keyboard = []
    row = []
    for topic_key in TOPICS:
        row.append(InlineKeyboardButton(
            get_topic_name(lang_code, topic_key),
            callback_data=f'topic_{topic_key}'
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def get_difficulty_keyboard(lang_code: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                get_difficulty_name(lang_code, level),
                callback_data=f'difficulty_{level}'
            ) for level in DIFFICULTY_LEVELS
        ],
        [InlineKeyboardButton(f"« {get_text(lang_code, 'back_to_topics')}", callback_data='back_to_topics')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_next_action_keyboard(lang_code: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(get_text(lang_code, 'next_phrase'), callback_data='next_phrase'),
            InlineKeyboardButton(get_text(lang_code, 'change_topic'), callback_data='change_topic')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

