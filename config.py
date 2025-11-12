import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')

TABLE_PHRASES = 'phrases'
TABLE_USER_STATS = 'user_stats'

SELECTING_LANG, SELECTING_TOPIC, SELECTING_DIFFICULTY, SELECTING_DIRECTION, AWAITING_TRANSLATION = range(5)

TOPICS = [
    # Present Tenses
    'present_simple',
    'present_continuous',
    'present_perfect',
    'present_perfect_continuous',

    # Past Tenses
    'past_simple',
    'past_continuous',
    'past_perfect',
    'past_perfect_continuous',

    # Future Tenses
    'future_simple',
    'future_continuous',
    'future_perfect',
    'future_perfect_continuous',

    # Grammar & Structure
    'passive_voice',
    'modal_verbs',
    'conditionals',
    'reported_speech',
    'questions_and_negatives',
    'verb_to_be',
    'irregular_verbs',
    'articles',
    'prepositions',
    'comparatives_and_superlatives',
    'phrasal_verbs',

    # Vocabulary / Everyday Topics
    'travel',
    'food',
    'daily_routine',
    'shopping',
    'weather',
    'hobbies',
    'work',
    'health',
    'education',
    'technology',
    'sports',
    'entertainment',
    'family',
    'environment'
]


DIFFICULTY_LEVELS = ['easy', 'medium', 'hard']