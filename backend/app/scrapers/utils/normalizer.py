"""Normalizers for phone numbers, URLs, and business names."""
from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlparse


def normalize_phone(raw: str | None) -> str | None:
    """Return a 10-digit Canadian phone number or None."""
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    # Strip country code +1
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return digits
    return None


def normalize_website(raw: str | None) -> str | None:
    """Return a cleaned https URL or None."""
    if not raw:
        return None
    raw = raw.strip()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    parsed = urlparse(raw)
    if not parsed.netloc:
        return None
    # Lowercase scheme+host, keep path
    return f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path}"


def website_domain(url: str | None) -> str | None:
    """Extract bare domain (no www) from a URL."""
    if not url:
        return None
    parsed = urlparse(url if "://" in url else "https://" + url)
    host = parsed.netloc.lower().lstrip("www.")
    return host or None


def normalize_name(raw: str) -> str:
    """Lowercase + remove accents + collapse whitespace for fuzzy matching."""
    nfd = unicodedata.normalize("NFD", raw)
    ascii_str = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", ascii_str.lower()).strip()


def detect_language(text: str | None) -> str:
    """Return 'fr' or 'en' heuristically."""
    if not text:
        return "fr"
    fr_markers = {"le", "la", "les", "de", "du", "des", "et", "est", "au", "aux", "pour"}
    words = set(re.findall(r"[a-zA-Zàâçéèêëîïôùûüœæ]+", text.lower()))
    if len(words & fr_markers) >= 2:
        return "fr"
    return "en"


def clean_text(raw: str | None) -> str | None:
    if not raw:
        return None
    return re.sub(r"\s+", " ", raw.strip()) or None
