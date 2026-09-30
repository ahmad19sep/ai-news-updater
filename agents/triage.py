"""Triage agent: scores every new story 1-10 for THIS audience, tags a topic
and urgency, and drops duplicates.

Two engines, same output (candidates in the store):
  * rules  — free, no model: the radar's audience_score + keyword rules
             (config.PIPELINE_MODE == "free"; also the hourly cloud job)
  * llm    — a cheap model reads the headlines in batches and explains why
             (config.PIPELINE_MODE == "api")
"""

import difflib
import re
from datetime import datetime, timezone

import config
import scoring
from agents import content
from agents.store import now_iso

SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "score": {"type": "integer", "minimum": 1, "maximum": 10},
                    "topic": {"type": "string", "enum": config.PIPELINE_TOPICS},
                    "urgency": {"type": "string", "enum": ["today", "this_week", "evergreen"]},
                    "reason": {"type": "string"},
                    "angle_hint": {"type": "string"},
                },
                "required": ["id", "score", "topic", "urgency", "reason", "angle_hint"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}

SYSTEM = """You are the triage editor for a LinkedIn creator who posts about AI.
You see a batch of freshly collected headlines (title, source, feed summary,
engagement). Your only job: decide which are worth the creator's attention.

Score 1-10 for THIS audience (described below):
 9-10  a real development most of this audience should know about today; strong post material
 7-8   clearly useful: a new capability, a decision it forces, a practical lesson, a good example of AI applied to a real problem
 5-6   fine but ordinary: incremental update, opinion piece, vendor marketing with one real fact
 1-4   noise: listicles, clickbait, stock-price chatter, rumours, duplicates of a bigger story, pure hype, off-topic

Rules:
- Judge the substance, not the source's fame. A small lab's shipped feature can beat a big lab's rumour.
- A story about AI applied to a real field (health, education, government, farming, industry, science) gets +1 if it reports an actual outcome, not a plan.
- Research papers score well only when a working professional could act on the finding.
- Two stories about the same event: give the more primary/complete one the score, the other 3 with reason "duplicate of <id>".
- topic: one of the allowed values. urgency: 'today' only when being late makes the post worthless.
- angle_hint: one line, the most interesting professional implication you can see from the headline alone. Do not invent facts; say "unclear from headline" if so.
- reason: one short line, plain English.
Return every id you were given, exactly once."""

# ---- rules engine -----------------------------------------------------
TOPIC_OF_CATEGORY = {
    "New Tools & Models": "tools", "AI in Coding": "coding", "Leaders & Podcasts": "society",
    "AI & the Future": "society", "AI in Defense": "politics_policy", "AI in Space": "science",
    "AI in Agriculture": "science", "AI in Health & Science": "health", "Research Papers": "science",
    "AI General News": "other",
}
TOPIC_KEYWORDS = [
    ("agents", r"\bagent(s|ic)?\b|\bmcp\b|\bcopilot\b"),
    ("models", r"\b(model|models|gpt-?\d|claude|gemini|llama|mistral|deepseek|qwen|sonnet|opus|o[1-9]\b|open-?weight)\b"),
    ("health", r"\b(health|hospital|clinic|patient|doctor|medical|drug|cancer|diagnos)"),
    ("politics_policy", r"\b(regulat|law|policy|government|senate|congress|eu\b|act\b|ban\b|election|white house|trump|minist)"),
    ("security", r"\b(security|hack|breach|malware|phishing|deepfake|scam|fraud)"),
    ("education", r"\b(school|student|teacher|university|education|learning platform)"),
    ("coding", r"\b(code|coding|developer|github|programm|ide\b|cursor)"),
    ("business", r"\b(revenue|funding|valuation|ipo|acqui|layoff|hiring|enterprise|startup|customer)"),
    ("science", r"\b(research|study|paper|scientist|physics|biology|protein|climate|space|nasa)"),
    ("tools", r"\b(app|tool|feature|update|launch|release|plugin|extension)"),
]
OFFICIAL = re.compile(r"\b(openai|google|deepmind|anthropic|microsoft|meta|nvidia|apple|amazon|hugging face|mistral|xai)\b", re.I)


def rules_score(story, hot_terms):
    """(score 1-10, topic, urgency, reason) from the radar's own rules."""
    title = story.get("title", "")
    try:
        age_h = (datetime.now(timezone.utc) - datetime.fromisoformat(story.get("published") or story.get("fetched"))).total_seconds() / 3600
    except (TypeError, ValueError):
        age_h = 999
    pillar = next((k for k, v in config.CATEGORIES.items() if v == story.get("category")), 10)
    raw, reasons, _local = scoring.audience_score(title, pillar, len(story.get("links") or []), age_h, hot_terms)
    if story.get("source") in config.INSTANT_SOURCES:
        raw += 3
        reasons.append("official announcement")
    elif OFFICIAL.search(title):
        raw += 1
    if len(story.get("summary") or "") > 150:
        raw += 1
    if (story.get("upvotes") or 0) >= 50:
        raw += 1
        reasons.append("community traction")
    if pillar == 9:
        raw -= 2
    if pillar == 3:
        raw -= 1
    # calibrated so that only a handful of stories a day reach 'new' (>= 6):
    # fresh + consumer-useful + multiple sources or an official source
    score = max(1, min(10, round(2 + raw * 0.55)))
    text = (title + " " + (story.get("summary") or "")).lower()
    topic = next((t for t, pat in TOPIC_KEYWORDS if re.search(pat, text)), None) or TOPIC_OF_CATEGORY.get(story.get("category"), "other")
    urgency = "today" if (age_h <= 24 and "official announcement" in reasons) else "this_week" if age_h <= 48 else "evergreen"
    return score, topic, urgency, (", ".join(reasons) or "matched audience rules")


