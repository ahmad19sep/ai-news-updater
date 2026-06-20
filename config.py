"""
AI News Radar - Configuration
All news sources, categories, and filter keywords.
Every source here is FREE (RSS feeds and public APIs).
"""

import os

# ---------------- Categories ----------------
# Every story is sorted into one of these by its TITLE (keyword rules
# below), no matter which source it came from.
CATEGORIES = {
    1: "New Tools & Models",
    2: "AI in Coding",
    3: "Leaders & Podcasts",
    4: "AI & the Future",
    5: "AI in Defense",
    6: "AI in Space",
    7: "AI in Agriculture",
    8: "AI in Health & Science",
    9: "Research Papers",
    10: "AI General News",
}

# Rules are checked top to bottom - the FIRST match wins, so put the
# most specific topics first. Words match on word boundaries.
# Tune these lists anytime; then run  python reclassify.py  to re-sort
# the whole archive with the new rules.
CATEGORY_RULES = [
    (2, [  # AI in Coding
        "coding", "code", "coder", "programmer", "programming", "developer",
        "copilot", "cursor", "github", "software engineer", "vibe coding",
        "ide", "debugging", "pull request", "claude code", "codex", "devin",
    ]),
    (6, [  # AI in Space
        "space", "nasa", "satellite", "satellites", "astronomy", "astronaut",
        "mars", "lunar", "moon", "rocket", "orbit", "telescope", "galaxy",
        "spacex", "cosmos", "exoplanet",
    ]),
    (7, [  # AI in Agriculture
        "farm", "farming", "farmer", "farmers", "agriculture", "agricultural",
        "crop", "crops", "harvest", "livestock", "soil", "irrigation",
        "pesticide", "agritech", "agtech", "greenhouse",
    ]),
    (5, [  # AI in Defense
        "military", "army", "defense", "defence", "pentagon", "weapon",
        "weapons", "warfare", "navy", "air force", "soldier", "soldiers",
        "battlefield", "missile", "missiles", "national security", "combat",
    ]),
    (8, [  # AI in Health & Science
        "health", "medical", "medicine", "cancer", "drug", "drugs", "protein",
        "biology", "hospital", "doctor", "doctors", "disease", "vaccine",
        "surgery", "climate", "physics", "chemistry", "dna", "brain",
        "mental health", "diagnosis", "patient", "patients", "biotech",
    ]),
    (3, [  # Leaders & Podcasts
        "altman", "amodei", "hassabis", "jensen huang", "nadella", "musk",
        "zuckerberg", "lecun", "sutskever", "pichai", "podcast", "interview",
        "keynote", "ceo",
    ]),
    (4, [  # AI & the Future
        "agi", "superintelligence", "future", "jobs", "job", "unemployment",
        "workforce", "workers", "singularity", "prediction", "predicts",
        "humanity", "existential", "by 2030", "by 2035", "takeover",
    ]),
    (1, [  # New Tools & Models
        "launch", "launches", "launched", "release", "releases", "released",
        "unveils", "unveil", "introduces", "announces", "new model", "update",
        "upgrade", "feature", "features", "tool", "tools", "app", "api",
        "model", "models", "version",
    ]),
    # No match -> the feed's own default category (often 10, General News)
]


def google_news(query):
    """Build a Google News RSS search URL for any query."""
    q = query.replace(" ", "+").replace('"', "%22")
    return f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"


def bing_news(query):
    """Bing News RSS for the same query - used as automatic backup,
    because Google News blocks cloud server IPs (GitHub Actions)."""
    q = query.replace(" ", "+").replace('"', "%22")
    return f"https://www.bing.com/news/search?q={q}&format=rss"


def news_search(name, query, category, lock=False, max_age_days=None):
    """A news-search feed: tries Google News first, falls back to Bing News.
    lock=True -> always file under this category, skip title rules.
    max_age_days -> accept older stories (slow topics like space/agriculture)."""
    feed = {"name": name, "url": google_news(query), "fallback": bing_news(query),
            "category": category, "trusted": False, "lock": lock}
    if max_age_days:
        feed["max_age_days"] = max_age_days
    return feed


