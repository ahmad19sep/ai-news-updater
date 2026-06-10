"""
AI News Radar - Configuration
All news sources, organized by the 5 content pillars.
Every source here is FREE (RSS feeds and public APIs).
"""

# Pillar names (used in database and display)
PILLARS = {
    1: "Product & Model Updates",
    2: "AI in Science",
    3: "Leaders & Voices",
    4: "Interesting Uses",
    5: "Research Breakthroughs",
}


def google_news(query):
    """Build a Google News RSS search URL for any query."""
    q = query.replace(" ", "+").replace('"', "%22")
    return f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"


def bing_news(query):
    """Bing News RSS for the same query - used as automatic backup,
    because Google News blocks cloud server IPs (GitHub Actions)."""
    q = query.replace(" ", "+").replace('"', "%22")
    return f"https://www.bing.com/news/search?q={q}&format=rss"


def news_search(name, query, pillar):
    """A news-search feed: tries Google News first, falls back to Bing News."""
    return {"name": name, "url": google_news(query), "fallback": bing_news(query),
            "pillar": pillar, "trusted": False}


def youtube_channel(channel_id):
    """Build a YouTube RSS feed URL for a channel."""
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


# Each feed: name, url, pillar, trusted
# trusted=True  -> official AI source, items pass WITHOUT keyword filter
# trusted=False -> general source, items must contain AI keywords to pass
FEEDS = [
    # ---------- Pillar 1: Product & Model Updates (official labs) ----------
    {"name": "OpenAI Blog",        "url": "https://openai.com/news/rss.xml",                          "pillar": 1, "trusted": True},
    {"name": "Google DeepMind",    "url": "https://deepmind.google/blog/rss.xml",                     "pillar": 1, "trusted": True},
    {"name": "Hugging Face Blog",  "url": "https://huggingface.co/blog/feed.xml",                     "pillar": 1, "trusted": True},
    news_search("Microsoft AI",    '"Microsoft" Copilot OR "Microsoft AI"', 1),
    {"name": "Google AI Blog",     "url": "https://blog.google/technology/ai/rss/",                   "pillar": 1, "trusted": True},
    {"name": "NVIDIA AI Blog",     "url": "https://blogs.nvidia.com/blog/category/generative-ai/feed/", "pillar": 1, "trusted": True},
    # Labs without official RSS -> Google News queries (still free)
    news_search("Anthropic News",  '"Anthropic" OR "Claude AI" announcement', 1),
    news_search("Meta AI News",    '"Meta AI" model release', 1),
    news_search("Mistral News",    '"Mistral AI"', 1),
    news_search("xAI News",        '"xAI" OR "Grok" Elon model', 1),

    # ---------- Pillar 2: AI in Science ----------
    {"name": "ScienceDaily AI",    "url": "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml", "pillar": 2, "trusted": True},
    {"name": "MIT News AI",        "url": "https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml",              "pillar": 2, "trusted": True},
    {"name": "Nature",             "url": "https://www.nature.com/nature.rss",                        "pillar": 2, "trusted": False},
    {"name": "NASA News",          "url": "https://www.nasa.gov/feed/",                               "pillar": 2, "trusted": False},

    # ---------- Pillar 3: Leaders & Voices ----------
    news_search("Sam Altman News",     '"Sam Altman"', 3),
    news_search("Dario Amodei News",   '"Dario Amodei"', 3),
    news_search("Demis Hassabis News", '"Demis Hassabis"', 3),
    news_search("Jensen Huang News",   '"Jensen Huang" AI', 3),
    news_search("Satya Nadella News",  '"Satya Nadella" AI', 3),
    news_search("Elon Musk AI News",   '"Elon Musk" AI', 3),
    # Key podcast channels on YouTube
    {"name": "Lex Fridman Podcast","url": youtube_channel("UCSHZKyawb77ixDdsGog4iWA"),                "pillar": 3, "trusted": False},
    {"name": "Dwarkesh Podcast",   "url": youtube_channel("UCXl4i9dYBrFOabk0xGmbkRA"),                "pillar": 3, "trusted": False},

    # ---------- Pillar 4: Interesting Uses ----------
    {"name": "r/ChatGPT",          "url": "https://www.reddit.com/r/ChatGPT/top/.rss?t=day",          "pillar": 4, "trusted": True},
    {"name": "r/LocalLLaMA",       "url": "https://www.reddit.com/r/LocalLLaMA/top/.rss?t=day",       "pillar": 4, "trusted": True},
    {"name": "r/artificial",       "url": "https://www.reddit.com/r/artificial/top/.rss?t=day",       "pillar": 4, "trusted": True},
    {"name": "Hacker News AI",     "url": "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT&points=50",    "pillar": 4, "trusted": True},
    news_search("Using AI To...",  '"using AI to"', 4),

    # ---------- Pillar 5: Research Breakthroughs ----------
    {"name": "arXiv AI",           "url": "https://rss.arxiv.org/rss/cs.AI",                          "pillar": 5, "trusted": True},
    # Hugging Face trending papers are fetched separately in fetcher.py (no RSS)
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
import os

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

# Max stories per pillar inside one digest (newest first).
DIGEST_MAX_PER_PILLAR = 8
