"""Language detection service — wraps langdetect with Canadian French/English bias."""
from __future__ import annotations

import re

from app.core.logging import logger

_FR_MARKERS = frozenset({
    "le", "la", "les", "de", "du", "des", "et", "est", "au", "aux",
    "pour", "dans", "avec", "sur", "par", "qui", "que", "nous", "vous",
    "ils", "elles", "une", "un", "pas", "ne", "se", "ce", "cet", "cette",
})

_EN_MARKERS = frozenset({
    "the", "and", "is", "are", "for", "with", "this", "that", "have",
    "from", "not", "but", "our", "your", "their", "we", "you", "they",
    "it", "as", "at", "by", "an", "be",
})


def detect_language(text: str | None) -> str:
    """Return 'fr' or 'en'. Defaults to 'fr' for Quebec market."""
    if not text or len(text.strip()) < 10:
        return "fr"

    # Try langdetect first
    try:
        from langdetect import detect, LangDetectException  # type: ignore
        lang = detect(text)
        if lang in ("fr", "en"):
            return lang
        # langdetect returns variants like fr-ca — normalize
        if lang.startswith("fr"):
            return "fr"
        if lang.startswith("en"):
            return "en"
    except Exception:
        pass

    # Heuristic fallback: count marker words
    words = set(re.findall(r"[a-zA-Zàâçéèêëîïôùûüœæ]+", text.lower()))
    fr_hits = len(words & _FR_MARKERS)
    en_hits = len(words & _EN_MARKERS)

    if fr_hits > en_hits:
        return "fr"
    if en_hits > fr_hits:
        return "en"
    return "fr"  # Quebec default


def normalize_detected(lang: str | None) -> str:
    """Normalize any ISO code to 'fr' or 'en'."""
    if not lang:
        return "fr"
    lang = lang.lower().strip()
    if lang.startswith("fr"):
        return "fr"
    if lang.startswith("en"):
        return "en"
    return "fr"