# Each feed: name, url, default category, trusted
# trusted=True  -> official AI source, items pass WITHOUT the AI keyword filter
# trusted=False -> general source, items must contain AI keywords to pass
# lock=True     -> keep the feed's category, ignore title rules
FEEDS = [
    # ---------- Official labs (default: New Tools & Models) ----------
    {"name": "OpenAI Blog",        "url": "https://openai.com/news/rss.xml",                          "category": 1, "trusted": True},
    {"name": "Google DeepMind",    "url": "https://deepmind.google/blog/rss.xml",                     "category": 1, "trusted": True},
    {"name": "Hugging Face Blog",  "url": "https://huggingface.co/blog/feed.xml",                     "category": 1, "trusted": True},
    {"name": "Google AI Blog",     "url": "https://blog.google/innovation-and-ai/technology/ai/rss/",  "category": 1, "trusted": True},
    {"name": "NVIDIA AI Blog",     "url": "https://blogs.nvidia.com/blog/category/generative-ai/feed/", "category": 1, "trusted": True},
    {"name": "Google Research",    "url": "https://research.google/blog/rss/",                        "category": 1, "trusted": True},
    {"name": "AWS ML Blog",        "url": "https://aws.amazon.com/blogs/machine-learning/feed/",      "category": 1, "trusted": True},
    {"name": "Apple ML Research",  "url": "https://machinelearning.apple.com/rss.xml",                "category": 1, "trusted": True},
    {"name": "Together AI",        "url": "https://www.together.ai/blog/rss.xml",                     "category": 1, "trusted": True},
    news_search("Microsoft AI",    '"Microsoft" Copilot OR "Microsoft AI"', 1),
    news_search("Anthropic News",  '"Anthropic" OR "Claude AI" announcement', 1),
    news_search("Meta AI News",    '"Meta AI" model release', 1),
    news_search("Mistral News",    '"Mistral AI"', 1),
    news_search("xAI News",        '"xAI" OR "Grok" Elon model', 1),
    news_search("DeepSeek News",   '"DeepSeek" model OR release', 1),
    news_search("Perplexity News", '"Perplexity AI"', 1),
    news_search("ElevenLabs News", '"ElevenLabs" voice AI', 1),
    news_search("Cohere News",     '"Cohere" AI model', 1),
    news_search("Runway News",     '"Runway" AI video', 1),
    news_search("Stability AI",    '"Stability AI" OR "Stable Diffusion"', 1),

    # ---------- Science & space ----------
    {"name": "ScienceDaily AI",    "url": "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml", "category": 8, "trusted": True},
    {"name": "MIT News AI",        "url": "https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml",              "category": 8, "trusted": True},
    {"name": "Nature",             "url": "https://www.nature.com/nature.rss",                        "category": 8, "trusted": False},
    {"name": "NASA News",          "url": "https://www.nasa.gov/feed/",                               "category": 6, "trusted": False},

    # ---------- Leaders & podcasts (locked to category 3) ----------
    news_search("Sam Altman News",     '"Sam Altman"', 3, lock=True),
    news_search("Dario Amodei News",   '"Dario Amodei"', 3, lock=True),
    news_search("Demis Hassabis News", '"Demis Hassabis"', 3, lock=True),
    news_search("Jensen Huang News",   '"Jensen Huang" AI', 3, lock=True),
    news_search("Satya Nadella News",  '"Satya Nadella" AI', 3, lock=True),
    news_search("Elon Musk AI News",   '"Elon Musk" AI', 3, lock=True),
    {"name": "Lex Fridman Podcast","url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCSHZKyawb77ixDdsGog4iWA", "category": 3, "trusted": False, "lock": True},
    {"name": "Dwarkesh Podcast",   "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCXl4i9dYBrFOabk0xGmbkRA", "category": 3, "trusted": False, "lock": True},

    # ---------- Community & general (default: General News) ----------
    {"name": "r/ChatGPT",          "url": "https://www.reddit.com/r/ChatGPT/top/.rss?t=day",          "category": 10, "trusted": True},
    {"name": "r/LocalLLaMA",       "url": "https://www.reddit.com/r/LocalLLaMA/top/.rss?t=day",       "category": 10, "trusted": True},
    {"name": "r/artificial",       "url": "https://www.reddit.com/r/artificial/top/.rss?t=day",       "category": 10, "trusted": True},
    {"name": "Hacker News AI",     "url": "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT&points=50",    "category": 10, "trusted": True},
    news_search("Using AI To...",  '"using AI to"', 10),

    # ---------- AI media (AI-dedicated sections; verified live) ----------
    {"name": "The Verge AI",       "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "category": 10, "trusted": True},
    {"name": "Ars Technica AI",    "url": "https://arstechnica.com/ai/feed/",                         "category": 10, "trusted": True},
    {"name": "Wired AI",           "url": "https://www.wired.com/feed/tag/ai/latest/rss",             "category": 10, "trusted": True},
    {"name": "MIT Tech Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/", "category": 10, "trusted": True},
    {"name": "The Decoder",        "url": "https://the-decoder.com/feed/",                            "category": 10, "trusted": True},
    {"name": "The Register AI",    "url": "https://www.theregister.com/software/ai_ml/headlines.atom", "category": 10, "trusted": True},
    {"name": "Engadget",           "url": "https://www.engadget.com/feed/",                           "category": 10, "trusted": False},
    {"name": "Semafor Tech",       "url": "https://www.semafor.com/rss.xml",                          "category": 10, "trusted": False},

    # ---------- High-signal AI newsletters/blogs (verified live) ----------
    {"name": "TLDR AI",            "url": "https://tldr.tech/api/rss/ai",                             "category": 10, "trusted": True},
    {"name": "Ben's Bites",        "url": "https://www.bensbites.com/feed",                           "category": 10, "trusted": True},
    {"name": "Import AI",          "url": "https://jack-clark.net/feed/",                             "category": 10, "trusted": True},
    {"name": "Latent Space",       "url": "https://www.latent.space/feed",                            "category": 10, "trusted": True},
    {"name": "Interconnects",      "url": "https://www.interconnects.ai/feed",                        "category": 10, "trusted": True},
    {"name": "Simon Willison",     "url": "https://simonwillison.net/atom/everything/",               "category": 2, "trusted": False},

    # ---------- AI-news YouTube channels (verified live) ----------
    {"name": "Matt Wolfe",         "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UChpleBmo18P08aKCIgti38g", "category": 10, "trusted": True, "lock": True},
    {"name": "AI Explained",       "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCNJ1Ymd5yFuUPtn21xtRbbw", "category": 10, "trusted": True, "lock": True},
    {"name": "TheAIGRID",          "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCbY9xX3_jW5c2fjlZVBI4cg", "category": 10, "trusted": True, "lock": True},

    # ---------- Breaking model/product hunters (catch the newest names fast) ----------
    news_search("Breaking GPT-5",   '"GPT-5" OR "GPT-5.5" OR "GPT-6"', 1),
    news_search("Breaking Gemini 3",'"Gemini 3" OR "Gemini 3.0"', 1),
    news_search("Breaking Claude",  '"Claude Opus" OR "Claude 4" OR "Claude 5"', 1),
    news_search("Breaking Llama 4", '"Llama 4" OR "Llama 5" Meta', 1),
    news_search("Breaking Sora/Veo",'Sora OR "Veo 3" AI video generator', 1),
    news_search("AI Agents",        '"AI agent" OR "agentic AI" launch', 1),
    news_search("New AI App",       '"AI app" OR "AI feature" WhatsApp OR Android OR iPhone', 1),

    # ---------- South Asia angle (audience: Pakistan / India) ----------
    news_search("AI Pakistan",     'AI Pakistan OR Pakistani startup OR freelancer', 10),
    news_search("AI India",        'AI India startup OR "Indian AI" launch', 10),
    news_search("AI Jobs S Asia",  'AI jobs Pakistan OR India OR Fiverr OR Upwork', 10),

    # ---------- Topic hunters (fill the new categories) ----------
    news_search("AI in Space",       'AI space exploration OR "AI" NASA satellite', 6, max_age_days=30),
    news_search("AI in Agriculture", 'AI agriculture OR "AI" farming crops', 7, max_age_days=30),
    news_search("AI in Defense",     'AI military OR "AI" defense weapons', 5),
    news_search("AI in Coding",      'AI coding OR "vibe coding" OR "AI" developers', 2),
    news_search("AI & the Future",   '"AI" jobs future OR AGI prediction', 4, max_age_days=30),
    news_search("AI in Health",      'AI healthcare OR "AI" medicine doctors', 8),

    # ---------- Research papers (locked to category 9) ----------
    {"name": "arXiv AI",           "url": "https://rss.arxiv.org/rss/cs.AI",                          "category": 9, "trusted": True, "lock": True},
    {"name": "arXiv NLP (cs.CL)",  "url": "https://rss.arxiv.org/rss/cs.CL",                          "category": 9, "trusted": True, "lock": True},
    {"name": "arXiv ML (cs.LG)",   "url": "https://rss.arxiv.org/rss/cs.LG",                          "category": 9, "trusted": True, "lock": True},
    # Hugging Face trending papers are fetched separately in fetcher.py (no RSS)
]

# ---------------- Audience relevance (AI x Ahmad) ----------------
# The audience: everyday people in Pakistan/India. They care about how AI
# changes THEIR life, jobs, income, daily tools - NOT model internals.

# Boost: consumer-facing news people can use or try today
CONSUMER_KEYWORDS = [
    "free", "app", "apps", "feature", "features", "chatgpt", "whatsapp",
    "google", "android", "iphone", "launch", "launches", "release", "tool",
    "tools", "voice", "photo", "photos", "video", "videos", "image", "images",
    "now available", "update", "price", "cheaper", "viral", "demo", "try",
    "students", "everyone", "your phone", "translate",
]

# Boost hard + badge: Pakistan/India local angle
LOCAL_KEYWORDS = [
    "pakistan", "pakistani", "india", "indian", "urdu", "hindi", "rupee",
    "rupees", "freelance", "freelancer", "freelancers", "freelancing",
    "fiverr", "upwork", "jobs", "job market", "karachi", "lahore", "islamabad",
    "delhi", "mumbai", "bangalore", "south asia", "desi",
]

# Demote: technical/research talk the audience does not care about
RESEARCHY_KEYWORDS = [
    "paper", "papers", "arxiv", "benchmark", "benchmarks", "sota",
    "state-of-the-art", "training run", "parameters", "weights", "dataset",
    "datasets", "fine-tuning", "finetuning", "inference", "gpu", "tpu",
    "rlhf", "tokenizer", "quantization",
]

# ---------------- Keyword filter ----------------
# An item from an UNTRUSTED source must contain at least one of these
# words/phrases in its title to be saved. (Word-boundary matching, so
# "ai" will NOT match inside "rain" or "air".)
AI_KEYWORDS = [
    "ai", "a.i.", "artificial intelligence", "machine learning", "deep learning",
    "neural network", "llm", "large language model", "chatbot", "genai",
    "generative", "gpt", "chatgpt", "openai", "anthropic", "claude",
    "gemini", "deepmind", "copilot", "llama", "mistral", "grok", "xai",
    "hugging face", "transformer", "diffusion", "stable diffusion", "midjourney",
    "sora", "agi", "superintelligence", "agent", "robot", "autonomous",
    "nvidia", "altman", "amodei", "hassabis", "self-driving", "deepfake",
    "text-to-video", "text-to-image", "voice clone", "rag",
    # latest model / product / company names (2025-2026)
    "gpt-5", "gpt-4o", "gpt-4.1", "o3", "o4-mini", "claude opus", "claude sonnet",
    "claude code", "gemini 2.5", "gemini 3", "nano banana", "veo 3", "veo", "grok 4",
    "deepseek", "qwen", "kimi", "minimax", "mistral large", "llama 4", "phi-4",
    "command r", "sora 2", "gpt-image", "flux", "operator", "perplexity",
    "midjourney", "stargate", "agentforce", "devin", "cursor", "windsurf",
    "github copilot", "v0.dev", "bolt.new", "lovable", "replit agent",
    "model context protocol", "mcp server", "vibe coding", "agentic ai",
    "reasoning model", "world model", "safe superintelligence", "thinking machines",
    "elevenlabs", "runway", "suno", "notebooklm", "mixture of experts", "cohere",
]

# If a title contains any of these, it is junk -> always rejected,
# even from trusted sources. Tune this list during Phase 4.
JUNK_KEYWORDS = [
    "crypto", "bitcoin", "nft", "casino", "betting", "horoscope",
    "coupon", "promo code", "deal of the day", "best black friday",
]

# How similar two titles must be (0.0 - 1.0) to count as the SAME story.
# Same stories get grouped into one card with all source links.
DUPLICATE_SIMILARITY = 0.80

# Only compare against stories from the last N hours when checking duplicates.
DUPLICATE_WINDOW_HOURS = 48

# Ignore items older than this many days at first run (prevents flooding
# the database with months of old archive on day one).
MAX_ITEM_AGE_DAYS = 3

# Database file (created automatically in the project folder)
DB_FILE = "news.db"

# ---------------- Phone notifications (ntfy.sh) ----------------
# Setup on your phone (one time):
#   1. Install the "ntfy" app (Play Store / App Store)
#   2. Tap + and subscribe to the topic name below
# Keep the topic SECRET - anyone who knows it can read your alerts.
# On the cloud server the topic comes from a secret environment variable,
# so it never appears in the public code. Locally, put it in a file named
# ntfy_topic.txt (one line, ignored by git).
NTFY_SERVER = "https://ntfy.sh"


def _load_topic():
    topic = os.environ.get("NTFY_TOPIC")
    if topic:
        return topic.strip()
    try:
        with open(os.path.join(os.path.dirname(__file__), "ntfy_topic.txt")) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


NTFY_TOPIC = _load_topic()

# Sources whose new items trigger an INSTANT phone alert
# (official lab announcements only - your "be first in Urdu" moments).
INSTANT_SOURCES = [
    "OpenAI Blog",
    "Google DeepMind",
    "Hugging Face Blog",
    "Google AI Blog",
    "NVIDIA AI Blog",
]

# Digest times (24h clock, your PC's local time). All non-instant items
# are collected and sent as one grouped summary at these hours.
DIGEST_HOURS = [8, 14, 21]

# Max stories per category inside one digest (newest first).
DIGEST_MAX_PER_PILLAR = 8

# Your online dashboard (opens when you tap a digest notification).
DASHBOARD_URL = "https://radar.hafizahmad.com/studio.html"

# Auto-delete news older than this many days (keeps the archive lean). Runs on
# every fetch cycle. Note: the Trends tab compares this week vs last week, so a
# value below 14 limits its "last week" baseline.
NEWS_RETENTION_DAYS = 7

# ---- "Post this" nudges -------------------------------------------------
# A gentle, action-oriented alert: every couple of hours (and instantly for a
# big story) your phone gets "📲 Post this — <headline>". Tap it -> Studio opens.
# It never nudges the same story twice, and stays quiet overnight (PK time).
NUDGE_ENABLED = True
NUDGE_EVERY_HOURS = 2        # minimum gap between routine nudges
NUDGE_MIN_SCORE = 6          # only stories worth filming get a nudge
NUDGE_URGENT_SCORE = 12      # a really big story nudges immediately (ignores the gap)
NUDGE_TZ_OFFSET = 5          # your timezone vs the server (PK = UTC+5; GitHub runs in UTC)
NUDGE_QUIET_START = 1        # no routine nudges between these local hours (1am–7am)
NUDGE_QUIET_END = 7


# ==================== AI PULSE ====================
# Pulse is a SEPARATE feature from the news "Trends" tab. It surfaces what
# people are actually USING, SEARCHING, and STRUGGLING with in AI right now
# (Reddit/HN/YouTube/Google-Trends), and turns each signal into a content
# suggestion for AI x Ahmad. All collection + any LLM analysis runs server-side
# (GitHub Action) and writes docs/pulse.json; the frontend only reads that file.

# Master switch. False = free, deterministic, NO API key needed (raw mode).
# True = LLM enriches signals (needs a Groq or Anthropic key in Secrets).
PULSE_USE_LLM = True

# Used only when PULSE_USE_LLM = True. Keys come from GitHub Secrets, never here.
PULSE_LLM_PROVIDER = "groq"               # "groq" | "anthropic"
PULSE_LLM_MODELS = {                       # verify current model strings at build time
    "groq": "llama-3.3-70b-versatile",
    "anthropic": "claude-haiku-4-5",
}

# Topics we track (search/usage signals are pulled around these).
PULSE_SEED_TERMS = [
    "AI tool", "ChatGPT", "AI image generator", "AI video", "AI agent",
    "free AI tool", "AI for students", "AI to make money",
]

# Global signal + local relevance.
PULSE_GEOS = ["US", "PK", "IN"]

# Subreddits = the primary source for "problems people face".
PULSE_SUBREDDITS = [
    "ChatGPT", "ClaudeAI", "OpenAI", "artificial",
    "StableDiffusion", "midjourney", "LocalLLaMA", "singularity",
]

# YouTube collector (needs YOUTUBE_API_KEY; silently skipped if absent).
PULSE_YT_MAX_RESULTS = 8
PULSE_YT_LOOKBACK_DAYS = 7

# Output caps.
PULSE_MAX_TRENDS = 12
PULSE_MAX_PAIN_POINTS = 8

# Momentum: ratio of today's signal strength vs the trailing-days average.
PULSE_MOMENTUM = {"rising": 1.25, "cooling": 0.80}

# Known AI tools/techniques for deterministic clustering (raw mode). Editable.
PULSE_TOOL_DICT = [
    "nano banana", "veo", "sora", "gemini", "chatgpt", "claude", "midjourney",
    "kling", "deepseek", "grok", "llama", "stable diffusion", "flux", "runway",
    "perplexity", "cursor", "copilot", "suno", "elevenlabs", "qwen", "mistral",
    "gpt-4", "gpt-5", "o1", "o3", "dall-e", "heygen", "pika", "luma", "wan",
]

# Problem-indicator keywords (raw-mode pain-point detection).
PULSE_PROBLEM_KEYWORDS = [
    "limit", "limits", "rate limit", "error", "not working", "down",
    "expensive", "broken", "can't", "cannot", "issue", "problem", "slow",
    "banned", "deprecated", "removed", "bug", "crash", "fails", "failed", "stuck",
]

# Reuse the existing local-angle keyword list for Pulse local relevance.
PULSE_LOCAL_KEYWORDS = LOCAL_KEYWORDS
