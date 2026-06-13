# X Auto-Post Pipeline — Setup Guide

Goal: pick a news story + template → an AI writes the X post/thread (grounded in the
real article, so it's always up to date) → it's posted to your X account.
A tiny **Cloudflare Worker** holds all the keys safely; the website never sees them.

Cost: **$0/month** (X free tier + Cloudflare free tier + a free/cheap writer key).

Do these once. Takes ~30–60 min. The X Developer step is the slow one — start it first.

---

## 1. X Developer account + keys (start this first — approval can take a bit)

1. Go to **https://developer.x.com** → sign in with your @aixahmad account → **Sign up** for the
   Free tier.
2. Create a **Project** and an **App** inside it (any name, e.g. "AI x Ahmad poster").
3. In the App's **Settings → User authentication settings → Set up**:
   - App permissions: **Read and write**
   - Type of App: **Web App / Automated App or Bot**
   - Callback URL: `https://ahmad19sep.github.io/ai-news-updater/` (any valid URL is fine)
   - Website URL: same
   - Save.
4. Go to **Keys and tokens** tab. Copy these **four** values (you'll paste them into Cloudflare):
   - **API Key**  (consumer key)
   - **API Key Secret**  (consumer secret)
   - **Access Token**
   - **Access Token Secret**
   (Generate the Access Token + Secret with **Read and Write** permission. If you set
   permissions AFTER generating, regenerate the token so it has write access.)

## 2. The writer (pick ONE)

- **Cloudflare Workers AI (recommended — free, NO key needed):** runs right inside your
  Worker. Just set `WRITER=cloudflare` and add an **AI binding** (see step 3.5 below).
  Free daily allowance, no extra account.
- **Groq (free, fast):** https://console.groq.com → API key. Set `WRITER=groq`, `WRITER_KEY=<key>`.
- **Gemini (free tier, has daily limits):** https://aistudio.google.com → Get API key. `WRITER=gemini`.
- **Claude / OpenAI:** paid keys (~cents/month). `WRITER=anthropic` or `openai`.

## 3.5 If using Cloudflare Workers AI (recommended)
In your Worker → **Settings → Bindings → Add → Workers AI** → set the **Variable name** to
exactly **`AI`** → Save → Deploy. Then set the secret **`WRITER=cloudflare`** (no WRITER_KEY needed).

## 3. Cloudflare Worker (the safe key-holder)

1. Make a free account at **https://dash.cloudflare.com** → **Workers & Pages** → **Create** →
   **Create Worker** → name it (e.g. `aix-x`) → **Deploy** (the default code is fine for now).
2. Open the Worker → **Edit code** → delete everything → paste the contents of
   **`x-worker/worker.js`** from this repo → **Deploy**.
3. Open the Worker → **Settings → Variables and Secrets** → add these (as **Secret**):
   | Name | Value |
   |------|-------|
   | `APP_TOKEN` | make up a long random password (you'll paste the SAME one in the app) |
   | `WRITER` | `gemini` or `anthropic` or `openai` |
   | `WRITER_KEY` | the key from step 2 |
   | `X_API_KEY` | from step 1 |
   | `X_API_SECRET` | from step 1 |
   | `X_ACCESS_TOKEN` | from step 1 |
   | `X_ACCESS_SECRET` | from step 1 |
   Save, then **Deploy** again.
4. Copy your Worker URL (looks like `https://aix-x.<your-name>.workers.dev`).

## 4. Connect it in the app

In the studio (owner device), open the X pipeline settings (the 🚀 button / setup field)
and paste:
- your **Worker URL**
- the **same `APP_TOKEN`** you set in Cloudflare

That's it. Now picking a story → template → 🚀 writes and (after your approval, or
automatically if you flip the toggle) posts to X.

---

## Notes
- **Threads use more quota.** The X free tier allows a few hundred to ~1,500 posts/month;
  a 6-tweet thread = 6 posts. The app shows a monthly counter so you never get surprised.
- **Safety:** default mode is **Approve first** — you see the thread before it posts. Flip
  to full-auto only once you trust it.
- The `APP_TOKEN` keeps random people from calling your Worker. Keep it private; it lives
  only in Cloudflare and on your owner device, never in the public page.
