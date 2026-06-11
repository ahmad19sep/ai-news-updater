"""
AI News Radar - Static site generator (online Creator Studio)

Reads news.db and writes docs/index.html - published free on GitHub Pages.
The cloud server regenerates it every hour after fetching news.

Three tabs, all working in the browser (no server needed):
  News    - stories, filters, search, trends, top picks, done marks
  Planner - video board saved on your device (localStorage)
  Prep    - paste/pick a story -> ready prompt to copy into the Claude app

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
<title>AI News Radar Studio</title>
<style>
  :root { --bg:#0f1217; --card:#171c24; --text:#e8eaed; --dim:#9aa3af;
          --accent:#4f9cff; --border:#262d38; --gold:#e0c36b; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
         font:15px/1.5 system-ui, "Segoe UI", sans-serif; }
  .wrap { max-width:980px; margin:0 auto; padding:18px 14px 60px; }
  h1 { font-size:22px; margin:6px 0 4px; } h1 .dot { color:var(--accent); }
  .updated { color:var(--dim); font-size:12.5px; margin-bottom:14px; }
  .tabs { display:flex; gap:8px; margin-bottom:16px; }
  .tabs button { background:var(--card); color:var(--text); border:1px solid var(--border);
      padding:8px 18px; border-radius:8px; font-size:14px; cursor:pointer; }
  .tabs button.active { background:var(--accent); border-color:var(--accent); color:#fff; }
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
  .meta button { background:none; border:1px solid var(--border); color:var(--dim);
      border-radius:6px; padding:3px 10px; font-size:12px; cursor:pointer; }
  .meta button:hover { border-color:var(--accent); color:var(--accent); }
  .actions { margin-left:auto; display:flex; gap:6px; }
  .extra { font-size:12.5px; margin-top:6px; }
  .extra a { color:var(--accent); text-decoration:none; margin-right:12px; }
  .why { font-size:12px; color:var(--gold); margin-top:6px; }
  .trends { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:14px; }
  .trends .chip { background:#1b2a1e; color:#7ee087; border:1px solid #2a4a30;
      padding:5px 12px; border-radius:16px; font-size:12.5px; cursor:pointer; }
  .trends .chip small { color:#5a8a62; }
  .more { display:block; margin:18px auto; background:var(--card); color:var(--accent);
      border:1px solid var(--border); padding:10px 26px; border-radius:8px;
      font-size:14px; cursor:pointer; }
  .empty { color:var(--dim); text-align:center; padding:50px 0; }
  /* Planner board */
  .board { display:flex; gap:12px; overflow-x:auto; padding-bottom:20px; }
  .col { min-width:235px; width:235px; flex-shrink:0; }
  .col h3 { font-size:14px; color:var(--dim); margin:0 0 10px; }
  .pcard { background:var(--card); border:1px solid var(--border); border-radius:10px;
           padding:10px 12px; margin-bottom:10px; font-size:13.5px; }
  .pcard .t { font-weight:600; margin-bottom:6px; line-height:1.3; }
  .pcard a { color:var(--accent); font-size:12px; text-decoration:none; }
  .pcard .row { display:flex; gap:6px; margin-top:8px; flex-wrap:wrap; align-items:center; }
  .pcard textarea { width:100%; min-height:42px; font-size:12.5px; margin-top:6px;
      background:#11151c; border:1px solid var(--border); color:var(--text);
      border-radius:6px; padding:6px 8px; }
  .pcard select, .pcard input[type=date] { font-size:12px; padding:4px 6px;
      background:#11151c; border:1px solid var(--border); color:var(--text); border-radius:6px; }
  .pcard button { background:none; border:1px solid var(--border); color:var(--dim);
      border-radius:6px; padding:3px 9px; font-size:12px; cursor:pointer; }
  .pcard button:hover { border-color:var(--accent); color:var(--accent); }
  .addrow { display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; }
  .addrow input { background:var(--card); border:1px solid var(--border); color:var(--text);
      padding:9px 12px; border-radius:8px; font-size:14px; }
  .btn { background:var(--accent); border:none; color:#fff; padding:9px 16px;
      border-radius:8px; cursor:pointer; font-size:14px; }
  .ghost { background:var(--card); color:var(--text); border:1px solid var(--border);
      padding:9px 16px; border-radius:8px; cursor:pointer; font-size:13px; }
  /* Prep */
  .brief { background:var(--card); border:1px solid var(--border); border-radius:10px;
           padding:16px 18px; margin-bottom:14px; }
  .brief h3 { margin:0 0 10px; font-size:15px; color:var(--gold); }
  #promptbox { width:100%; min-height:280px; font-family:Consolas, monospace;
      font-size:12.5px; background:#11151c; border:1px solid var(--border);
      color:var(--text); border-radius:8px; padding:10px; }
  .copied { color:#7ee087; font-size:13px; margin-left:10px; }
  .toast { position:fixed; bottom:20px; left:50%; transform:translateX(-50%);
      background:var(--accent); color:#fff; padding:10px 22px; border-radius:20px;
      font-size:14px; opacity:0; transition:opacity .3s; pointer-events:none; }
  .toast.show { opacity:1; }
</style>
</head>
<body>
<div class="wrap">
  <h1>AI News Radar Studio <span class="dot">&#9679;</span></h1>
  <div class="updated">Updated: __UPDATED__ (auto-refreshes every hour)</div>

  <div class="tabs">
    <button id="tabbtn-news" class="active" onclick="switchTab('news')">&#128240; News</button>
    <button id="tabbtn-plan" onclick="switchTab('plan')">&#127916; Planner</button>
    <button id="tabbtn-prep" onclick="switchTab('prep')">&#128221; Prep</button>
  </div>

  <section id="tab-news">
    <div class="trends" id="trends"></div>
    <div class="bar" id="pillars"></div>
    <div class="search"><input id="q" placeholder="Search stories... (e.g. Gemini, Altman, robot)"></div>
    <div class="count" id="count"></div>
    <div id="list"></div>
    <button class="more" id="more" style="display:none">Show more</button>
  </section>

  <section id="tab-plan" hidden>
    <div class="addrow">
      <input id="newidea" style="flex:1;min-width:220px" placeholder="New video idea (or use &#127916; on any news story)">
      <button class="btn" onclick="addIdea()">+ Add</button>
      <button class="ghost" onclick="exportPlans()">Export</button>
      <button class="ghost" onclick="importPlans()">Import</button>
    </div>
    <p class="count">Plans are saved in THIS browser. Use Export/Import to move
       them between phone and PC.</p>
    <div class="board" id="board"></div>
  </section>

  <section id="tab-prep" hidden>
    <p class="count">Pick a story (&#128221; button on news cards) or paste a link.
       Then copy the prompt into your <b>Claude app</b> - Claude will read the
       link and write your full script kit.</p>
    <div class="addrow">
      <input id="prepurl" style="flex:1;min-width:220px" placeholder="https://... story link">
      <input id="preptitle" style="width:240px" placeholder="title (optional)">
      <button class="btn" onclick="buildPrep()">Build prompt</button>
    </div>
    <div id="prepout" hidden>
      <div class="brief">
        <h3>&#129302; Prompt for Claude
          <button class="ghost" style="padding:4px 12px;font-size:12px" onclick="copyPrompt()">&#128203; Copy</button>
          <span id="copyok" class="copied"></span></h3>
        <textarea id="promptbox" readonly></textarea>
      </div>
    </div>
  </section>
</div>
<div class="toast" id="toast"></div>

<script>
const PILLARS = __PILLARS__;
const ITEMS = __ITEMS__;
const TRENDS = __TRENDS__;
const PAGE = 60;
const STAGES = [["idea","\\uD83D\\uDCA1 Idea"],["script","\\u270D\\uFE0F Script"],
  ["record","\\uD83C\\uDFA5 Record"],["edit","\\u2702\\uFE0F Edit"],
  ["uploaded","\\u2B06\\uFE0F Uploaded"],["published","\\u2705 Published"]];
let pillar = 0, hideDone = false, hotOnly = false, topMode = false, q = "", shown = PAGE;
const doneSet = new Set(JSON.parse(localStorage.getItem("done") || "[]"));
let plans = JSON.parse(localStorage.getItem("plans") || "[]");

function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg; t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 1800);
}
function savePlans() { localStorage.setItem("plans", JSON.stringify(plans)); }
function switchTab(name) {
  ["news","plan","prep"].forEach(n => {
    document.getElementById("tab-" + n).hidden = n !== name;
    document.getElementById("tabbtn-" + n).classList.toggle("active", n === name);
  });
  if (name === "plan") renderBoard();
}
function ago(iso) {
  if (!iso) return "";
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 3600) return Math.max(1, s/60|0) + " min ago";
  if (s < 86400) return (s/3600|0) + " hours ago";
  return (s/86400|0) + " days ago";
}
function esc(t) { const d = document.createElement("div"); d.textContent = t; return d.innerHTML; }

/* ---------------- News tab ---------------- */
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
      '<span class="actions">' +
      '<button class="plan-btn">&#127916; plan</button>' +
      '<button class="prep-btn">&#128221;</button>' +
      '<button class="db">' + (doneSet.has(it.u) ? "undo" : "done &#10003;") + "</button>" +
      "</span></div>" + why + extra;
    d.querySelector(".db").onclick = () => {
      doneSet.has(it.u) ? doneSet.delete(it.u) : doneSet.add(it.u);
      localStorage.setItem("done", JSON.stringify([...doneSet]));
      render();
    };
    d.querySelector(".plan-btn").onclick = () => { addPlan(it.t, it.u); };
    d.querySelector(".prep-btn").onclick = () => {
      document.getElementById("prepurl").value = it.u;
      document.getElementById("preptitle").value = it.t;
      switchTab("prep"); buildPrep();
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
    c.onclick = () => {
      q = t.display; document.getElementById("q").value = t.display;
      shown = PAGE; render();
    };
    el.appendChild(c);
  });
}

/* ---------------- Planner tab ---------------- */
function addPlan(title, url) {
  plans.unshift({ id: Date.now(), title: title, url: url || "", notes: "",
                  platform: "both", date: "", stage: "idea" });
  savePlans();
  toast("Added to Planner \\uD83C\\uDFAC");
}
function addIdea() {
  const inp = document.getElementById("newidea");
  if (!inp.value.trim()) return;
  addPlan(inp.value.trim(), "");
  inp.value = "";
  renderBoard();
}
function renderBoard() {
  const board = document.getElementById("board");
  board.innerHTML = "";
  STAGES.forEach(([key, label], si) => {
    const col = document.createElement("div");
    col.className = "col";
    const cards = plans.filter(p => p.stage === key);
    col.innerHTML = "<h3>" + label + " (" + cards.length + ")</h3>";
    cards.forEach(p => {
      const c = document.createElement("div");
      c.className = "pcard";
      c.innerHTML =
        '<div class="t">' + esc(p.title) + "</div>" +
        (p.url ? '<a href="' + esc(p.url) + '" target="_blank">source link</a>' : "") +
        '<div class="row"><select class="plat">' +
        ["long","short","both"].map(v =>
          '<option value="' + v + '"' + (p.platform === v ? " selected" : "") + ">" +
          v[0].toUpperCase() + v.slice(1) + "</option>").join("") +
        '</select><input type="date" class="pdate" value="' + esc(p.date || "") + '"></div>' +
        '<textarea class="pnotes" placeholder="notes...">' + esc(p.notes || "") + "</textarea>" +
        '<div class="row">' +
        (si > 0 ? '<button class="mv-prev">&larr;</button>' : "") +
        (si < STAGES.length - 1 ? '<button class="mv-next">&rarr;</button>' : "") +
        '<button class="do-prep" style="color:var(--gold)">&#128221; prep</button>' +
        '<button class="del">&#10005;</button></div>';
      c.querySelector(".plat").onchange = e => { p.platform = e.target.value; savePlans(); };
      c.querySelector(".pdate").onchange = e => { p.date = e.target.value; savePlans(); };
      c.querySelector(".pnotes").onchange = e => { p.notes = e.target.value; savePlans(); };
      const prev = c.querySelector(".mv-prev");
      if (prev) prev.onclick = () => { p.stage = STAGES[si - 1][0]; savePlans(); renderBoard(); };
      const next = c.querySelector(".mv-next");
      if (next) next.onclick = () => { p.stage = STAGES[si + 1][0]; savePlans(); renderBoard(); };
      c.querySelector(".do-prep").onclick = () => {
        document.getElementById("prepurl").value = p.url;
        document.getElementById("preptitle").value = p.title;
        switchTab("prep"); buildPrep();
      };
      c.querySelector(".del").onclick = () => {
        if (confirm("Delete this card?")) {
          plans = plans.filter(x => x.id !== p.id); savePlans(); renderBoard();
        }
      };
      col.appendChild(c);
    });
    board.appendChild(col);
  });
}
function exportPlans() {
  navigator.clipboard.writeText(JSON.stringify(plans))
    .then(() => toast("Plans copied - paste in Import on the other device"));
}
function importPlans() {
  const txt = prompt("Paste the exported plans text here:");
  if (!txt) return;
  try {
    const arr = JSON.parse(txt);
    if (Array.isArray(arr)) { plans = arr; savePlans(); renderBoard(); toast("Plans imported"); }
  } catch (e) { alert("That text is not valid plans data."); }
}

/* ---------------- Prep tab ---------------- */
const COMMON = new Set(["the","and","for","with","that","this","from","what",
  "how","why","new","its","has","have","are","was","will","can","you","your",
  "says","after","about","over","into","more","most"]);
function words(t) {
  return new Set((t.toLowerCase().match(/[a-z0-9]{3,}/g) || []).filter(w => !COMMON.has(w)));
}
function buildPrep() {
  const url = document.getElementById("prepurl").value.trim();
  const title = document.getElementById("preptitle").value.trim() || url;
  if (!url && !title) { toast("Paste a link first"); return; }
  const tw = words(title);
  const related = [];
  for (const it of ITEMS) {
    if (it.u === url) continue;
    let common = 0;
    for (const w of words(it.t)) if (tw.has(w)) common++;
    if (common >= 2) related.push([common, it]);
  }
  related.sort((a, b) => b[0] - a[0]);
  const rel = related.slice(0, 6).map(r => "- " + r[1].t + " (" + r[1].s + ") " + r[1].u);
  const prompt =
"You are my video scriptwriter for my AI news YouTube channel. My audience is Pakistan and India - simple people who love AI news in easy Roman Urdu/Hindi.\\n\\n" +
"THE STORY: " + title + "\\n" +
"SOURCE LINK: " + url + "\\n\\n" +
"FIRST: open and read the source link above.\\n\\n" +
"RELATED COVERAGE (read if useful, for extra angles):\\n" +
(rel.length ? rel.join("\\n") : "(none)") + "\\n\\n" +
"CREATE FOR ME:\\n\\n" +
"1. LONG VIDEO SCRIPT (5-8 minutes, Roman Urdu/Hindi):\\n" +
"   - Hook in first 10 seconds (a question or shocking fact)\\n" +
"   - Explain the story simply, like talking to a friend\\n" +
"   - Why it matters for normal people in Pakistan/India\\n" +
"   - My opinion section (leave a placeholder for me)\\n" +
"   - Ending with subscribe call-to-action\\n\\n" +
"2. SHORT/REEL SCRIPT (45-60 seconds, Roman Urdu/Hindi):\\n" +
"   - Hook -> 3 punchy facts -> strong ending line\\n\\n" +
"3. FIVE TITLE OPTIONS (mix Roman Urdu + English keywords people search)\\n\\n" +
"4. YOUTUBE DESCRIPTION (2-3 lines + hashtags + 15 SEO tags)\\n\\n" +
"5. THREE THUMBNAIL TEXT IDEAS (max 4 words each, curiosity-making)\\n\\n" +
"Keep all language SIMPLE. Avoid difficult English words. Energy high.";
  document.getElementById("promptbox").value = prompt;
  document.getElementById("prepout").hidden = false;
}
function copyPrompt() {
  navigator.clipboard.writeText(document.getElementById("promptbox").value)
    .then(() => document.getElementById("copyok").textContent = "copied! paste it in Claude");
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
