"""
AI News Radar - Weekly Digest Generator

Scans the last 7 days of stories already in the SQLite database, scores them
with PURE PYTHON RULES (no API, no LLM, $0), and writes a Markdown file with
headings + original source links — ready to paste into Claude for polishing.

This is ADDITIVE: it only reads the database, never fetches or changes anything.

Run on demand:   python digest.py
In code:         from digest import generate_weekly_digest
                 generate_weekly_digest("news.db", "docs/digests")
"""

import html as _htmlmod
import json
import os
import re
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone


def _e(s):
    return _htmlmod.escape(str(s or ""))


def _alink(url, text):
    return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (
        _htmlmod.escape(str(url or ""), quote=True), _e(text))


def _html_doc(title, body):
    """Wrap the digest body in a clean, print-to-PDF page (Save as PDF button)."""
    return """<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>""" + _e(title) + """</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
  :root{--ink:#0f172a;--dim:#5f6671;--line:#e5e7eb;--accent:#16a34a;}
  *{box-sizing:border-box;}
  body{max-width:760px;margin:0 auto;padding:34px 22px 70px;color:var(--ink);
       font:15px/1.6 Inter,system-ui,sans-serif;-webkit-font-smoothing:antialiased;}
  h1{font-size:26px;font-weight:800;letter-spacing:-.02em;margin:0 0 4px;}
  h2{font-size:18px;font-weight:700;margin:30px 0 12px;padding-bottom:6px;
     border-bottom:2px solid var(--line);}
  .sub{color:var(--dim);font-size:13px;margin-bottom:18px;}
  .big{background:#f6faf7;border:1px solid #d7ead9;border-radius:12px;padding:16px 18px;}
  .big .t{font-size:17px;font-weight:700;margin-bottom:6px;}
  ol,ul{padding-left:22px;} li{margin-bottom:11px;}
  .meta{color:var(--dim);font-size:13px;}
  a{color:var(--accent);text-decoration:none;} a:hover{text-decoration:underline;}
  .nums li{margin-bottom:5px;}
  .foot{margin-top:34px;color:var(--dim);font-size:12px;border-top:1px solid var(--line);padding-top:12px;}
  .bar{position:sticky;top:0;background:#fff;padding:12px 0;margin:-34px 0 8px;
       display:flex;gap:10px;align-items:center;border-bottom:1px solid var(--line);}
  .btn{background:var(--accent);color:#fff;border:none;padding:10px 18px;border-radius:9px;
       font:600 14px Inter;cursor:pointer;}
  .ghost{background:#fff;color:var(--ink);border:1px solid var(--line);padding:10px 16px;
         border-radius:9px;font:600 13px Inter;text-decoration:none;}
  @media print{.bar{display:none;} body{padding:0;} a{color:var(--ink);}}
</style></head><body>
<div class="bar noprint">
  <button class="btn" onclick="window.print()">📄 Save as PDF</button>
  <a class="ghost" href="latest.md" download>⬇ Markdown (for Claude)</a>
</div>
""" + body + """
</body></html>"""

try:
    import config
    CATEGORIES = config.CATEGORIES
except Exception:  # standalone fallback
    CATEGORIES = {1: "New Tools & Models", 2: "AI in Coding", 3: "Leaders & Podcasts",
                  4: "AI & the Future", 5: "AI in Defense", 6: "AI in Space",
                  7: "AI in Agriculture", 8: "AI in Health & Science",
                  9: "Research Papers", 10: "AI General News"}

SCIENCE_CATEGORY = 8          # "AI in Health & Science" (spec calls it "AI in Science")
DAYS = 7

# ============================================================================
#  TUNABLE CONFIG — edit these weights / keyword lists, no logic digging needed
# ============================================================================

# Signal A — source coverage (highest weight): points per distinct source
COVERAGE_POINTS = 10

# Signal B — human engagement (Reddit / HN), capped so one viral post can't win
ENGAGEMENT_CAP = 50
ENGAGEMENT_SOURCES_HINT = ("reddit", "hacker news", "hn")   # source-name contains

# Signal C — "real story / real people" boost
HUMAN_BOOST = 15
HUMAN_KEYWORDS = [
    "used ai to", "built with ai", "ai helped", "scientists", "researchers",
    "discovered", "world's first", "first time", "student", "doctor", "farmer",
    "patient", "saved", "cure", "breakthrough",
]

