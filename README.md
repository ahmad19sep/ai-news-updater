# AI News Radar — LinkedIn Studio

A news radar that watches the AI world around the clock, and a studio that turns
one selected story into **one useful LinkedIn post**. Fewer posts, better sourced.

## 🔗 Your links (bookmark these)

| What | Link |
|------|------|
| 🌍 **Studio** (private, passcode) | https://ahmad19sep.github.io/ai-news-updater/studio.html |
| 📰 Public news site | https://ahmad19sep.github.io/ai-news-updater/ |
| ☁️ Cloud runs + logs | https://github.com/ahmad19sep/ai-news-updater/actions |
| 📦 Code | https://github.com/ahmad19sep/ai-news-updater |
| 📱 Phone alerts | ntfy app, topic in `ntfy_topic.txt` (secret) |

## Channels

**LinkedIn is the only active publishing workflow.** X is optional — a separate
adaptation you choose to make, never automatic. Reddit is for genuine
participation, not cross-posting. Facebook, Instagram, TikTok, WhatsApp and
YouTube outputs were retired: their prompts, buttons and handlers are gone.

Nothing posts by itself. The studio drafts, you review, you post.

## Writing a post

In the Studio, open a story and hit **in LinkedIn draft**:

1. **Paste the facts** — a few lines from the article. No AI can open your link,
   so this is what the post is actually built from.
2. **Pick a mode** — 🧠 *Insight* (one development and what it means for your
   audience) or 🛠️ *Practical* (one action, checklist or tradeoff the source
   really supports). Both copy a prompt for ChatGPT / Gemini / Claude.
3. **Paste the output back** and hit **Validate**. You get the post, its sources,
   and private review notes that never leave the studio.
4. **Copy post → Open LinkedIn → ✓ Mark as posted.** Only that last tick marks a
   story handled; copying or opening LinkedIn changes nothing.

If you paste only a headline, the writer is told to answer `needs_input` and ask
for what it needs rather than invent details. If a story has no useful angle for
your audience it can answer `skip` — no post is a fine outcome.

Your audience and any personal note are remembered in synced settings, so you
set them once. Firsthand claims ("I tested this") only appear when you supply a
real note; otherwise the post stays an attributed explanation.

## Setup (one time)

```
pip install -r requirements.txt
```

## Commands

| Command | What it does |
|---------|--------------|
| `python main.py` | Fetch once + send instant alerts for lab announcements |
| `python main.py --loop` | Run forever: fetch hourly + digests at 8:00, 14:00, 21:00 |
| `python main.py --latest` | Show the 20 newest stories in the terminal |
| `python main.py --digest` | Send the digest to your phone right now |
| `python main.py --test` | Send a test notification to your phone |
| `python generate_site.py` | Rebuild the studio (`docs/studio.html`) |
| `python generate_public.py` | Rebuild the public site (`docs/index.html`) |
| `python generate_pulse.py` | Rebuild the Pulse signals (`docs/pulse.json`) |
| `python reclassify.py` | Re-sort the archive after editing category rules |
| `node dump_prompts.js` | Regenerate `PROMPTS.md` from `docs/templates.js` |
| `node smoke_test.js` | Prompt-library + boot checks (needs `npm i --no-save jsdom`) |
| `node ui_test.js` | Drives the studio UI: every tab + the whole draft flow |

The cloud does all of this hourly on its own — see `.github/workflows/fetch.yml`.
Your PC can stay off.

## Phone setup (one time)

1. Install the **ntfy** app — [Play Store](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / App Store
2. Tap **+** and subscribe to your private topic (`ntfy_topic.txt` / `NTFY_TOPIC`)
3. Run `python main.py --test` — a notification should appear

Keep the topic name secret — it is your private channel. **Instant alerts** fire
only for official lab announcements (OpenAI, Google DeepMind, Google AI, NVIDIA,
Hugging Face); everything else arrives in 3 daily digests.

## The 10 categories

Stories are sorted by **what the title talks about** (keyword rules in
`config.py`), not by where they came from:

1. **New Tools & Models** | 2. **AI in Coding** | 3. **Leaders & Podcasts**
4. **AI & the Future** | 5. **AI in Defense** | 6. **AI in Space**
7. **AI in Agriculture** | 8. **AI in Health & Science** | 9. **Research Papers**
10. **AI General News**

## Files

**Collection**
- `config.py` — sources, filter keywords, ntfy topic, digest times, retention (**edit to tune**)
- `fetcher.py` — downloads ~90 feeds in parallel, filters, dedupes, saves
- `filters.py` — AI keyword filter, junk filter, fuzzy duplicate detector
- `scoring.py` — story ranking + week-over-week trend terms
- `database.py` — SQLite storage (`news.db`, created automatically)
- `main.py` — entry point; `notifier.py` — ntfy phone alerts; `digest.py` — weekly digest

**Studio + sites**
- `generate_site.py` — builds the private studio (`docs/studio.html`)
- `docs/templates.js` — **the prompts** (authored source; `docs/studio.html` is generated)
- `generate_public.py` — builds the public news site; `generate_pulse.py` + `collectors/` + `analyzer/` — Pulse signals
- `x-worker/` — optional Cloudflare Worker for X (draft or post; never posts without an explicit action)

Setup notes: [PULSE-SETUP.md](PULSE-SETUP.md) · [X-PIPELINE-SETUP.md](X-PIPELINE-SETUP.md) · [XMINI_API.md](XMINI_API.md)

## Known gaps

- **Firebase rules are permissive.** Sync and captures use unauthenticated REST
  writes; the studio's passcode is a screen gate, not database authorization.
  Anyone who learns a path can write to it. Proper owner-scoped auth is the next
  real security job.
- The public site and weekly digest still rebuild hourly; neither is needed for a
  LinkedIn post to stand on its own.
