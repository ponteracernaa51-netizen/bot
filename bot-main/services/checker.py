"""
Deterministic translation validation.

The final score is based on semantic similarity only. Grammar is still
analyzed for detailed error feedback, but it does not affect the score.
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from html import escape
from math import sqrt

import httpx

from config import (
    AI_TIMEOUT,
    GROQ_API_KEY,
    SEMANTIC_CACHE_SIZE,
    SEMANTIC_MODEL,
    TOGETHER_API_KEY,
)

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"[a-z]+(?:'[a-z]+)?", re.IGNORECASE)
_ARTICLE_RE = re.compile(r"\b(a|an|the)\b", re.IGNORECASE)
_PREPOSITION_RE = re.compile(r"\b(at|in|on|by|to|from|for|with|of|as|about|during|before|after|around|between|into|through|under|over|above|below)\b", re.IGNORECASE)
_VERB_FORM_RE = re.compile(r"\b(am|is|are|was|were|be|being|been|have|has|had|do|does|did|will|would|can|could|may|might|must|should)\b", re.IGNORECASE)
_CONTRACTIONS = {
    "i'm": "i am",
    "you're": "you are",
    "he's": "he is",
    "she's": "she is",
    "it's": "it is",
    "we're": "we are",
    "they're": "they are",
    "can't": "cannot",
    "won't": "will not",
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "i'll": "i will",
    "you'll": "you will",
    "we'll": "we will",
    "they'll": "they will",
}

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_TOGETHER_URL = "https://api.together.xyz/v1/chat/completions"

_GROQ_MODEL = "llama-3.1-8b-instant"
_TOGETHER_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"


@dataclass(frozen=True)
class ValidationScores:
    grammar: float
    semantic: float

    @property
    def total(self) -> int:
        return max(1, min(100, round(self.semantic)))


def _apply_semantic_gate(score: int, semantic: float) -> int:
    if semantic < 30:
        return min(score, 50)
    if semantic < 55:
        return min(score, 65)
    return score


def _normalize(text: str) -> str:
    value = text.strip().lower()
    for old, new in _CONTRACTIONS.items():
        value = re.sub(rf"\b{re.escape(old)}\b", new, value)
    value = re.sub(r"[^a-z0-9'\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _tokens(text: str) -> list[str]:
    return _WORD_RE.findall(_normalize(text))


def _best_reference(user_answer: str, references: list[str]) -> str:
    normalized_answer = _normalize(user_answer)
    return max(
        references,
        key=lambda item: _lexical_similarity(normalized_answer, _normalize(item)),
    )


def _lexical_similarity(left: str, right: str) -> float:
    try:
        from rapidfuzz import fuzz

        return float(fuzz.token_set_ratio(left, right))
    except Exception:
        left_tokens = set(_tokens(left))
        right_tokens = set(_tokens(right))
        if not left_tokens and not right_tokens:
            return 100.0
        if not left_tokens or not right_tokens:
            return 0.0
        return 100.0 * len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


@lru_cache(maxsize=SEMANTIC_CACHE_SIZE)
def _cached_sentence_embedding(text: str) -> tuple[float, ...] | None:
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        return None

    model = _get_sentence_model()
    if model is None:
        return None
    vector = model.encode(text, normalize_embeddings=True)
    return tuple(float(x) for x in vector)


@lru_cache(maxsize=1)
def _get_sentence_model():
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(SEMANTIC_MODEL)
    except Exception as e:
        logger.warning("semantic_model_unavailable: %s", e)
        return None


def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def _semantic_score(user_answer: str, references: list[str]) -> float:
    lexical = max(_lexical_similarity(user_answer, ref) for ref in references)
    user_embedding = _cached_sentence_embedding(_normalize(user_answer))
    reference_embeddings = [
        embedding
        for ref in references
        if (embedding := _cached_sentence_embedding(_normalize(ref))) is not None
    ]
    if user_embedding is None or not reference_embeddings:
        return lexical

    semantic = max(_cosine(user_embedding, ref) for ref in reference_embeddings)
    semantic_score = max(0.0, min(100.0, semantic * 100.0))
    return max(lexical, semantic_score)


@lru_cache(maxsize=1)
def _get_language_tool():
    import shutil
    if not shutil.which("java"):
        logger.warning("LanguageTool disabled: Java runtime (java) is not installed or not in PATH.")
        return None

    try:
        import language_tool_python

        return language_tool_python.LanguageTool("en-US")
    except Exception as e:
        logger.warning("language_tool_unavailable: %s", e)
        return None


def _grammar_score(user_answer: str, reference: str, level: str) -> tuple[float, list[str]]:
    tool = _get_language_tool()
    words = max(1, len(_tokens(user_answer)))
    issues: list[str] = []

    if tool is None:
        score = _heuristic_grammar_score(user_answer, reference, issues)
    else:
        matches = tool.check(user_answer)
        # Exclude misspelling and typographical errors entirely as spelling is removed
        relevant = [
            item
            for item in matches
            if item.ruleIssueType in {"grammar", "style"}
        ]
        penalty_per_issue = 12 if level in {"A1", "A2"} else 16
        score = 100.0 - min(70.0, (len(relevant) / words) * 100.0 + len(relevant) * penalty_per_issue)
        issues.extend(item.message for item in relevant[:4])

    score = _apply_tense_article_penalties(score, user_answer, reference, issues)
    score = _apply_verb_form_penalties(score, user_answer, reference, issues)
    score = _apply_preposition_penalties(score, user_answer, reference, issues)
    score = _apply_tense_and_capitalization_penalties(score, user_answer, reference, issues)
    return max(1.0, score), issues


def _heuristic_grammar_score(user_answer: str, reference: str, issues: list[str]) -> float:
    score = 100.0
    answer = user_answer.strip()
    if answer and answer[0].islower():
        score -= 5
        issues.append("Start the sentence with a capital letter.")
    if len(_tokens(answer)) >= 5 and not re.search(r"[.!?]$", answer):
        score -= 5
        issues.append("Add sentence punctuation.")
    if abs(len(_tokens(answer)) - len(_tokens(reference))) >= 5:
        score -= 8
        issues.append("The answer length is far from the reference translation.")
    return score


def _apply_tense_article_penalties(
    score: float,
    user_answer: str,
    reference: str,
    issues: list[str],
) -> float:
    answer_norm = _normalize(user_answer)
    reference_norm = _normalize(reference)

    answer_articles = _ARTICLE_RE.findall(answer_norm)
    reference_articles = _ARTICLE_RE.findall(reference_norm)
    if reference_articles and not answer_articles:
        score -= 6
        issues.append("Check missing articles such as a, an, or the.")

    tense_markers = ("will", "was", "were", "did", "have", "has", "had")
    missing_tense = [
        marker
        for marker in tense_markers
        if re.search(rf"\b{marker}\b", reference_norm)
        and not re.search(rf"\b{marker}\b", answer_norm)
    ]
    if missing_tense:
        score -= min(12, len(missing_tense) * 6)
        issues.append("Check verb tense and auxiliary verbs.")

    return score


def _apply_verb_form_penalties(
    score: float,
    user_answer: str,
    reference: str,
    issues: list[str],
) -> float:
    """Check for incorrect verb forms and double auxiliary verbs (e.g., 'I'm usually work')."""
    answer_norm = _normalize(user_answer)
    answer_lower = user_answer.lower()

    # Check for patterns like "I'm work", "he's go", "we're make" (auxiliary + bare verb)
    auxiliary_patterns = [
        r"\b(i'm|you're|he's|she's|it's|we're|they're)\s+(work|go|make|see|come|take|get|give|find|tell|ask|know|think|feel|try|stop|seem|appear|become|start|continue|begin|help|want|need|like|love|hate|prefer)",
        r"\bam\s+(work|go|make|see|come|take|get|give|find|tell|ask|know|think|feel|try|stop|seem|appear|become|start|continue|begin|help|want|need|like|love|hate|prefer)",
        r"\b(is|are|was|were)\s+(work|go|make|see|come|take|get|give|find|tell|ask|know|think|feel|try|stop|seem|appear|become|start|continue|begin|help|want|need|like|love|hate|prefer)\b(?!\s*ing)",
    ]

    for pattern in auxiliary_patterns:
        if re.search(pattern, answer_lower):
            score -= 8
            if "Check verb forms" not in "".join(issues):
                issues.append("Check verb forms - avoid double auxiliaries (e.g., 'I'm work' should be 'I work').")
            break

    return score


def _apply_preposition_penalties(
    score: float,
    user_answer: str,
    reference: str,
    issues: list[str],
) -> float:
    """Check for incorrect prepositions and missing prepositions."""
    answer_norm = _normalize(user_answer)
    reference_norm = _normalize(reference)

    # Common preposition corrections
    preposition_fixes = {
        "in weekend": "at weekend",
        "in the weekend": "at the weekend",
        "on the weekends": "at weekends",
        "in weekends": "at weekends",
        "work in weekends": "work at weekends",
        "work in the weekend": "work at the weekend",
        "on afternoon": "in the afternoon",
        "in morning": "in the morning",
        "in night": "at night",
    }

    for wrong, correct in preposition_fixes.items():
        if wrong in answer_norm and correct not in answer_norm:
            score -= 7
            if "Check prepositions" not in "".join(issues):
                issues.append(f"Check prepositions - use '{correct}' instead of '{wrong}'.")
            break

    return score


def _apply_tense_and_capitalization_penalties(
    score: float,
    user_answer: str,
    reference: str,
    issues: list[str],
) -> float:
    """Check for incorrect verb tense (Present Continuous vs Simple Present) and capitalization errors."""
    answer_lower = user_answer.lower()
    
    # Check for Present Continuous when Simple Present should be used
    # Patterns like "are living", "is working", "are going" in habitual/general statements
    present_continuous_patterns = [
        r"\b(are|is|am)\s+(living|working|going|staying|studying|playing|eating|drinking|using|driving|reading|writing)",
    ]
    
    # Check if reference uses simple present (live, work, go, stay, etc.)
    simple_present_verbs = r"\b(live|work|go|stay|study|play|eat|drink|use|drive|read|write)\b"
    
    if re.search(simple_present_verbs, reference.lower()):
        for pattern in present_continuous_patterns:
            if re.search(pattern, answer_lower):
                # Check if this is really wrong by seeing if reference doesn't use continuous
                if not re.search(r"\b(are|is|am)\s+\w+ing\b", reference.lower()):
                    score -= 8
                    if "Check verb tense" not in "".join(issues):
                        issues.append("Check verb tense - use simple present ('live') instead of continuous ('are living').")
                    break
    
    # Check for capitalization errors (proper nouns like city names should be capitalized)
    # Extract words that should be capitalized
    words_in_answer = user_answer.split()
    lowercased_proper_nouns = []
    
    for i, word in enumerate(words_in_answer):
        # Check if word is lowercased but should be capitalized
        # (e.g., city names, country names - words that are capitalized in reference)
        clean_word = re.sub(r'[^a-z]', '', word.lower())
        if clean_word:
            # Check if this word appears capitalized in reference
            reference_words = reference.split()
            for ref_word in reference_words:
                ref_clean = re.sub(r'[^a-z]', '', ref_word.lower())
                if clean_word == ref_clean and ref_word[0].isupper() and word[0].islower():
                    # This word should be capitalized
                    if word not in ['is', 'are', 'am', 'in', 'at', 'on', 'the', 'a', 'an', 'and', 'or']:
                        lowercased_proper_nouns.append(word)
    
    if lowercased_proper_nouns:
        score -= 5
        noun_list = ", ".join(lowercased_proper_nouns[:2])
        if "Check capitalization" not in "".join(issues):
            issues.append(f"Check capitalization - capitalize proper nouns like '{noun_list}'.")
    
    return score


def preload_models():
    """Pre-load and cache semantic model and language tool helper."""
    logger.info("Pre-loading semantic model (sentence-transformers)...")
    try:
        _get_sentence_model()
    except Exception as e:
        logger.warning("Failed pre-loading semantic model: %s", e)

    logger.info("Pre-loading language tool...")
    try:
        _get_language_tool()
    except Exception as e:
        logger.warning("Failed pre-loading language tool: %s", e)


async def check_translation(
    original_ru: str,
    original_uz: str,
    reference_english: str,
    user_answer: str,
    level: str,
    alternative_answers: list[str] | None = None,
    phrase_lang: str = "ru",
) -> dict:
    references = [reference_english, *(alternative_answers or [])]
    references = list(dict.fromkeys(item.strip() for item in references if item and item.strip()))
    if not references:
        raise ValueError("At least one reference answer is required")

    # Run deterministic checker - no AI involvement in scoring
    res = await asyncio.to_thread(
        _check_translation_sync,
        references,
        user_answer,
        level,
    )

    return res


def _check_translation_sync(references: list[str], user_answer: str, level: str) -> dict:
    best_reference = _best_reference(user_answer, references)
    semantic = _semantic_score(user_answer, references)
    grammar, grammar_issues = _grammar_score(user_answer, best_reference, level)

    scores = ValidationScores(grammar=grammar, semantic=semantic)
    errors: list[str] = []
    if semantic < 70:
        errors.append("Meaning is different from the expected translation.")
    errors.extend(grammar_issues)

    total = _apply_semantic_gate(scores.total, semantic)

    return {
        "score": total,
        "errors": errors[:6],
        "feedback": _build_feedback(scores, errors),
        "is_correct": total >= 70,
        "details": {
            "syntax": round(grammar, 1),
            "semantic": round(semantic, 1),
            "matched_reference": best_reference,
        },
    }


def _build_feedback(scores: ValidationScores, errors: list[str]) -> str:
    if scores.total >= 90:
        return "Excellent translation. The meaning and English form are both strong."
    if scores.total >= 70:
        return "Good translation. Review the notes below to make it more natural."
    if errors:
        return "The answer needs work. Focus first on matching the meaning."
    return "Keep practicing. Try to stay closer to the reference translation."


def format_result_message(
    original_ru: str,
    original_uz: str,
    reference: str,
    user_answer: str,
    result: dict,
    lang: str = "ru",
    ai_explanation: str | None = None,
) -> str:
    score = result["score"]
    details = result.get("details", {})

    if score >= 90:
        verdict = "Perfect! 🌟"
        emoji = "🟢"
    elif score >= 70:
        verdict = "Good Job! ✨"
        emoji = "🟡"
    elif score >= 50:
        verdict = "Almost there! 💪"
        emoji = "🟠"
    else:
        verdict = "Keep trying! 📚"
        emoji = "🔴"

    original_label = "Uzbek" if lang == "uz" else "Russian"
    original_text  = original_uz if lang == "uz" else original_ru

    lines = [
        f"{emoji} <b>{verdict} — {score}/100</b>",
        "━━━━━━━━━━━━━━━━━━━━",
        f"<b>💬 {original_label}:</b> {escape(original_text)}",
        f"<b>✍️ Your answer:</b> <i>{escape(user_answer)}</i>",
        f"<b>✅ Correct:</b> <i>{escape(reference)}</i>",
        "━━━━━━━━━━━━━━━━━━━━",
        "📊 <b>Score Details:</b>",
        f"• <b>Meaning:</b> {round(details.get('semantic', 0))}/100",
    ]

    if result.get("errors"):
        lines.append("")
        lines.append("⚠️ <b>What to improve:</b>")
        for err in result["errors"][:5]:
            lines.append(f"• {escape(str(err))}")

    if result.get("feedback"):
        lines.append("")
        lines.append(f"💡 <i>{escape(result['feedback'])}</i>")

    if ai_explanation:
        lines.append("")
        lines.append("🤖 <b>AI Explanation:</b>")
        lines.append(f"<i>{escape(ai_explanation)}</i>")

    return "\n".join(lines)
