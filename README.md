# AI News Radar

**Live dashboard:** https://ahmad19sep.github.io/ai-news-updater/ (updates every hour)

Your 24/7 eyes on the AI world. Fetches every important AI story — with original
source links — so you can make videos in Urdu, Hindi, and English before anyone else.

Full plan: [AI-News-Radar-Project-Blueprint.md](AI-News-Radar-Project-Blueprint.md)

## Setup (one time)

```
pip install -r requirements.txt
```

## How to use

| Command | What it does |
|---------|--------------|
| `python main.py` | Fetch once + send instant alerts for lab announcements |
| `python main.py --loop` | Run forever: fetch hourly + digests at 8:00, 14:00, 21:00 |
| `python main.py --latest` | Show the 20 newest stories in the terminal |
| `python main.py --digest` | Send the digest to your phone right now |
| `python main.py --test` | Send a test notification to your phone |
| `python dashboard.py` | Open the dashboard at http://localhost:5000 |

## Phone setup (one time)

1. Install the **ntfy** app — [Play Store](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / App Store
2. Tap **+** and subscribe to your private topic (see `NTFY_TOPIC` in `config.py`)
3. Run `python main.py --test` — a notification should appear on your phone

Keep the topic name secret — it is your private channel.

**Instant alerts** (high priority, tap to open the link) fire only for official lab
announcements: OpenAI, Google DeepMind, Google AI, NVIDIA, Hugging Face.
Everything else arrives in **3 daily digests** grouped by pillar.

## The 5 pillars

1. **Product & Model Updates** — OpenAI, DeepMind, Anthropic, Meta, Mistral, xAI, Microsoft, NVIDIA, Hugging Face
2. **AI in Science** — ScienceDaily, MIT News, Nature, NASA
3. **Leaders & Voices** — Altman, Amodei, Hassabis, Huang, Nadella, Musk + podcasts
4. **Interesting Uses** — Reddit, Hacker News, Google News
5. **Research Breakthroughs** — arXiv, Hugging Face trending papers

## Files

- `config.py` — all sources, filter keywords, ntfy topic, digest times (**edit this to tune**)
- `fetcher.py` — downloads feeds, applies filters, saves to database
- `filters.py` — AI keyword filter, junk filter, duplicate detector
- `database.py` — SQLite storage (`news.db`, created automatically)
- `notifier.py` — ntfy.sh phone notifications (instant alerts + digests)
- `main.py` — entry point

## Build status

- [x] Phase 1 — Fetcher + database + keyword filter
- [x] Phase 2 — ntfy.sh phone notifications (instant alerts + digests)
- [x] Cloud deploy — GitHub Actions fetches hourly, PC can stay off
- [x] Phase 3 — Web dashboard (`dashboard.py`) with filters, search, done marks
- [ ] Phase 4 — Tune filters during real use
