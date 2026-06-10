"""
AI News Radar - Filters
1. Keyword filter  : keeps only AI-related items from general sources.
2. Junk filter     : removes spam/off-topic items from ALL sources.
3. Duplicate check : detects the same story covered by multiple sites.
"""

import re
from difflib import SequenceMatcher

import config

# Build word-boundary regexes once, so "ai" matches "AI wins" but not "rain".
_AI_PATTERNS = [re.compile(r"\b" + re.escape(k) + r"\b", re.IGNORECASE)
                for k in config.AI_KEYWORDS]
_JUNK_PATTERNS = [re.compile(r"\b" + re.escape(k) + r"\b", re.IGNORECASE)
                  for k in config.JUNK_KEYWORDS]


def is_ai_related(title):
    return any(p.search(title) for p in _AI_PATTERNS)


def is_junk(title):
    return any(p.search(title) for p in _JUNK_PATTERNS)


def _normalize(title):
    """Lowercase, remove punctuation and the ' - Source Name' tail that
    Google News adds, so titles compare fairly."""
    title = title.lower()
    title = re.sub(r"\s+-\s+[^-]+$", "", title)   # drop trailing "- CNN" etc.
    title = re.sub(r"[^a-z0-9 ]+", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def find_duplicate(title, existing_items):
    """Return the id of an existing item that is the SAME story, or None.
    existing_items = rows with .id and .title from the last 48 hours."""
    norm = _normalize(title)
    if not norm:
        return None
    for row in existing_items:
        other = _normalize(row["title"])
        if not other:
            continue
        if SequenceMatcher(None, norm, other).ratio() >= config.DUPLICATE_SIMILARITY:
            return row["id"]
    return None
