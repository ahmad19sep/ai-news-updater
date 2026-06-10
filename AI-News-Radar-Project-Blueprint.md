# AI News Radar — Project Blueprint

**Owner:** You
**Goal:** A tool that watches the entire AI world 24/7 and brings every important story — with its original source link — to your phone and dashboard, so you can read it and make videos in Urdu, Hindi, and English faster than anyone else.

**What it does NOT do:** It does not write content, scripts, or summaries. It fetches, organizes, and delivers. The reading, judgment, and creativity stay with you.

---

## 1. The Problem

To run the best AI news channel, you would need to sit 24 hours a day watching dozens of websites, blogs, Reddit threads, and podcasts. That is impossible. This tool becomes your eyes — it never sleeps, never misses a source, and hands you everything in one organized place.

## 2. The Solution in One Line

**Fetch → Clean → Store → Deliver.** Every hour, the tool checks all sources, removes junk and duplicates, saves everything in a database, and delivers it to your phone (ntfy.sh push notifications) and a web dashboard.

## 3. The Five Content Pillars

Every news item is sorted into one of five categories. These are also your video categories.

**Pillar 1 — Product & Model Updates.** New models, tools, and features from AI companies. Sources: official blogs of OpenAI, Anthropic, Google DeepMind, Meta AI, Mistral, xAI, Microsoft AI, Hugging Face.

**Pillar 2 — AI in Science.** AI used in biology, medicine, space, physics, climate. Sources: Nature, Science Magazine, ScienceDaily, NASA news, MIT News.

**Pillar 3 — Leaders & Voices.** What AI leaders (Sam Altman, Dario Amodei, Demis Hassabis, Jensen Huang, Satya Nadella, Elon Musk and others) say in interviews, podcasts, and keynotes — including their advice on using AI effectively. Sources: Google News queries per leader + YouTube RSS feeds of key podcast channels.

**Pillar 4 — Interesting Uses.** Real people doing creative and unusual things with AI. Sources: Reddit (r/ChatGPT, r/LocalLLaMA, r/artificial), Hacker News, Google News "using AI to" queries.

**Pillar 5 — Research Breakthroughs.** Important new papers, filtered to only the ones getting real attention. Sources: Hugging Face trending papers, arXiv (filtered).

## 4. How It Works (The Pipeline)

**Step 1 — Fetch (every 60 minutes).** The tool visits every source through free RSS feeds and public APIs. No paid services needed.

**Step 2 — Clean.** A keyword filter removes non-AI junk. A duplicate detector finds the same story covered by multiple sites and groups them into ONE story card with ALL source links attached — more angles for your videos.

**Step 3 — Store.** Every item is saved in a small local database (SQLite) with title, link, source, category, and time. This prevents re-sending the same news and slowly becomes your personal searchable AI news archive — later useful for your RAG learning projects.

**Step 4 — Deliver, two channels:**

*ntfy.sh push notifications (two levels)* — chosen because Telegram is blocked in Pakistan; ntfy is free, unblocked, and needs no account.
- Instant alert — only for Pillar 1 official lab announcements (roughly 1–3 per day). These are your "be first in Urdu" moments.
- Digest — all other items collected and sent 3 times daily (morning, afternoon, night), grouped by pillar.
- Setup: install the ntfy app on your phone and subscribe to a private random topic name. Done.

*Web Dashboard:*
- All items, newest first
- Each card: headline, source name, "2 hours ago" timestamp, original link(s)
- Filter buttons by pillar + a search box
- A "done" mark for stories you have already covered

## 5. Technology

| Part | Tool | Cost |
|------|------|------|
| Language | Python | Free |
| Feed reading | feedparser + requests | Free |
| Database | SQLite (one file, no server) | Free |
| Dashboard | Flask web app | Free |
| Alerts | ntfy.sh push notifications | Free |
| Scheduling | Python scheduler (runs every hour) | Free |
| Hosting | Your PC first; free cloud later | Free |

**Total running cost: $0/month.**

## 6. Known Limitations (Accepted Honestly)

1. **Importance judgment stays human.** The tool fetches 40–80 items/day; choosing what is video-worthy is your editorial skill — that is what makes the channel yours.
2. **Leader content arrives as links, not transcripts.** You get the headline and link to the interview/podcast; watching it is your job (version 1).
3. **"How people use it differently" arrives with natural delay.** Usage analysis appears on Reddit and in articles 1–3 days after a launch; the tool catches it under Pillar 4.
4. **Paywalled sites** (Bloomberg, The Information) deliver only the headline.
5. **Twitter/X** has no free API; but major news reaches blogs, Reddit, and Hacker News within minutes, so almost nothing is lost.
6. **Filters need tuning.** Expect 1–2 weeks of adjusting keywords until junk disappears.
7. **The PC must stay on**, or we deploy to a free cloud host as a later step.

## 7. Build Plan

- **Phase 1:** Fetcher + database + keyword filter. Test that news flows in correctly.
- **Phase 2:** ntfy.sh notifications — instant alerts + digests.
- **Phase 3:** Web dashboard with filters and search.
- **Phase 4:** Tune filters and duplicate detection for 1–2 weeks of real use.
- **Later (version 2):** importance ranking, podcast transcripts, cloud deployment, and optional LLM summaries when you are ready.

## 8. Success Definition

You open your phone notifications in the morning and within 5 minutes you know everything important that happened in AI worldwide — with original links ready. You pick a story, make a video, and publish before anyone else covers it in Urdu or Hindi.
