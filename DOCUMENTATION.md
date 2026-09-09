# AI Radar Studio — Documentation

*An AI-powered newsroom + social-media content engine, built for the "AI x Ahmad" (@aixahmad) brand.*
*Runs on $0 infrastructure. One person can operate a full multi-platform content operation from it.*

---

## 1. What it is

AI Radar Studio automatically **collects AI news from 70+ sources every hour**, scores and de-duplicates it, and turns the best stories into **ready-to-publish content** for X (Twitter), LinkedIn, Instagram, Facebook, TikTok, WhatsApp and YouTube — articles, human-sounding posts, replies, carousels and designed poster images — while **learning from real engagement data** which content grows the account.

Everything is human-approved: the AI drafts, the operator reviews and posts. Nothing auto-posts.

---

## 2. Where it is deployed

| Piece | Where | URL / location | Cost |
|---|---|---|---|
| **Studio (the app)** | GitHub Pages | https://ahmad19sep.github.io/ai-news-updater/studio.html | $0 |
| **Public news website** | GitHub Pages | https://ahmad19sep.github.io/ai-news-updater/ | $0 |
| **Data & sync** | Firebase Realtime DB | `aixahmad-studio-default-rtdb.asia-southeast1` | $0 (free tier) |
| **AI generation API** | Cloudflare Worker | `x-writer.ahmadwork665.workers.dev` (holds the Anthropic key server-side) | $0 host + ~$0.01/generation |
| **Automation (crons)** | GitHub Actions | hourly news fetch · Caira pull · 6-hourly Pulse | $0 |
| **Browser extension** | Chrome (unpacked) | `x-extension/` folder in the repo | $0 |
| **Editor workflow (Caira)** | Vercel (separate app) | videoflow-sigma.vercel.app | external |

**How deployment works:** the website is 100% static. A Python generator (`generate_site.py` / `generate_public.py`) builds HTML into the repo's **`docs/` folder**; every push to `main` makes GitHub Pages rebuild and serve it automatically (~1 minute). No servers to maintain.

**How to verify it's live:** open the URLs above, or GitHub repo → **Settings → Pages** ("Your site is live at…"), or the **Actions** tab → "pages build and deployment" (green check = deployed).

---

## 3. Architecture (the big picture)

```
70+ RSS feeds + NewsData.io + HuggingFace papers
        │  (GitHub Action, hourly)
        ▼
 fetcher.py → SQLite (news.db) → scoring, de-dup, 7-day purge
        │
        ├─► generate_site.py  → docs/studio.html   (the Studio app)
        ├─► generate_public.py→ docs/index.html    (public news site)
        │
        ├─► caira.py: stories with score ≥ 10 auto-dispatch to Caira
        │   (load-balanced to the editor with fewest open tasks);
        │   approved work returns to the Studio's "Ready to Post"
        ▼
 GitHub Pages serves everything

 Firebase Realtime DB = cross-device state:
   done/posted stories · published articles · X reply captures &
   performance · repurpose captures & performance · write drafts &
   performance · Caira queue · ready-to-post

 Cloudflare Worker = the only place the Anthropic API key exists.
 The Studio sends a prompt → Worker calls Claude (Sonnet) → returns text.
 The key never touches the browser, extension, or repo.
```

---

## 4. The Studio, tab by tab

### 🏠 Home
Today's top pick (freshest high-scoring story), **"Post on X today"** widget (3 ready text posts, rotated daily, one-click post), and quick stats.

### 📰 News / Popular
The scored, de-duplicated feed. Each story: publish to the website, open the **Newsroom**, or mark done. Once a story (or any duplicate of it) is used anywhere, it's ticked done **on every device**.

### 🗞 Newsroom (per story)
One **master prompt** → paste into Claude/ChatGPT → paste the output back → **Parse** auto-splits it into: headline, 500-700-word article, 2 designed image prompts, and platform-native posts for LinkedIn / X / Reddit / Facebook / Instagram / WhatsApp / YouTube — each with a copy-&-open button. Publishing pushes the article to the public website and links all social posts to it.
Also: **💎 Value post** — turns news into *useful* content (how-to steps, tips carousel, infographic + captions for every platform), the highest-reach format.

### ✅ Ready to Post
Approved work arriving from **Caira** (the editor app on Vercel). Two-way flow: high-scoring stories are auto-assigned to whichever editor has the fewest open tasks; finished, approved posts appear here with per-platform post buttons.

### ↩️ X Replies
Capture any X post (browser extension or paste on mobile) → **⚡ one click** generates the 2 best replies via the API (the AI first classifies the post — question/news/hot-take/joke — and answers accordingly). Used replies are logged and scored so the dashboard learns **which reply styles grow the account**.

### ♻️ Repurpose
Capture a post you admire on X or LinkedIn → the AI decides the smartest move (rewrite as your own, comment, question, hot take…) and writes original X + LinkedIn + comment versions — with strict no-plagiarism rules. Includes image capture, own-brand poster maker, and its own performance tracking.

