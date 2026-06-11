"""
AI News Radar - Story scoring + trend detection (no AI needed, pure logic)

1. compute_trends()  -> which model/tool/company names are RISING this week
                        vs last week (catches the next "Nano Banana" early)
2. score_items()     -> ranks recent stories by video-worthiness:
                        many sources + official lab + fresh + trending topic
"""

import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

import config

# Words that look like names but are noise - never count as trend terms.
STOPWORDS = {
    "the", "a", "an", "i", "why", "how", "what", "when", "who", "where",
    "new", "this", "that", "your", "you", "it", "is", "are", "will", "can",
    "could", "should", "here", "now", "after", "before", "with", "from",
    "and", "but", "not", "no", "yes", "show", "ask", "hn", "ai", "us", "uk",
    "mr", "dr", "if", "in", "on", "at", "to", "of", "for", "as", "by", "or",
    "be", "do", "we", "he", "she", "they", "its", "his", "her", "their",
    "our", "my", "me", "just", "more", "most", "best", "top", "big", "says",
    "say", "said", "get", "gets", "got", "make", "makes", "made", "use",
    "uses", "used", "using", "everyone", "people", "man", "woman", "year",
    "week", "day", "today", "tech", "news", "update", "report", "study",
}

# News outlets - they appear in every headline tail, they are not trends.
PUBLISHERS = {
    "yahoo finance", "business insider", "bloomberg", "times", "reuters",
    "cnbc", "forbes", "techcrunch", "the verge", "verge", "wired", "axios",
    "cnn", "bbc", "fortune", "futurism", "engadget", "ars technica",
    "the information", "wall street journal", "wsj", "new york times",
    "washington post", "guardian", "financial times", "insider", "zdnet",
    "venturebeat", "the register", "tom's hardware", "pcmag", "gizmodo",
    "india today", "ndtv", "hindustan times", "economic times", "livemint",
    "dawn", "geo news", "the decoder", "9to5google", "macrumors",
}

# Capitalized phrases of 1-3 words, e.g. "Nano Banana", "Gemini 3", "GPT-5.2"
_TERM_RE = re.compile(r"\b[A-Z][\w.+-]*(?:\s+(?:[A-Z][\w.+-]*|\d[\w.]*)){0,2}")


def _terms_from_title(title):
    """Extract candidate model/tool/company names from one headline."""
    # Google/Bing News add " - Publisher Name" at the end - cut it off.
    title = re.sub(r"\s+[-|]\s+[^-|]+$", "", title)
    found = {}
    for match in _TERM_RE.findall(title):
        words = match.split()
        # drop leading/trailing stopwords ("Why Gemini" -> "Gemini")
        while words and words[0].lower() in STOPWORDS:
            words = words[1:]
        while words and words[-1].lower() in STOPWORDS:
            words = words[:-1]
        if not words:
            continue
        term = " ".join(words)
        if len(term) < 3 or term.lower() in PUBLISHERS:
            continue
        found[term.lower()] = term  # key normalized, value = display form
    return found


def compute_trends(conn, min_count=4):
    """Compare term counts: last 7 days vs the 7 days before.
    Returns a list of dicts sorted by importance:
    {term, display, now, prev, status} - status: new / rising / steady / cooling
    """
    now = datetime.now(timezone.utc)
    cutoff_14 = (now - timedelta(days=14)).isoformat()
    cutoff_7 = (now - timedelta(days=7)).isoformat()

    rows = conn.execute(
        "SELECT title, fetched FROM items WHERE fetched >= ?", (cutoff_14,)
    ).fetchall()

    this_week, last_week = Counter(), Counter()
    display = {}
    for r in rows:
        terms = _terms_from_title(r["title"])
        display.update(terms)
        bucket = this_week if r["fetched"] >= cutoff_7 else last_week
        for key in terms:
            bucket[key] += 1

    trends = []
    for key, count in this_week.items():
        if count < min_count:
            continue
        prev = last_week.get(key, 0)
        if prev == 0:
            status = "new"
        elif count >= prev * 2:
            status = "rising"
        elif count <= prev * 0.5:
            status = "cooling"
        else:
            status = "steady"
        trends.append({"term": key, "display": display[key],
                       "now": count, "prev": prev, "status": status})

    order = {"new": 0, "rising": 1, "steady": 2, "cooling": 3}
    trends.sort(key=lambda t: (order[t["status"]], -t["now"]))
    return trends


def rising_terms(trends):
    """Just the new + rising term keys (used for story scoring)."""
    return [t["term"] for t in trends if t["status"] in ("new", "rising")]


# --- Audience relevance: "Should Ahmad film this today?" ---
# The audience (everyday people in Pakistan/India) cares about life, jobs,
# money, tools they can try - NOT benchmarks or papers.
_CONSUMER_P = [re.compile(r"\b" + re.escape(k) + r"\b", re.IGNORECASE)
               for k in config.CONSUMER_KEYWORDS]
_LOCAL_P = [re.compile(r"\b" + re.escape(k) + r"\b", re.IGNORECASE)
            for k in config.LOCAL_KEYWORDS]
_RESEARCHY_P = [re.compile(r"\b" + re.escape(k) + r"\b", re.IGNORECASE)
                for k in config.RESEARCHY_KEYWORDS]


def audience_score(title, pillar, n_extra_sources, age_h, hot_terms):
    """Returns (score, reasons, is_local). Higher = film it today."""
    score, reasons = 0, []
    local = any(p.search(title) for p in _LOCAL_P)
    if local:
        score += 4
        reasons.append("PK/IN local angle")
    if any(p.search(title) for p in _CONSUMER_P):
        score += 3
        reasons.append("useful for viewers")
    if any(p.search(title) for p in _RESEARCHY_P):
        score -= 4  # technical talk - audience does not care
    if n_extra_sources:
        score += 2 * n_extra_sources
        reasons.append(f"{n_extra_sources + 1} sources")
    if age_h <= 24:
        score += 3
        reasons.append("fresh today")
    elif age_h <= 48:
        score += 1
    title_low = title.lower()
    for term in hot_terms:
        if term in title_low:
            score += 2
            reasons.append(f"trending: {term}")
            break
    if pillar in (1, 2):  # tools & coding = things people can actually use
        score += 1
    return score, reasons, local


def score_items(conn, trends=None, hours=72):
    """Audience-scored recent stories (research papers excluded), sorted
    high-to-low. Used for the daily Top 5 phone picks."""
    if trends is None:
        trends = compute_trends(conn)
    hot_terms = rising_terms(trends)[:15]

    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=hours)).isoformat()
    rows = conn.execute(
        "SELECT id, title, url, links, source, pillar, published, fetched "
        "FROM items WHERE fetched >= ?", (cutoff,)
    ).fetchall()

    scored = []
    for r in rows:
        if r["pillar"] == 9:   # research papers are never video candidates
            continue
        extra = len(json.loads(r["links"] or "[]"))
        when = r["published"] or r["fetched"]
        try:
            age_h = (now - datetime.fromisoformat(when)).total_seconds() / 3600
        except ValueError:
            age_h = 999
        score, reasons, local = audience_score(
            r["title"], r["pillar"], extra, age_h, hot_terms)
        scored.append({
            "id": r["id"], "title": r["title"], "url": r["url"],
            "source": r["source"], "category": r["pillar"],
            "score": score, "reasons": reasons, "local": local,
        })

    scored.sort(key=lambda x: -x["score"])
    return scored