# Signal D — source authority (matched against the source name AND the outlet
# in a Google/Bing title tail like "... - TechCrunch")
AUTHORITY_OFFICIAL = 10
AUTHORITY_TOPTIER = 7
AUTHORITY_DEFAULT = 3
OFFICIAL_SOURCES = ["openai", "anthropic", "deepmind", "google ai", "meta ai",
                    "mistral", "nvidia", "microsoft ai", "hugging face", "xai"]
TOPTIER_SOURCES = ["techcrunch", "the verge", "verge", "nature", "science",
                   "mit", "reuters", "financial times", " ft", "wsj",
                   "wall street journal", "wired", "bloomberg"]

# Signal E — keyword heat
HEAT_WORDS = ["launch", "launched", "released", "unveils", "announces",
              "breakthrough", "first-ever", "sues", "lawsuit", "banned",
              "shuts down", "acquires"]
HEAT_POINTS = 5
HEAT_CAP = 15
SOFT_WORDS = ["rumor", "might", "could", "reportedly", "leak"]
SOFT_PENALTY = -3

# Signal F — freshness (last 2 days of the window)
FRESH_DAYS = 2
FRESH_POINTS = 3

# Interesting-Uses bucket thresholds
INTERESTING_MIN_UPVOTES = 100
INTERESTING_MIN_COMMENTS = 20

# Most-active-topic stopwords (so the result is meaningful)
STOPWORDS = set("""
the a an and or of to in on for with by from as at is are was were be been being
this that these those it its their your you we they he she his her our new ai a.i
how why what when who will can could should would may might just more most best top
big says say said get gets got make makes made use uses used using s vs about over
into out up down after before now today week year amid no not but if then than
""".split())

# ============================================================================


def _norm_title(title):
    """Lowercase, drop the ' - Outlet' tail Google/Bing News appends."""
    t = re.sub(r"\s+[-|]\s+[^-|]+$", "", title or "")
    return t.lower()


def _outlet_tail(title):
    m = re.search(r"\s[-|]\s([^-|]+)$", title or "")
    return m.group(1).strip().lower() if m else ""


def _authority(source, title):
    hay = (source or "").lower() + " " + _outlet_tail(title)
    if any(s in hay for s in OFFICIAL_SOURCES):
        return AUTHORITY_OFFICIAL
    if any(s in hay for s in TOPTIER_SOURCES):
        return AUTHORITY_TOPTIER
    return AUTHORITY_DEFAULT


def _is_engagement_source(source):
    s = (source or "").lower()
    return any(h in s for h in ENGAGEMENT_SOURCES_HINT)


