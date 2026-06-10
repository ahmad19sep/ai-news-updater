"""
AI News Radar - Static site generator (online dashboard)

Reads news.db and writes docs/index.html - a single-page dashboard
published free on GitHub Pages. The cloud server regenerates it every
hour after fetching news.

Run manually:  python generate_site.py
"""

import json
import os
from datetime import datetime, timezone

import config
import database
import scoring

MAX_STORIES = 1200  # keep the page fast on phones
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI News Radar</title>
<style>
  :root { --bg:#0f1217; --card:#171c24; --text:#e8eaed; --dim:#9aa3af;
          --accent:#4f9cff; --border:#262d38; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
         font:15px/1.5 system-ui, "Segoe UI", sans-serif; }
  .wrap { max-width:880px; margin:0 auto; padding:18px 14px 60px; }
  h1 { font-size:22px; margin:6px 0 4px; } h1 .dot { color:var(--accent); }
  .updated { color:var(--dim); font-size:12.5px; margin-bottom:14px; }
  .bar { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:14px; }
  .bar button { background:var(--card); color:var(--text);
      border:1px solid var(--border); padding:6px 12px; border-radius:18px;
      font-size:13px; cursor:pointer; }
  .bar button.active { background:var(--accent); border-color:var(--accent); color:#fff; }
  .search { display:flex; gap:8px; margin-bottom:6px; }
  .search input { flex:1; background:var(--card); border:1px solid var(--border);
      color:var(--text); padding:9px 14px; border-radius:8px; font-size:14px; }
  .count { color:var(--dim); font-size:13px; margin:8px 0 12px; }
  .card { background:var(--card); border:1px solid var(--border);
      border-radius:10px; padding:14px 16px; margin-bottom:10px; }
  .card.done { opacity:.45; }
  .card h2 { font-size:16px; margin:0 0 6px; line-height:1.35; }
  .card h2 a { color:var(--text); text-decoration:none; }
  .card h2 a:hover { color:var(--accent); }
  .meta { font-size:12.5px; color:var(--dim); display:flex; flex-wrap:wrap;
      gap:6px 14px; align-items:center; }
  .pill { background:#20283a; color:#9cc1ff; padding:2px 9px; border-radius:10px; }
  .pill.hot { background:#3a2616; color:#ffb86b; }
  .trends { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:14px; }
  .trends .chip { background:#1b2a1e; color:#7ee087; border:1px solid #2a4a30;
      padding:5px 12px; border-radius:16px; font-size:12.5px; cursor:pointer; }
  .trends .chip small { color:#5a8a62; }
  .why { font-size:12px; color:#e0c36b; margin-top:6px; }
  .meta .db { margin-left:auto; background:none; border:1px solid var(--border);
      color:var(--dim); border-radius:6px; padding:3px 10px; font-size:12px; cursor:pointer; }
  .meta .db:hover { border-color:var(--accent); color:var(--accent); }
  .extra { font-size:12.5px; margin-top:6px; }
  .extra a { color:var(--accent); text-decoration:none; margin-right:12px; }
  .more { display:block; margin:18px auto; background:var(--card); color:var(--accent);
      border:1px solid var(--border); padding:10px 26px; border-radius:8px;
      font-size:14px; cursor:pointer; }
  .empty { color:var(--dim); text-align:center; padding:50px 0; }
</style>
</head>
<body>
<div class="wrap">
  <h1>AI News Radar <span class="dot">&#9679;</span></h1>
  <div class="updated">Updated: __UPDATED__ (auto-refreshes every hour)</div>
  <div class="trends" id="trends"></div>
  <div class="bar" id="pillars"></div>
  <div class="search"><input id="q" placeholder="Search stories... (e.g. Gemini, Altman, robot)"></div>
  <div class="count" id="count"></div>
  <div id="list"></div>
  <button class="more" id="more" style="display:none">Show more</button>
</div>
<script>
const PILLARS = __PILLARS__;
const ITEMS = __ITEMS__;
const TRENDS = __TRENDS__;
const PAGE = 60;
let pillar = 0, hideDone = false, hotOnly = false, topMode = false, q = "", shown = PAGE;
const doneSet = new Set(JSON.parse(localStorage.getItem("done") || "[]"));

function ago(iso) {
  if (!iso) return "";
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 3600) return Math.max(1, s/60|0) + " min ago";
  if (s < 86400) return (s/3600|0) + " hours ago";
  return (s/86400|0) + " days ago";
}
function esc(t) { const d = document.createElement("div"); d.textContent = t; return d.innerHTML; }

function filtered() {
  const needle = q.toLowerCase();
  let items = ITEMS.filter(it =>
    (!pillar || it.p === pillar) &&
    (!hideDone || !doneSet.has(it.u)) &&
    (!hotOnly || (it.l && it.l.length)) &&
    (!topMode || it.sc >= 5) &&
    (!needle || it.t.toLowerCase().includes(needle)));
  if (topMode) items = items.slice().sort((a, b) => b.sc - a.sc);
  return items;
}

function render() {
  const items = filtered();
  document.getElementById("count").textContent =
    items.length + " stories" + (q ? ' for "' + q + '"' : "") +
    (pillar ? " in " + PILLARS[pillar] : "");
  const list = document.getElementById("list");
  list.innerHTML = items.length ? "" : '<div class="empty">No stories found.</div>';
  items.slice(0, shown).forEach(it => {
    const d = document.createElement("div");
    d.className = "card" + (doneSet.has(it.u) ? " done" : "");
    let extra = "", hot = "";
    if (it.l && it.l.length) {
      hot = '<span class="pill hot">&#128293; ' + (it.l.length + 1) + " sources</span>";
      extra = '<div class="extra">also covered by: ' + it.l.map(x =>
        '<a href="' + esc(x.url) + '" target="_blank" rel="noopener">' + esc(x.source) + "</a>").join("") + "</div>";
    }
    const why = (topMode && it.r && it.r.length)
      ? '<div class="why">&#11088; score ' + it.sc + " &mdash; " + esc(it.r.join(" · ")) + "</div>" : "";
    d.innerHTML =
      '<h2><a href="' + esc(it.u) + '" target="_blank" rel="noopener">' + esc(it.t) + "</a></h2>" +
      '<div class="meta"><span class="pill">' + PILLARS[it.p] + "</span>" + hot +
      "<span>" + esc(it.s) + "</span><span>" + ago(it.d) + "</span>" +
      '<button class="db">' + (doneSet.has(it.u) ? "undo" : "done &#10003;") + "</button></div>" + why + extra;
    d.querySelector(".db").onclick = () => {
      doneSet.has(it.u) ? doneSet.delete(it.u) : doneSet.add(it.u);
      localStorage.setItem("done", JSON.stringify([...doneSet]));
      render();
    };
    list.appendChild(d);
  });
  document.getElementById("more").style.display = items.length > shown ? "block" : "none";
}

function bar() {
  const el = document.getElementById("pillars");
  el.innerHTML = "";
  const top = document.createElement("button");
  top.innerHTML = "&#11088; Top Picks";
  top.className = topMode ? "active" : "";
  top.title = "Best video stories right now, ranked by score";
  top.onclick = () => { topMode = !topMode; shown = PAGE; bar(); render(); };
  el.appendChild(top);
  const defs = [[0, "All"]].concat(Object.entries(PILLARS).map(([k, v]) => [+k, v]));
  defs.forEach(([num, name]) => {
    const b = document.createElement("button");
    b.textContent = name;
    b.className = num === pillar ? "active" : "";
    b.onclick = () => { pillar = num; shown = PAGE; bar(); render(); };
    el.appendChild(b);
  });
  const hot = document.createElement("button");
  hot.innerHTML = "&#128293; Hot";
  hot.className = hotOnly ? "active" : "";
  hot.title = "Stories covered by 2+ sites - usually the big ones";
  hot.onclick = () => { hotOnly = !hotOnly; shown = PAGE; bar(); render(); };
  el.appendChild(hot);
  const h = document.createElement("button");
  h.innerHTML = "Hide covered";
  h.className = hideDone ? "active" : "";
  h.onclick = () => { hideDone = !hideDone; shown = PAGE; bar(); render(); };
  el.appendChild(h);
}

function trendsBar() {
  const el = document.getElementById("trends");
  TRENDS.forEach(t => {
    const c = document.createElement("button");
    c.className = "chip";
    const arrow = t.status === "new" ? "&#127381;" : "&#128640;";
    c.innerHTML = arrow + " " + esc(t.display) + " <small>" + t.now +
      (t.prev ? " (was " + t.prev + ")" : "") + "</small>";
    c.title = "Click to see all stories about " + t.display;
    c.onclick = () => {
      q = t.display; document.getElementById("q").value = t.display;
      shown = PAGE; render();
    };
    el.appendChild(c);
  });
}

document.getElementById("q").addEventListener("input", e => {
  q = e.target.value.trim(); shown = PAGE; render();
});
document.getElementById("more").onclick = () => { shown += PAGE; render(); };
trendsBar(); bar(); render();
</script>
</body>
</html>
"""


def generate():
    conn = database.connect()
    rows = conn.execute(
        "SELECT id, title, url, links, source, pillar, published, fetched FROM items "
        "ORDER BY COALESCE(published, fetched) DESC LIMIT ?", (MAX_STORIES,)
    ).fetchall()

    # Trend chips (new + rising only) and video-worthiness scores
    trends = scoring.compute_trends(conn)
    chips = [t for t in trends if t["status"] in ("new", "rising")][:10]
    score_map = {s["id"]: s for s in scoring.score_items(conn, trends)}
    conn.close()

    items = []
    for r in rows:
        s = score_map.get(r["id"])
        items.append({
            "t": r["title"], "u": r["url"], "s": r["source"], "p": r["pillar"],
            "d": r["published"] or r["fetched"],
            "l": json.loads(r["links"] or "[]"),
            "sc": s["score"] if s else 0,
            "r": s["reasons"] if s else [],
        })

    updated = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    html = (PAGE
            .replace("__PILLARS__", json.dumps(config.CATEGORIES))
            .replace("__ITEMS__", json.dumps(items, ensure_ascii=False))
            .replace("__TRENDS__", json.dumps(chips, ensure_ascii=False))
            .replace("__UPDATED__", updated))

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"docs/index.html written with {len(items)} stories.")


if __name__ == "__main__":
    generate()
