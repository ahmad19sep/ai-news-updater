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
| `python dashboard.py` | Open the **Creator Studio** at http://localhost:5000 |

## Creator Studio (on your PC)

Three tabs at http://localhost:5000:

- **📰 News** — all stories with filters/search, a **🎬 Plan** button on every
  story (sends it to the planner) and done marks
- **🎬 Planner** — your video board: Idea → Script → Record → Edit → Uploaded
  → Published. Cards hold notes, platform (long/short/both) and planned date
- **📝 Video Prep** — paste a story link → the tool fetches the article, finds
  related coverage from your archive, and builds a ready prompt: **copy it
  into your Claude app** to get the full script kit (no API needed)

Your plans and done marks live in `plans.db` (only on your PC, never pushed),
so "Get latest" always pulls cloud news without conflicts.

## Phone setup (one time)

1. Install the **ntfy** app — [Play Store](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / App Store
2. Tap **+** and subscribe to your private topic (see `NTFY_TOPIC` in `config.py`)
3. Run `python main.py --test` — a notification should appear on your phone

Keep the topic name secret — it is your private channel.

**Instant alerts** (high priority, tap to open the link) fire only for official lab
announcements: OpenAI, Google DeepMind, Google AI, NVIDIA, Hugging Face.
Everything else arrives in **3 daily digests** grouped by pillar.

## The 10 categories

Stories are sorted by **what the title talks about** (keyword rules in
`config.py`), not just where they came from:

1. **New Tools & Models** | 2. **AI in Coding** | 3. **Leaders & Podcasts**
4. **AI & the Future** | 5. **AI in Defense** | 6. **AI in Space**
7. **AI in Agriculture** | 8. **AI in Health & Science** | 9. **Research Papers**
10. **AI General News**

Changed the rules? Run `python reclassify.py` to re-sort the whole archive.

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
