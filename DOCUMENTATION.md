# AI Radar Studio — Documentation

*An AI news radar and a LinkedIn writing desk, built for the "AI x Ahmad" (@aixahmad) brand.*
*Runs on $0 infrastructure. One person operates the whole thing.*

---

## 1. What it is

AI Radar Studio **collects AI news from ~90 sources every hour**, scores and de-duplicates it, and helps turn a selected story into **one useful LinkedIn post** — built only from facts the operator actually supplies, with the sources kept visible.

**LinkedIn is the only active publishing workflow.** X is an optional channel you adapt into deliberately; Reddit is for genuine participation, not cross-posting. Facebook, Instagram, TikTok, WhatsApp and YouTube outputs were retired in September 2026 — their prompts, buttons and handlers are gone, not just hidden.

Nothing posts by itself. The AI drafts, the operator reviews and posts. Parsing a draft, copying it, or opening LinkedIn changes nothing: only an explicit "✓ Mark as posted" takes a story off the lists.

---

## 2. Where it is deployed

| Piece | Where | URL / location | Cost |
|---|---|---|---|
| **Studio (the app)** | GitHub Pages | https://ahmad19sep.github.io/ai-news-updater/studio.html | $0 |
| **Public news website** | GitHub Pages | https://ahmad19sep.github.io/ai-news-updater/ | $0 |
| **Data & sync** | Firebase Realtime DB | `aixahmad-studio-default-rtdb.asia-southeast1` | $0 (free tier) |
| **Optional generation API** | Cloudflare Worker | holds the Anthropic key server-side | $0 host + ~$0.01/generation |
| **Automation (crons)** | GitHub Actions | hourly news fetch · 6-hourly Pulse | $0 |
| **Browser extension** | Chrome (unpacked) | `x-extension/` folder in the repo | $0 |

**How deployment works:** the site is 100% static. A Python generator (`generate_site.py` / `generate_public.py`) builds HTML into the repo's **`docs/` folder**; every push to `main` makes GitHub Pages rebuild and serve it (~1 minute). No servers to maintain.

**How to verify it's live:** open the URLs above, or GitHub repo → **Settings → Pages**, or the **Actions** tab → "pages build and deployment" (green check = deployed).

---

## 3. Architecture (the big picture)

```
~90 RSS feeds + NewsData.io + HuggingFace papers
        │  (GitHub Action, hourly)
        ▼
 fetcher.py → SQLite (news.db) → filter, fuzzy de-dup, score, 30-day purge
        │                         (30 days because the trend view compares
        │                          this week against the week before it)
        ├─► generate_site.py   → docs/studio.html   (the Studio app)
        ├─► generate_public.py → docs/index.html    (public news site)
        └─► digest.py          → docs/digests/      (weekly digest)
        ▼
 GitHub Pages serves everything

 Firebase Realtime DB = cross-device state:
   done/posted stories · published articles · repurpose captures &
   performance · write drafts & performance · synced settings
   (audience, personal note)

 Cloudflare Worker (optional) = the only place an API key exists.
 The Studio sends a prompt → Worker calls the model → returns text.
 The key never touches the browser, extension, or repo.
```

The default path needs no API at all: the Studio copies a prompt, you paste it into ChatGPT / Gemini / Claude, and paste the answer back.

---

## 4. The Studio, tab by tab

### 🏠 Home
Today's top pick (freshest high-scoring story), a ready-post widget, and quick stats.

### 📰 News / Popular
The scored, de-duplicated feed. Each story can open the **LinkedIn draft**, be published to the public website, or be marked done. Once a story (or any duplicate of it) is used, it's ticked on **every device**.

### in LinkedIn draft (per story)
The core workflow. One story → one post:

1. **Paste the facts** — a few lines from the article. No AI can open a link, so this is what the post is genuinely built from.
2. **Pick a mode** — **🧠 Insight** (one supported development and the specific professional implication) or **🛠️ Practical** (one action, decision checklist, evaluation question or tradeoff the source actually supports). Both copy a prompt.
3. **Paste the output back → Validate.** The `[[MARKER]]` response splits into the post, its sources, and **private review notes** that never leave the Studio (which sentence rests on which fact, what is interpretation, what needs approval).
4. **Copy post → Open LinkedIn → ✓ Mark as posted.**

If only a headline is supplied, the writer returns `needs_input` and says what it needs rather than inventing details. If there's no worthwhile angle for the audience it can return `skip` — no post is a valid outcome. Firsthand claims ("I tested this") appear only when a real personal note is supplied; otherwise the post stays an attributed explanation. No forced follow/like CTA, no mandatory hashtags or questions.

Audience and personal note are remembered in synced settings, so they're set once.

### ♻️ Repurpose
Capture a post you admire on X or LinkedIn (extension or paste) → the AI decides the smartest move (rewrite as your own, comment, question, hot take…) and writes original versions, with strict no-plagiarism rules. Has its own performance tracking.

### ✍️ Write
Short original posts from a seed idea: named presets, style profiles, one-click ⚡ generation via the optional Worker (or copy-paste), refine buttons, drafts synced across devices, and a performance dashboard. Still X-shaped in its formatting — a LinkedIn-native rewrite is the obvious next job.

