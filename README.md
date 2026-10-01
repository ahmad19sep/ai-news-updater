# AI x Ahmad — content system

A radar that watches the AI world around the clock, a pipeline of small agents
that turns the best stories into **LinkedIn drafts written in your voice**, and
a Studio where you pick, edit, schedule and post. Nothing posts by itself.

LinkedIn is the only active channel. X, Reddit, Facebook, WhatsApp Channel and
YouTube come later, each as its own agent that adapts an *approved* LinkedIn post.

## 🔗 Your links

| What | Link |
|------|------|
| 🎛 **Studio** (private, passcode) | https://ahmad19sep.github.io/ai-news-updater/studio.html |
| 🗄 Old studio (kept for reference) | https://ahmad19sep.github.io/ai-news-updater/studio-legacy.html |
| 📰 Public news site | https://ahmad19sep.github.io/ai-news-updater/ |
| ☁️ Cloud runs + logs | https://github.com/ahmad19sep/ai-news-updater/actions |
| 📱 Phone alerts | ntfy app, topic in `ntfy_topic.txt` (secret) |

## How it works

```
hourly collector (~90 feeds)  ──►  news.db
                                     │
   python run_pipeline.py            ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │ 1 triage   score every new story 1-10 for your audience               │
   │            FREE mode: the radar's own rules (runs hourly in the cloud) │
   │            API mode:  Haiku reads the headlines and explains why       │
   │ 2 enrich   fetch the article, build a source pack (never an LLM)      │
   │ 3 angle    2-3 honest angles + hook + format                           │
   │ 4 writer   the LinkedIn draft + first comment + hashtags               │
   │ 5 verify   every number must exist in the source; banned phrases;      │
   │            AI-smell fact-check; one rewrite if it fails                │
   └──────────────────────────────────────────────────────────────────────┘
        3-5 in FREE mode = you, in the Studio: copy the agent's prompt into your
        Claude / ChatGPT subscription, paste the JSON answer back, it is parsed
        and checked. In API mode the Claude agents do 3-5 (~$0.30 per run).
                                     │  shared state (Firebase or docs/pipeline.json)
                                     ▼
   Studio:  Today · Discover · Ideas · Compose · Schedule · Published · Library · Settings
            you shortlist → write/edit in your voice → approve → slot → copy → post on LinkedIn → ✓ Mark as posted → rate
```

**Free mode is the default** (`PIPELINE_MODE = "free"` in `config.py`): no API
key, no cost. Ideas fill up every hour from the cloud; the top ones already
have their article text fetched, so the prompt you copy carries real source
text, not a headline. Switch to API mode per run (`--mode api`) or in config
when you want the agents to draft automatically; `PIPELINE_DAILY_BUDGET_USD`
hard-stops a run at $1.

Two jobs stay yours on purpose: **picking the story** and **the final rewrite**.
Generic AI-sounding posts lose reach on LinkedIn; your edit is the product.

A draft is never written from a headline alone. If the article cannot be
fetched, the pack is marked *thin* and the writer is told to stay short and
honest. Every number in a draft is checked against the source text; the
verifier lists what it could not support.

## Daily flow

1. **Ideas arrive** — the hourly cloud job triages new stories (free) and
   fetches the articles for the best ones. **Today** shows the top picks.
2. **Ideas → ✍️ Write** on the story you want. In **Compose**: *Copy writer
   prompt* → paste into Claude.ai / ChatGPT → paste the JSON answer → *Parse*.
   The post, first comment, hashtags, claims and checks fill in. (In API mode
   the drafts are already waiting here.)
3. Edit the post in your voice (live LinkedIn preview, hook length, checks,
   claims table, source pack). Optional: *Copy fact-check prompt* the same
   way. For a feed image, use **Copy image prompt** after editing the post;
   the brief carries your current text and asks for a readable image with alt
   text. Then **Approve**.
4. **Schedule** — put it on the next free slot (Tue/Wed/Thu 09:00 by default).
5. When it is due: **Copy post → Open LinkedIn → paste → post → paste the first
   comment → ✓ Mark as posted**.
6. A day later, in **Published**, rate it 1-10 and note the numbers. Your best
   posts go into `content/examples.md` so the writer sounds more like you.

Want a story the pipeline missed? **Discover → 💡 Save as idea**, or in Ideas
click **✍️ Draft** (copies the exact command) or **📝 Write myself** (paste facts,
copy a grounded prompt into any AI, paste the post back).

## Your voice lives in plain files

| File | What it controls |
|------|------------------|
| `content/voice.md` | who you are, audience, tone, topic priorities, never-do list |
| `content/hooks.json` | hook patterns the angle agent draws on |
| `content/examples.md` | your best posts — the writer imitates the voice, never the content |
| `content/linkedin_rules.md` | the rules the writer and verifier enforce |
| `content/image_prompt.md` | image brief guidelines copied from Compose |
| `config.py` (bottom) | models per agent, budget, thresholds, drafts per run |

