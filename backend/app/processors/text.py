import ftfy
from langdetect import detect, LangDetectException


def clean_text(raw: str) -> str:
    """
    Fixes encoding issues, normalizes whitespace.
    ftfy handles mojibake and other common text corruption.
    """
    if not raw:
        return ""
    fixed = ftfy.fix_text(raw)
    normalized = " ".join(fixed.split())
    return normalized.strip()


def detect_language(text: str) -> str:
    """Returns ISO language code — 'en', 'bn', 'hi' etc."""
    try:
        if len(text.strip()) < 10:
            return "unknown"
        return detect(text)
    except LangDetectException:
        return "unknown"


def normalize_text(raw: str, source_type: str = "text") -> dict:
    """
    Master normalization function called by all three input paths.
    Returns a dict with cleaned text and metadata.
    """
    cleaned = clean_text(raw)
    language = detect_language(cleaned)
    return {
        "text": cleaned,
        "language": language,
        "source_type": source_type,
        "char_count": len(cleaned),
    }