### 💡 Inspire
A bank of proven content formats plus today's top news rewritten into useful angles. Every idea can go to ✍️ Write, the 🛠️ Practical prompt, or the LinkedIn draft.

### ⭐ Me
Personal-brand posters: the operator's own face presents the news. The face comes from a real photo — never AI-generated.

### 📈 Trends / Pulse / Research
Rising topic signals week-over-week; what people are using, searching and struggling with (Pulse, from Reddit / HN / YouTube / Google); and daily AI papers for learning. Pulse *reads* those platforms as signal sources — reading a platform is not publishing to it.

---

## 5. Content intelligence (what makes output good)

- **Evidence before style.** The writer is told it cannot open links and must never pretend otherwise. Every factual claim has to come from supplied material; a vendor's claim stays attributed to the vendor; timing is checked separately from when the story was collected, so an older piece is never framed as breaking. Missing evidence produces a question, not a guess.
- **Human voice engine** — rules that kill "AI-sounding" text: varied sentence rhythm, one idea per post, honest interpretation, banned AI phrases (game-changer, seamless, delve…) and banned sentence patterns ("It's not just X, it's Y").
- **No engagement bait.** No forced "follow me", no "repost ♻️", no "comment YES", no fake urgency. A question at the end is an editorial choice, only when an answer is actually wanted.
- **Design studio** — image prompts are generated by a virtual studio of **20 named designers** with distinct signatures, rotated in code per prompt across **13 poster formats** with mood-matched accent colors, so no two posters look alike.
- **Performance learning** — posted content can be scored and the dashboards show what works. Missing metrics are missing, not zero.

---

## 6. Security model

- **No API keys anywhere public.** Model keys live only in the Cloudflare Worker's encrypted environment; GitHub Actions secrets hold the NewsData key, the site passcode and the Firebase URL. The static site and extension contain zero secrets.
- The Studio's passcode is a **screen gate**: only the SHA-256 hash ships in the page, and unlocking derives the Firebase board address from the code. It controls what the *page* shows.
- ⚠️ **Known gap: the Firebase rules are permissive.** Reads and writes go directly to the Realtime DB unauthenticated, so the screen gate is not database authorization — anyone who learns a path can write to it. Owner-scoped auth with server-enforced rules is the outstanding security job on this project. Treat everything in Firebase as operator-visible convenience state, not private data.
- The browser extension captures **only on click** — no background scraping, no automation against platform rules, no auto-posting anywhere.
- The optional X Worker rejects unknown actions; a request with a missing action can no longer fall through into publishing.

---

## 7. Operating cost

| Item | Cost |
|---|---|
| Hosting, automation, database, extension | **$0** |
| Optional ⚡ generation via the Worker | ~**$0.005–0.02 per generation** |
| Default copy-paste mode into Claude/ChatGPT/Gemini | $0 |

---

## 8. 5-minute demo script

1. **Home** — today's top pick and quick stats.
2. **News → in LinkedIn draft** — pick a story, paste two sentences from the source, copy the **Insight** prompt, paste the AI's answer back, **Validate** → post + sources + private review notes.
3. **Show the guard rails** — clear the pasted facts and run it again: the writer answers `needs_input` and asks instead of inventing.
4. **Copy post → Open LinkedIn** — and point out that neither marks the story done; only ✓ does.
5. **🛠️ Practical mode** on the same story — a checklist or decision question instead of commentary.
6. **⭐ Me** — a personal-brand poster for the same headline.
7. **📈 Pulse / Trends** — where the next story ideas come from.
8. Finish on the **public website** — the audience-facing side, rebuilt hourly.

---

## 9. Repo map (for developers)

| Path | Purpose |
|---|---|
| `fetcher.py`, `filters.py`, `scoring.py`, `config.py`, `database.py` | hourly collection, filtering, de-dup, scoring, retention |
| `main.py`, `notifier.py`, `digest.py` | run loop, phone alerts, weekly digest |
| `generate_site.py` | builds the Studio (`docs/studio.html`) |
| `generate_public.py` | builds the public site (`docs/index.html`) |
| `docs/templates.js` | **ALL prompt engineering** — authored source; `docs/studio.html` is generated |
| `dump_prompts.js` | regenerates `PROMPTS.md` from `docs/templates.js` |
| `generate_pulse.py`, `collectors/`, `analyzer/` | the Pulse signal pipeline |
| `x-worker/` | optional Cloudflare Worker for X (draft or post; never on an unknown action) |
| `x-extension/` | Chrome extension (capture → Firebase, on click only) |
| `.github/workflows/` | fetch (hourly) · pulse (6 h) |
| `smoke_test.js`, `ui_test.js` | prompt-library checks · full UI walk-through in JSDOM |
| `PROMPTS.md` | generated, human-readable copy of every prompt |
| `XMINI_API.md`, `X-PIPELINE-SETUP.md`, `PULSE-SETUP.md` | setup guides |

---

*Last substantive update: September 2026 — the LinkedIn-first refactor. Retired in that pass: the multi-platform Newsroom, the Caira editor pipeline and its workflow, the publish board / create wizard / per-editor workspaces / team chat, the X Replies tab, and the Facebook / Instagram / TikTok / WhatsApp / YouTube output paths.*