def _parse_dt(s):
    try:
        d = datetime.fromisoformat(s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _score(item, now):
    """Return (total, signals_dict) for one story row."""
    title = item["title"] or ""
    low = title.lower()
    links = []
    try:
        links = json.loads(item["links"] or "[]")
    except Exception:
        links = []

    sig = {}
    # A — source coverage
    n_sources = 1 + len(links)
    sig["coverage"] = n_sources * COVERAGE_POINTS
    item_n_sources = n_sources

    # B — human engagement (Reddit/HN)
    eng = 0
    if _is_engagement_source(item["source"]):
        up = item["upvotes"] or 0
        com = item["comments"] or 0
        eng = min(ENGAGEMENT_CAP, (up / 100.0) + (com / 20.0))
    sig["engagement"] = eng

    # C — real-story boost
    sig["human"] = HUMAN_BOOST if any(k in low for k in HUMAN_KEYWORDS) else 0

    # D — authority
    sig["authority"] = _authority(item["source"], title)

    # E — keyword heat
    heat = min(HEAT_CAP, HEAT_POINTS * sum(1 for w in HEAT_WORDS if w in low))
    heat += SOFT_PENALTY * sum(1 for w in SOFT_WORDS if w in low)
    sig["heat"] = heat

    # F — freshness
    when = _parse_dt(item["published"]) or _parse_dt(item["fetched"])
    fresh = FRESH_POINTS if (when and (now - when) <= timedelta(days=FRESH_DAYS)) else 0
    sig["fresh"] = fresh

    total = sum(sig.values())
    return round(total, 1), sig, item_n_sources, links


def _best_link(item, links):
    """Pick the highest-authority link among the story and its coverage."""
    cands = [(item["source"], item["url"])] + [(l.get("source", ""), l.get("url", "")) for l in links]
    cands = [(s, u) for s, u in cands if u]
    if not cands:
        return item["url"]
    cands.sort(key=lambda su: _authority(su[0], ""), reverse=True)
    return cands[0][1]


def _md_link(url):
    return url or ""


def generate_weekly_digest(db_path="news.db", output_dir="docs/digests", archive=True):
    """Writes docs/digests/latest.md always (the dashboard button downloads this).
    Writes a permanent dated copy only when archive=True (the Sunday weekly run /
    manual runs) so the folder doesn't fill with one file per fetch cycle."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=DAYS)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(items)")}
    up_sel = "upvotes" if "upvotes" in cols else "0 AS upvotes"
    com_sel = "comments" if "comments" in cols else "0 AS comments"
    rows = conn.execute(
        f"SELECT id, title, url, links, source, pillar, published, fetched, "
        f"{up_sel}, {com_sel} FROM items WHERE fetched >= ?",
        (cutoff.isoformat(),)
    ).fetchall()
    conn.close()

    scored = []
    for r in rows:
        total, sig, n_sources, links = _score(r, now)
        scored.append({"row": r, "total": total, "sig": sig,
                       "n_sources": n_sources, "links": links})
    scored.sort(key=lambda x: x["total"], reverse=True)

    top10 = scored[:10]
    top10_urls = {s["row"]["url"] for s in top10}

    # Interesting Uses: human-keyword AND (engaged Reddit/HN OR science source)
    interesting = []
    for s in scored:
        r = s["row"]
        low = (r["title"] or "").lower()
        if not any(k in low for k in HUMAN_KEYWORDS):
            continue
        engaged = _is_engagement_source(r["source"]) and \
            ((r["upvotes"] or 0) >= INTERESTING_MIN_UPVOTES or
             (r["comments"] or 0) >= INTERESTING_MIN_COMMENTS)
        is_science = r["pillar"] == SCIENCE_CATEGORY
        if (engaged or is_science) and r["url"] not in top10_urls:
            interesting.append(s)
        if len(interesting) >= 8:
            break

    science = [s for s in scored if s["row"]["pillar"] == SCIENCE_CATEGORY][:5]

    # Trend stats
    total_stories = len(rows)
    words = Counter()
    for r in rows:
        for w in re.findall(r"[a-zA-Z][a-zA-Z0-9'+-]{2,}", _norm_title(r["title"])):
            wl = w.lower()
            if wl not in STOPWORDS and len(wl) > 2:
                words[wl] += 1
    most_topic = words.most_common(1)[0][0] if words else "—"
    cat_counter = Counter(r["pillar"] for r in rows)
    busiest_cat = (CATEGORIES.get(cat_counter.most_common(1)[0][0], "—")
                   if cat_counter else "—")

    # ---- build the markdown ----
    start_s = cutoff.strftime("%d %b %Y")
    end_s = now.strftime("%d %b %Y")
    out = []
    out.append(f"# 🗞️ AI THIS WEEK — {start_s} to {end_s}\n")

    if top10:
        big = top10[0]
        r = big["row"]
        cov = [_md_link(l.get("url", "")) for l in big["links"] if l.get("url")]
        out.append("## 🔥 Biggest Story of the Week")
        out.append(f"**{r['title']}**")
        out.append(f"Covered by {big['n_sources']} source(s) · Score: {big['total']}")
        out.append(f"Best source link: {_best_link(r, big['links'])}")
        if cov:
            out.append("All coverage: " + " · ".join([r["url"]] + cov))
        else:
            out.append(f"Link: {r['url']}")
        out.append("")
    else:
        out.append("## 🔥 Biggest Story of the Week")
        out.append("_No stories tracked this week yet._\n")

    out.append("## 🤯 Most Interesting / Real-World AI Uses")
    if interesting:
        for i, s in enumerate(interesting, 1):
            r = s["row"]
            note = ""
            if _is_engagement_source(r["source"]) and (r["upvotes"] or 0):
                note = f' — {r["upvotes"]:,} upvotes on Reddit/HN'
            elif r["pillar"] == SCIENCE_CATEGORY:
                note = " — science angle"
            out.append(f"{i}. **{r['title']}**{note}")
            out.append(f"   {r['url']}")
    else:
        out.append("_Nothing matched the real-world filter this week._")
    out.append("")

    out.append("## 📊 Top 10 Stories This Week (ranked)")
    if top10:
        for i, s in enumerate(top10, 1):
            r = s["row"]
            out.append(f"{i}. **{r['title']}** — {r['source']} — Score {s['total']}")
            out.append(f"   {r['url']}")
    else:
        out.append("_No stories this week._")
    out.append("")

    out.append("## 🧪 AI in Science Highlights")
    if science:
        for s in science:
            r = s["row"]
            out.append(f"- **{r['title']}** — {r['url']}")
    else:
        out.append("_No science stories this week._")
    out.append("")

    out.append("## 📈 This Week in Numbers")
    out.append(f"- Total stories tracked: {total_stories}")
    out.append(f"- Most active topic: {most_topic}")
    out.append(f"- Busiest category: {busiest_cat}")
    out.append("")
    out.append("---")
    out.append("*Auto-generated by AI News Radar. Source links are original. "
               "Ready for editorial polish.*")

    md = "\n".join(out) + "\n"

    # ---- build the HTML / PDF version from the same data ----
    H = []
    H.append(f"<h1>🗞️ AI This Week</h1><div class='sub'>{start_s} to {end_s}</div>")
    if top10:
        big = top10[0]
        r = big["row"]
        H.append("<h2>🔥 Biggest Story of the Week</h2>")
        H.append("<div class='big'><div class='t'>" + _e(r["title"]) + "</div>")
        H.append(f"<div class='meta'>Covered by {big['n_sources']} source(s) · Score {big['total']}</div>")
        H.append("<div style='margin-top:8px'>" + _alink(_best_link(r, big["links"]), "Open best source →") + "</div>")
        if big["links"]:
            extra = " · ".join(_alink(l.get("url", ""), "link " + str(i + 1))
                               for i, l in enumerate(big["links"]) if l.get("url"))
            H.append(f"<div class='meta' style='margin-top:6px'>All coverage: {extra}</div>")
        H.append("</div>")
    H.append("<h2>🤯 Most Interesting / Real-World AI Uses</h2>")
    if interesting:
        H.append("<ol>")
        for s in interesting:
            r = s["row"]
            note = ""
            if _is_engagement_source(r["source"]) and (r["upvotes"] or 0):
                note = f" <span class='meta'>— {r['upvotes']:,} upvotes</span>"
            elif r["pillar"] == SCIENCE_CATEGORY:
                note = " <span class='meta'>— science angle</span>"
            H.append("<li>" + _alink(r["url"], r["title"]) + note + "</li>")
        H.append("</ol>")
    else:
        H.append("<p class='meta'>Nothing matched the real-world filter this week.</p>")
    H.append("<h2>📊 Top 10 Stories This Week</h2>")
    if top10:
        H.append("<ol>")
        for s in top10:
            r = s["row"]
            H.append("<li>" + _alink(r["url"], r["title"]) +
                     f" <span class='meta'>— {_e(r['source'])} · Score {s['total']}</span></li>")
        H.append("</ol>")
    else:
        H.append("<p class='meta'>No stories this week.</p>")
    H.append("<h2>🧪 AI in Science Highlights</h2>")
    if science:
        H.append("<ul>")
        for s in science:
            H.append("<li>" + _alink(s["row"]["url"], s["row"]["title"]) + "</li>")
        H.append("</ul>")
    else:
        H.append("<p class='meta'>No science stories this week.</p>")
    H.append("<h2>📈 This Week in Numbers</h2><ul class='nums'>")
    H.append(f"<li>Total stories tracked: <b>{total_stories}</b></li>")
    H.append(f"<li>Most active topic: <b>{_e(most_topic)}</b></li>")
    H.append(f"<li>Busiest category: <b>{_e(busiest_cat)}</b></li></ul>")
    H.append("<div class='foot'>Auto-generated by AI News Radar. Source links are original. "
             "Ready for editorial polish.</div>")
    html_doc = _html_doc(f"AI Weekly Digest {now.strftime('%Y-%m-%d')}", "\n".join(H))

    os.makedirs(output_dir, exist_ok=True)
    # "latest" copies are what the dashboard buttons open — always refreshed
    with open(os.path.join(output_dir, "latest.md"), "w", encoding="utf-8") as f:
        f.write(md)
    with open(os.path.join(output_dir, "latest.html"), "w", encoding="utf-8") as f:
        f.write(html_doc)
    fpath = os.path.join(output_dir, "latest.html")
    if archive:
        stamp = now.strftime("%Y-%m-%d")
        with open(os.path.join(output_dir, f"AI-Weekly-Digest-{stamp}.md"), "w", encoding="utf-8") as f:
            f.write(md)
        fpath = os.path.join(output_dir, f"AI-Weekly-Digest-{stamp}.html")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(html_doc)
    print(f"Weekly digest written: {fpath} ({total_stories} stories this week)")
    return fpath


# TODO (future, OFF by default — do not enable without the user's say-so):
#   Optional Sunday step that sends ONLY the top-10 titles to Google Gemini's
#   free tier for a one-line "why this matters" per story (~10 calls/week,
#   inside the free quota). This is the ONLY place an LLM would ever enter the
#   app, and only when the user explicitly turns it on.


if __name__ == "__main__":
    generate_weekly_digest()