# ---- shared -----------------------------------------------------------
def _norm(t):
    return re.sub(r"[^a-z0-9 ]+", " ", (t or "").lower()).split()


_STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "by", "is", "its", "it", "as",
         "at", "from", "new", "ai", "says", "how", "why", "what", "this", "that", "will", "can", "you", "your"}


def _dupe_of(title, others, threshold=0.82):
    """Same story twice: near-identical title, or the same content words
    (Jaccard >= 0.5 after stopwords) — catches 'OpenAI unveils X' vs 'OpenAI introduces X'."""
    words = _norm(title)
    a = " ".join(words)
    wa = {w for w in words if w not in _STOP and len(w) > 1}
    for o in others:
        ow = _norm(o.get("title"))
        b = " ".join(ow)
        if a and b and difflib.SequenceMatcher(None, a, b).ratio() >= threshold:
            return o.get("id")
        wb = {w for w in ow if w not in _STOP and len(w) > 1}
        if len(wa) >= 4 and len(wb) >= 4 and len(wa & wb) / len(wa | wb) >= 0.5:
            return o.get("id")
    return None


def _save(store, s, score, topic, urgency, reason, hint, existing, engine):
    dupe = _dupe_of(s["title"], existing)
    status = "new" if score >= config.PIPELINE_TRIAGE_MIN_SCORE else "low"
    if dupe:
        status = "duplicate"
    prev = store.get("candidates", s["id"]) or {}
    store.put("candidates", s["id"], {
        "title": s["title"], "url": s["url"], "source": s["source"],
        "category": s["category"], "published": s["published"], "fetched": s["fetched"],
        "summary": s.get("summary", ""), "links": list(s.get("links") or []), "score": score, "topic": topic, "urgency": urgency,
        "reason": reason, "angle_hint": hint, "status": status, "duplicate_of": dupe,
        "engine": engine, "created": prev.get("created") or now_iso(),
    })
    existing.append({"id": s["id"], "title": s["title"]})
    return status


def _batch_text(stories):
    lines = []
    for s in stories:
        eng = ""
        if s.get("upvotes") or s.get("comments"):
            eng = f" | engagement: {s.get('upvotes', 0)} up, {s.get('comments', 0)} comments"
        lines.append(f"[{s['id']}] {s['title']}\n  source: {s['source']} | category: {s['category']}"
                     f" | published: {(s.get('published') or '')[:10]}{eng}"
                     + (f"\n  summary: {s['summary']}" if s.get("summary") else ""))
    return "\n".join(lines)


def run_rules(store, stories, hot_terms=None, log=print):
    """Free triage. Returns the same counts as run()."""
    existing = list(store.all("candidates").values())
    kept = dismissed = dupes = 0
    for s in stories:
        score, topic, urgency, reason = rules_score(s, hot_terms or [])
        if score < config.PIPELINE_TRIAGE_KEEP_SCORE:
            dismissed += 1
            continue
        if _save(store, s, score, topic, urgency, reason, "", existing, "rules") == "duplicate":
            dupes += 1
        kept += 1
    return {"scored": len(stories), "kept": kept, "dismissed": dismissed, "duplicates": dupes,
            "ids": [s["id"] for s in stories]}


def run(llm, store, stories, log=print):
    """LLM triage. Returns counts + the ids that were scored."""
    voice = content.voice()
    system = SYSTEM + "\n\nAUDIENCE:\n" + voice["audience"] + "\n\nTOPIC PRIORITIES:\n" + voice["priorities"]
    existing = list(store.all("candidates").values())
    kept = dismissed = dupes = 0
    scored_ids = []
    for start in range(0, len(stories), config.PIPELINE_TRIAGE_BATCH):
        batch = stories[start:start + config.PIPELINE_TRIAGE_BATCH]
        by_id = {s["id"]: s for s in batch}
        try:
            result = llm.json("triage", system, "STORIES:\n" + _batch_text(batch), SCHEMA, max_tokens=6000)
        except Exception as e:                      # one bad batch must not kill the run
            log(f"  [!] triage batch failed: {e}")
            continue
        for item in result.get("items", []):
            s = by_id.get(item.get("id"))
            if not s:
                continue
            scored_ids.append(s["id"])
            score = int(item.get("score", 0))
            if score < config.PIPELINE_TRIAGE_KEEP_SCORE:
                dismissed += 1
                continue
            status = _save(store, s, score, item.get("topic", "other"), item.get("urgency", "this_week"),
                           item.get("reason", ""), item.get("angle_hint", ""), existing, "llm")
            dupes += int(status == "duplicate")
            kept += 1
    return {"scored": len(scored_ids), "kept": kept, "dismissed": dismissed,
            "duplicates": dupes, "ids": scored_ids}
