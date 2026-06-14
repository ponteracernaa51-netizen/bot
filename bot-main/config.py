import os
from dotenv import load_dotenv

load_dotenv()


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# ─── Telegram ────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ─── Supabase ────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ─── AI providers (для объяснения ошибок) ────────────────────
GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
AI_TIMEOUT      = _float_env("AI_TIMEOUT", 8.0)          # секунд

# ─── Validation weights ───────────────────────────────────────
SEMANTIC_MODEL      = os.getenv("SEMANTIC_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
SEMANTIC_CACHE_SIZE = _int_env("SEMANTIC_CACHE_SIZE", 512)
GRAMMAR_WEIGHT      = _float_env("GRAMMAR_WEIGHT",  0.50)
SEMANTIC_WEIGHT     = _float_env("SEMANTIC_WEIGHT", 0.50)

# ─── Phrase storage ───────────────────────────────────────────
PHRASE_SIMILARITY_THRESHOLD = _float_env("PHRASE_SIMILARITY_THRESHOLD", 75.0)

# ─── Anti-spam ────────────────────────────────────────────────
ANTISPAM_WINDOW_SECONDS = _float_env("ANTISPAM_WINDOW_SECONDS", 2.0)
ANTISPAM_MAX_EVENTS     = _int_env("ANTISPAM_MAX_EVENTS", 4)

# ─── Fallback levels (используется если БД недоступна) ───────
LEVELS_FALLBACK: dict[str, str] = {
    "A2": "Elementary — simple everyday phrases",
    "B1": "Intermediate — conversational English",
    "B2": "Upper-Intermediate — complex sentences",
    "C1": "Advanced — near-native fluency",
}
