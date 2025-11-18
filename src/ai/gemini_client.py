# src/ai/gemini_client.py

import json
import logging

import google.generativeai as genai

# ==================== НАЧАЛО ИЗМЕНЕНИЙ ====================
# Импортируем объект `settings` из модуля `src.core.config`
from src.core.config import settings
# ===================== КОНЕЦ ИЗМЕНЕНИЙ =====================

# Настраиваем API ключ при загрузке модуля
# Теперь обращаемся к ключу через объект settings
try:
    if settings.gemini_api_key:
        genai.configure(api_key=settings.gemini_api_key)
    else:
        logging.warning("GEMINI_API_KEY is not set. AI features will be disabled.")
except Exception as e:
    logging.error(f"Error configuring Google Gemini API: {e}")


async def evaluate_translation(
    original_phrase: str,
    user_translation: str,
    correct_translation_example: str,
    user_lang: str,
    direction: str,
) -> dict:
    """
    Evaluates the user's translation using the Gemini API.
    """
    lang_from, lang_to = direction.split("-")

    # Формируем детальный промпт для Gemini
    prompt = f"""
Act as a language expert. Evaluate the user's translation based on the original phrase and a correct example.
Provide your response ONLY in a valid JSON format, without any markdown formatting like ```json ... ```.

The user's interface language is '{user_lang}'. Your explanation and all text fields must be in this language.

- Original phrase ({lang_from}): "{original_phrase}"
- User's translation ({lang_to}): "{user_translation}"
- Example of a correct translation ({lang_to}): "{correct_translation_example}"

Analyze the user's translation for grammar, vocabulary, and meaning.
Assign a score from 0 to 100, where 100 is a perfect translation.

The JSON output must have the following structure:
{{
  "score": <integer, 0-100>,
  "explanation": "<string, your detailed feedback in {user_lang}>",
  "corrected_translation": "<string, an ideal version of the translation>",
  "mistakes": [
    {{
      "type": "<string, e.g., 'Grammar', 'Vocabulary', 'Punctuation', 'Meaning'>",
      "description": "<string, a short description of the mistake in {user_lang}>"
    }}
  ]
}}

If the user's translation is perfect, the "mistakes" array should be empty.
"""

    # Создаем словарь-заглушку на случай ошибки
    error_response = {
        "score": 0,
        "explanation": "Произошла ошибка при анализе вашего ответа. Пожалуйста, попробуйте позже.",
        "corrected_translation": correct_translation_example,
        "mistakes": [],
    }

    if not settings.gemini_api_key:
        return error_response

    try:
        model = genai.GenerativeModel("gemini-flash-latest")
        response = await model.generate_content_async(prompt)
        
        # Убираем возможные markdown-обертки ```json ... ```
        cleaned_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()

        # Парсим JSON
        result = json.loads(cleaned_text)
        return result

    except json.JSONDecodeError as e:
        logging.error(f"Gemini response JSON parsing failed: {e}. Response text: {response.text}")
        return error_response
    except Exception as e:
        logging.error(f"An unexpected error occurred with Gemini API: {e}")
        return error_response