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
    {"name": "Microsoft AI",       "url": google_news('"Microsoft" Copilot OR "Microsoft AI"'),      "pillar": 1, "trusted": False},
    {"name": "Google AI Blog",     "url": "https://blog.google/technology/ai/rss/",                   "pillar": 1, "trusted": True},
    {"name": "NVIDIA AI Blog",     "url": "https://blogs.nvidia.com/blog/category/generative-ai/feed/", "pillar": 1, "trusted": True},
    # Labs without official RSS -> Google News queries (still free)
    {"name": "Anthropic News",     "url": google_news('"Anthropic" OR "Claude AI" announcement'),     "pillar": 1, "trusted": False},
    {"name": "Meta AI News",       "url": google_news('"Meta AI" model release'),                     "pillar": 1, "trusted": False},
    {"name": "Mistral News",       "url": google_news('"Mistral AI"'),                                "pillar": 1, "trusted": False},
    {"name": "xAI News",           "url": google_news('"xAI" OR "Grok" Elon model'),                  "pillar": 1, "trusted": False},

    # ---------- Pillar 2: AI in Science ----------
    {"name": "ScienceDaily AI",    "url": "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml", "pillar": 2, "trusted": True},
    {"name": "MIT News AI",        "url": "https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml",              "pillar": 2, "trusted": True},
    {"name": "Nature",             "url": "https://www.nature.com/nature.rss",                        "pillar": 2, "trusted": False},
    {"name": "NASA News",          "url": "https://www.nasa.gov/feed/",                               "pillar": 2, "trusted": False},

    # ---------- Pillar 3: Leaders & Voices ----------
    {"name": "Sam Altman News",    "url": google_news('"Sam Altman"'),                                "pillar": 3, "trusted": False},
    {"name": "Dario Amodei News",  "url": google_news('"Dario Amodei"'),                              "pillar": 3, "trusted": False},
    {"name": "Demis Hassabis News","url": google_news('"Demis Hassabis"'),                            "pillar": 3, "trusted": False},
    {"name": "Jensen Huang News",  "url": google_news('"Jensen Huang" AI'),                           "pillar": 3, "trusted": False},
    {"name": "Satya Nadella News", "url": google_news('"Satya Nadella" AI'),                          "pillar": 3, "trusted": False},
    {"name": "Elon Musk AI News",  "url": google_news('"Elon Musk" AI'),                              "pillar": 3, "trusted": False},
    # Key podcast channels on YouTube
    {"name": "Lex Fridman Podcast","url": youtube_channel("UCSHZKyawb77ixDdsGog4iWA"),                "pillar": 3, "trusted": False},
    {"name": "Dwarkesh Podcast",   "url": youtube_channel("UCXl4i9dYBrFOabk0xGmbkRA"),                "pillar": 3, "trusted": False},

    # ---------- Pillar 4: Interesting Uses ----------
    {"name": "r/ChatGPT",          "url": "https://www.reddit.com/r/ChatGPT/top/.rss?t=day",          "pillar": 4, "trusted": True},
    {"name": "r/LocalLLaMA",       "url": "https://www.reddit.com/r/LocalLLaMA/top/.rss?t=day",       "pillar": 4, "trusted": True},
    {"name": "r/artificial",       "url": "https://www.reddit.com/r/artificial/top/.rss?t=day",       "pillar": 4, "trusted": True},
    {"name": "Hacker News AI",     "url": "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT&points=50",    "pillar": 4, "trusted": True},
    {"name": "Using AI To...",     "url": google_news('"using AI to"'),                               "pillar": 4, "trusted": False},

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
