# AI Pulse — setup & "your part"

**Pulse** is a new studio tab that shows what people are actually **using, searching,
and struggling with** in AI right now (not news headlines), and turns each signal into
a content idea for AI x Ahmad. It is separate from the News/Trends tabs.

It runs **server-side** in a GitHub Action and writes `docs/pulse.json`; the studio tab
only reads that file. **No API key ever touches the website.**

---

## ✅ It already works — $0, no keys
Out of the box Pulse uses **Reddit + Hacker News** (no keys needed) in **raw mode**
(`PULSE_USE_LLM = False`). You get: hot trends, rising tools, and "problems people face,"
each linking to the real source. The **AI x Ahmad** action runs it **every 6 hours**.

Nothing required from you to get this. 🎉

---

## 🔼 Optional upgrades (only if you want more)

Add these in **GitHub → repo → Settings → Secrets and variables → Actions → New repository secret**
(same place your other secrets live). Each is optional; a missing one is just skipped.

### 1. Richer cards (named trends + Urdu content ideas + angles) — **recommended, free**
This turns on **LLM mode**.
1. Get a **free** Groq key: <https://console.groq.com> → API Keys.
2. Add secret **`GROQ_API_KEY`** = your key.
3. In [config.py](config.py) set **`PULSE_USE_LLM = True`** and commit.

Now each cycle the model clusters the signals into clean named trends with a
"what this means for YOU" angle, a LinkedIn angle, and ready Urdu video ideas.
*(If the key is ever missing/broken, it auto-falls back to raw mode — never fails.)*

### 2. Real YouTube signal — free
1. Google Cloud Console → enable **YouTube Data API v3** → create an API key.
2. Add secret **`YOUTUBE_API_KEY`** = your key.

Without it, Pulse still uses YouTube **autocomplete** (what people search); with it,
you also get recent high-view AI videos per topic.

### 3. Higher-quality synthesis (paid, optional)
Add **`ANTHROPIC_API_KEY`** and set `PULSE_LLM_PROVIDER = "anthropic"` in config.
Better writing than Groq, but costs money. Groq is plenty to start.

### 4. Google Trends (best-effort, off by default)
`pytrends` is unofficial and usually **blocked from GitHub's servers**, so it's left off.
To try it: `pip install -r requirements-pulse.txt` locally, or add that install line to
[.github/workflows/pulse.yml](.github/workflows/pulse.yml). Expect it to often return nothing on the cloud.

---

## ▶️ Running it
- **Automatic:** the **AI Pulse** workflow runs every 6 hours.
- **Manual:** GitHub → **Actions → "AI Pulse" → Run workflow**.
- **Locally:** `python generate_pulse.py` → writes `docs/pulse.json`.

## Honest limitations
- **Reddit/HN** are the reliable free signals; **YouTube** needs a key; **Google Trends** is best-effort.
- **Instagram / Facebook / LinkedIn** have no free, ToS-compliant trend API — those items are
  **inferred** from cross-platform signals and clearly labelled "inferred," never faked.
- **Raw mode** cards are leaner (no AI angles/ideas) by design — flip on `PULSE_USE_LLM` for the rich version.
- **Momentum** (rising/hot/cooling) needs a few days of history to be meaningful — early on, most show "rising."