Edit them any time; every run reads them fresh. The Studio's Library tab shows them.

## Setup (one time)

```
pip install -r requirements.txt
```

Free mode needs nothing else. For API mode set `ANTHROPIC_API_KEY`, or put it
in `anthropic_key.txt` (git-ignored); in the cloud it is the `ANTHROPIC_API_KEY`
secret. For one shared state across devices and the cloud, keep `FIREBASE_URL`
and `SITE_PASSCODE` set (cloud secrets; `firebase_url.txt` / `site_passcode.txt`
locally). Without Firebase the pipeline writes `docs/pipeline.json` and Studio
edits stay in that browser.

## Commands

| Command | What it does |
|---------|--------------|
| `python run_pipeline.py` | Free: triage new stories + fetch articles for the top 10 (no key) |
| `python run_pipeline.py --mode api` | Claude agents: triage, then draft + verify the top 5 (~$0.30) |
| `python run_pipeline.py --triage` | Only score new stories into Ideas |
| `python run_pipeline.py --mode api --draft --ids a1b2c3,d4e5f6` | Draft specific candidates with the API (the Studio copies this for you) |
| `python run_pipeline.py --dry-run` | Show what would run, no cost |
| `python run_pipeline.py --status` | What is in the store, last runs and cost |
| `python main.py` | Fetch news once + instant alerts (the cloud does this hourly) |
| `python generate_studio.py` | Rebuild the Studio (`docs/studio.html`) |
| `python generate_site.py` | Rebuild the old studio (`docs/studio-legacy.html`) |
| `python generate_public.py` | Rebuild the public site |
| `python generate_pulse.py` | Rebuild Pulse signals (`docs/pulse.json`) |
| `python -m unittest tests.test_pipeline` | Pipeline tests with a fake Claude (no key, no cost) |
| `python -m unittest test_agent_ai_radar test_agent_discovery` | Classifier tests |
| `node studio_test.js` | Drives every Studio screen in JSDOM (`npm i --no-save jsdom` first) |
| `node smoke_test.js` / `node ui_test.js` | Old studio tests |

Cloud workflows: `fetch.yml` (hourly news + free triage + site builds),
`pipeline.yml` (API drafts, "Run workflow" on demand only), `pulse.yml` (every 6 h).

## Phone setup (one time)

1. Install the **ntfy** app — [Play Store](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / App Store
2. Subscribe to your private topic (`ntfy_topic.txt` / `NTFY_TOPIC`)
3. `python main.py --test` — a notification should appear

Instant alerts fire only for official lab announcements; the pipeline sends
"drafts ready"; everything else arrives in 3 daily digests.

## The 10 categories

Stories are sorted by **what the title talks about** (keyword rules in `config.py`):

1. New Tools & Models | 2. AI in Coding | 3. Leaders & Podcasts | 4. AI & the Future
5. AI in Defense | 6. AI in Space | 7. AI in Agriculture | 8. AI in Health & Science
9. Research Papers | 10. AI General News

## Files

**Agents (`agents/`)** — one job each
- `llm.py` — Claude calls (JSON in/out), cost ledger, budget; `store.py` — shared state (Firebase or `docs/pipeline.json`)
- `sources.py` (reads news.db) · `triage.py` · `enrich.py` · `angle.py` · `writer.py` · `verify.py` · `content.py` (loads `content/`)
- `run_pipeline.py` — the orchestrator CLI

**Studio** — `studio/index.html`, `studio/app.css`, `studio/app.js` are the source; `generate_studio.py` inlines them with the latest news into `docs/studio.html`

**Collection** — `config.py` (sources, rules, pipeline settings), `fetcher.py`, `filters.py`, `scoring.py`, `database.py`, `main.py`, `notifier.py`, `digest.py`

**Other outputs** — `generate_public.py` (public site), `generate_pulse.py` + `collectors/` + `analyzer/` (Pulse), `generate_site.py` + `docs/templates.js` (old studio), `agent_ai_radar.py` (Agents & AI classifier used by Discover)

**Optional / legacy** — `x-worker/`, `x-extension/`, `dashboard.py`

Setup notes: [PULSE-SETUP.md](PULSE-SETUP.md) · [X-PIPELINE-SETUP.md](X-PIPELINE-SETUP.md) · [XMINI_API.md](XMINI_API.md) · [DOCUMENTATION.md](DOCUMENTATION.md)

## Known gaps

- **Firebase rules are permissive.** The Studio and the agents use unauthenticated
  REST writes under a secret path; the passcode is a screen gate, not database
  authorization. Owner-scoped auth is the next real security job.
- LinkedIn analytics are typed in by hand (LinkedIn does not expose personal
  post stats to individual apps).
- Other channels are placeholders in Settings until their agents exist.
