# AI News Radar

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
| `python main.py` | Fetch all sources once and show a summary |
| `python main.py --loop` | Keep running, fetch every 60 minutes |
| `python main.py --latest` | Show the 20 newest stories in the terminal |

## The 5 pillars

1. **Product & Model Updates** — OpenAI, DeepMind, Anthropic, Meta, Mistral, xAI, Microsoft, NVIDIA, Hugging Face
2. **AI in Science** — ScienceDaily, MIT News, Nature, NASA
3. **Leaders & Voices** — Altman, Amodei, Hassabis, Huang, Nadella, Musk + podcasts
4. **Interesting Uses** — Reddit, Hacker News, Google News
5. **Research Breakthroughs** — arXiv, Hugging Face trending papers

## Files

- `config.py` — all sources and filter keywords (**edit this to tune filters**)
- `fetcher.py` — downloads feeds, applies filters, saves to database
- `filters.py` — AI keyword filter, junk filter, duplicate detector
- `database.py` — SQLite storage (`news.db`, created automatically)
- `main.py` — entry point

## Build status

- [x] Phase 1 — Fetcher + database + keyword filter
- [ ] Phase 2 — ntfy.sh phone notifications (instant alerts + digests)
- [ ] Phase 3 — Web dashboard with filters and search
- [ ] Phase 4 — Tune filters during real use
