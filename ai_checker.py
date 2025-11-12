import logging
import json
from typing import Optional
import config
import google.generativeai as genai

logger = logging.getLogger(__name__)

model: Optional[genai.GenerativeModel] = None
try:
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY не найден в переменных окружения.")
    
    genai.configure(api_key=config.GEMINI_API_KEY)
    
    model = genai.GenerativeModel('gemini-pro-latest')
    logger.info(f"Модель Gemini '{model.model_name}' успешно инициализирована.")

except (ValueError, Exception) as e:
    logger.error(f"Ошибка при инициализации Gemini: {e}")
    model = None

async def check_translation(
    original_phrase: str, 
    user_translation: str,
    source_lang: str, 
    target_lang: str, 
    ui_lang: str
) -> str:
    if not model:
        return json.dumps({"error": "Сервис AI-проверки временно недоступен."})

    lang_map = {'ru': 'Russian', 'uz': 'Uzbek', 'en': 'English'}

    prompt_text = f"""
    You are an expert language teacher. Evaluate a translation.

    Original phrase ({lang_map.get(source_lang)}): "{original_phrase}"
    User's translation to {lang_map.get(target_lang)}: "{user_translation}"

    Analyze the translation and respond ONLY with a valid JSON object. 
    The JSON must have these keys:
    - "score": an integer from 0 to 10.
    - "corrected_translation": a string with the ideal translation.
    - "explanation": a brief, one-sentence explanation in {lang_map.get(ui_lang, 'English')}.
    
    Example of your output:
    {{
      "score": 8,
      "corrected_translation": "This is a correct sentence.",
      "explanation": "You used the wrong article, but the rest was perfect."
    }}
    """
    
    try:
        response = await model.generate_content_async(prompt_text)
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
        
        # Просто проверяем, что это валидный JSON, и возвращаем его как строку
        json.loads(cleaned_response) 
        
        logger.info("Проверка через Gemini API успешно завершена.")
        return cleaned_response

    except json.JSONDecodeError:
        logger.error(f"Gemini вернул невалидный JSON: {response.text}")
        return json.dumps({"error": "Не удалось обработать ответ от AI."})
    except Exception as e:
        logger.error(f"Ошибка при вызове Gemini API: {e}", exc_info=True)
        return json.dumps({"error": "Произошла ошибка при проверке перевода."})