### ✍️ Write (Anthropic Write Engine)
Short, original text posts that grow an X account. 15 named presets (Ask a Real Question, Hot Take, Builder Thought, Anti-Hype Check…), 7 style profiles (Ahmad Natural, Funny Dev, Sharp Hot Take…), one-click ⚡ generation, refine buttons (Funnier / Sharper / Simpler / To question), quality + copy-risk badges, drafts synced across devices, and a performance dashboard with "what to post next" suggestions.

### 💡 Inspire
A curated bank of 26 proven, useful content formats (interactive posts, save-worthy lists, prompt-of-the-day, money angles, explainers) **plus** today's top news auto-rewritten into useful angles ("new model → 5 things you can do with it"). Every idea: ✍️ Write it, 💎 make a value pack, or 📰 open the Newsroom.

### ⭐ Me
Personal-brand posters: **the operator's own face presents the news** (news-anchor style). Reaction pose auto-matches the story mood (shocked for leaks, pointing for launches…). Face is taken from the operator's real photo — never AI-generated.

### 📈 Trends / Pulse / Research
Rising topic signals week-over-week, what people are using/searching (Pulse), and daily AI papers for learning.

---

## 5. Content intelligence (what makes output good)

- **Human voice engine** — every prompt enforces 20+ rules that kill "AI-sounding" text: varied sentence rhythm, one idea per post, personal opinion ("my take…"), banned AI phrases (game-changer, seamless, delve…), banned AI sentence patterns, per-platform audience voices (X = builders scrolling fast; Facebook = explain to a friend; LinkedIn = professionals, no corporate speak).
- **X algorithm awareness** — X posts are text-only (links are suppressed by X); the article link goes in the **first reply** via a dedicated 🧵 button.
- **Design studio** — image prompts are generated by a virtual studio of **20 named designers** with distinct signatures (Swiss minimalist, tabloid, cinematic, brutalist, data-first…), rotated **in code** per prompt, across **13 poster formats** (marker-highlight, breaking strip, VS card, big-number, cutout viral card, then-vs-now…) with mood-matched accent colors. Result: no two posters look alike.
- **Performance learning** — every posted reply/post can be scored (likes, replies ×3, reposts ×4, bookmarks ×5, profile clicks ×6, follows ×10). Dashboards show the best styles, presets, posting times, emoji impact, and top-20 posts, and recommend what to post more of.

---

## 6. Security model

- **No API keys anywhere public.** The Anthropic key lives only in the Cloudflare Worker's encrypted environment; GitHub Actions secrets hold the Caira/NewsData keys. The static site and extension contain zero secrets.
- The Firebase URL is public by design (public-rules realtime DB for a single-operator tool); all writes are operator-initiated.
- The browser extension captures **only on click** — no background scraping, no automation against X's rules, no auto-posting anywhere.

---

## 7. Operating cost

| Item | Cost |
|---|---|
| Hosting, automation, database, extension | **$0** |
| AI generation (⚡ buttons, Claude Sonnet via Worker) | ~**$0.005–0.02 per generation** (a few dollars/month at heavy use) |
| Optional: copy-paste mode into Claude/ChatGPT apps | $0 |

---

## 8. 5-minute demo script

1. **Home** — show today's top pick + the 3 ready "Post on X today" posts (one-click to X).
2. **News → Newsroom** — pick a story, copy master prompt → paste AI output → **Parse** → show article + every platform's post + 2 designed image prompts → platform buttons.
3. **💎 Value post** — same story as a how-to/infographic pack (slides + captions + image prompt).
4. **✍️ Write** — type an idea, press **⚡ Generate**, show Best + backup with quality badges, press "🔥 To hot take".
5. **↩️ X Replies** — paste any tweet, **⚡ Reply**, show the 2 tailored replies.
6. **⭐ Me** — "Poster with me" on a headline (personal-brand news card).
7. **📊 Performance** — show the learning loop (best styles, suggestions).
8. Finish on the **public website** — the audience-facing side, auto-updated hourly.

---

## 9. Repo map (for developers)

| Path | Purpose |
|---|---|
| `fetcher.py`, `config.py`, `database.py` | hourly news collection, scoring, retention |
| `generate_site.py` | builds the Studio (docs/studio.html) |
| `generate_public.py` | builds the public site (docs/index.html) |
| `docs/templates.js` | ALL prompt engineering (voice rules, engines, design studio) |
| `caira.py` + `CAIRA_INTEGRATION.md` | two-way editor-app integration |
| `x-extension/` | Chrome extension (capture → Firebase) |
| `.github/workflows/` | fetch (hourly) · caira-pull (5 min) · pulse (6 h) |
| `PROMPTS.md` | human-readable copy of every prompt |
| `XMINI_API.md` | Cloudflare Worker setup guide |
