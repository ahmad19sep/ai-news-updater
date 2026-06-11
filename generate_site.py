"""
AI News Radar - Static site generator (online Creator Studio)

Reads news.db and writes docs/index.html - published free on GitHub Pages.
The cloud server regenerates it every hour after fetching news.

Four tabs, all working in the browser (no server needed):
  News      - stories, filters, search, trends, top picks, done marks
  Planner   - video board saved on your device (localStorage)
  Prep      - pick a story -> ready prompt to copy into the Claude app
  Analytics - YouTube channel stats fetched directly from the YouTube API
              (your API key stays in YOUR browser only)

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

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0b0f17">
<title>AI News Radar — Creator Studio</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:#0b0f17; --bg2:#0e1420; --surface:#131a26; --surface2:#18202e;
    --text:#e7ecf3; --dim:#8b96a5; --faint:#5c6675;
    --line:rgba(255,255,255,.07); --line2:rgba(255,255,255,.12);
    --indigo:#6366f1; --cyan:#22d3ee; --gold:#fbbf24; --green:#34d399;
    --red:#f87171; --orange:#fb923c;
    --grad:linear-gradient(135deg,#6366f1 0%,#22d3ee 100%);
    --shadow:0 10px 30px -12px rgba(0,0,0,.55);
    --r:14px;
  }
  * { box-sizing:border-box; }
  html { scrollbar-color:#2a3342 transparent; }
  body { margin:0; background:radial-gradient(1200px 500px at 70% -10%, #141c30 0%, var(--bg) 55%);
         color:var(--text); font:14.5px/1.55 Inter, system-ui, "Segoe UI", sans-serif;
         -webkit-font-smoothing:antialiased; }
  ::selection { background:rgba(99,102,241,.35); }
  a { color:var(--cyan); }
  .wrap { max-width:1020px; margin:0 auto; padding:0 16px 80px; }

  /* ---------- header ---------- */
  header { position:sticky; top:0; z-index:50; backdrop-filter:blur(14px);
           background:rgba(11,15,23,.72); border-bottom:1px solid var(--line); }
  .hrow { max-width:1020px; margin:0 auto; padding:14px 16px;
          display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
  .logo { display:flex; align-items:center; gap:10px; font-weight:800;
          font-size:17px; letter-spacing:-.02em; }
  .logo .orb { width:11px; height:11px; border-radius:50%; background:var(--grad);
          box-shadow:0 0 14px rgba(34,211,238,.8); animation:pulse 2.4s infinite; }
  @keyframes pulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(.78);opacity:.7} }
  .logo small { font-weight:500; color:var(--faint); font-size:11px; margin-left:2px; }
  .tabs { display:flex; gap:4px; background:var(--surface); border:1px solid var(--line);
          padding:4px; border-radius:999px; margin-left:auto; }
  .tabs button { background:none; border:none; color:var(--dim); padding:7px 16px;
          border-radius:999px; font:600 13px Inter, sans-serif; cursor:pointer;
          transition:.18s; white-space:nowrap; }
  .tabs button:hover { color:var(--text); }
  .tabs button.active { background:var(--grad); color:#fff;
          box-shadow:0 4px 14px -4px rgba(99,102,241,.6); }
  .updated { width:100%; color:var(--faint); font-size:11.5px; }

  /* ---------- chips & filter bar ---------- */
  .trends { display:flex; flex-wrap:wrap; gap:8px; margin:18px 0 4px; }
  .chip { display:inline-flex; align-items:center; gap:6px;
          background:rgba(52,211,153,.08); color:var(--green);
          border:1px solid rgba(52,211,153,.25); padding:5px 13px;
          border-radius:999px; font:500 12.5px Inter; cursor:pointer; transition:.15s; }
  .chip:hover { background:rgba(52,211,153,.16); transform:translateY(-1px); }
  .chip small { color:rgba(52,211,153,.65); font-weight:400; }
  .bar { display:flex; flex-wrap:wrap; gap:8px; margin:14px 0; }
  .bar button { background:var(--surface); color:var(--dim); border:1px solid var(--line);
          padding:6px 14px; border-radius:999px; font:500 12.5px Inter;
          cursor:pointer; transition:.15s; }
  .bar button:hover { color:var(--text); border-color:var(--line2); }
  .bar button.active { background:var(--grad); border-color:transparent; color:#fff;
          font-weight:600; box-shadow:0 4px 12px -4px rgba(99,102,241,.55); }
  .bar button.gold.active { background:linear-gradient(135deg,#f59e0b,#fbbf24); }
  .search { display:flex; gap:10px; margin:6px 0 4px; }
  .search input { flex:1; background:var(--surface); border:1px solid var(--line);
          color:var(--text); padding:11px 16px; border-radius:12px; font:14px Inter;
          outline:none; transition:.18s; }
  .search input:focus { border-color:var(--indigo);
          box-shadow:0 0 0 3px rgba(99,102,241,.18); }
  .count { color:var(--faint); font-size:12.5px; margin:10px 2px 14px; }

  /* ---------- story cards ---------- */
  .card { background:var(--surface); border:1px solid var(--line); border-radius:var(--r);
          padding:16px 18px; margin-bottom:12px; transition:.18s; position:relative; }
  .card:hover { border-color:var(--line2); transform:translateY(-1px); box-shadow:var(--shadow); }
  .card.done { opacity:.4; }
  .card h2 { font-size:15.5px; font-weight:600; margin:0 0 9px; line-height:1.4;
          letter-spacing:-.01em; }
  .card h2 a { color:var(--text); text-decoration:none; }
  .card h2 a:hover { color:var(--cyan); }
  .meta { font-size:12px; color:var(--dim); display:flex; flex-wrap:wrap;
          gap:6px 12px; align-items:center; }
  .pill { background:rgba(99,102,241,.12); color:#a5b4fc; padding:2.5px 10px;
          border-radius:999px; font-weight:500; font-size:11.5px; }
  .pill.hot { background:rgba(251,146,60,.12); color:var(--orange); }
  .actions { margin-left:auto; display:flex; gap:6px; }
  .meta button { background:none; border:1px solid var(--line); color:var(--dim);
          border-radius:8px; padding:4px 11px; font:500 11.5px Inter; cursor:pointer;
          transition:.15s; }
  .meta button:hover { border-color:var(--indigo); color:var(--text);
          background:rgba(99,102,241,.1); }
  .extra { font-size:12px; margin-top:8px; color:var(--dim); }
  .extra a { color:var(--cyan); text-decoration:none; margin-right:12px; }
  .why { font-size:12px; color:var(--gold); margin-top:8px; }
  .more { display:block; margin:22px auto; background:var(--surface); color:var(--text);
          border:1px solid var(--line); padding:11px 34px; border-radius:999px;
          font:600 13px Inter; cursor:pointer; transition:.18s; }
  .more:hover { border-color:var(--indigo); box-shadow:var(--shadow); }
  .empty { color:var(--faint); text-align:center; padding:60px 0; }

  /* ---------- planner ---------- */
  .addrow { display:flex; gap:10px; margin:18px 0 14px; flex-wrap:wrap; }
  .addrow input, select, input[type=date], input[type=number], textarea {
          background:var(--surface); border:1px solid var(--line); color:var(--text);
          padding:10px 14px; border-radius:12px; font:13.5px Inter; outline:none; }
  .addrow input:focus, textarea:focus { border-color:var(--indigo); }
  .btn { background:var(--grad); border:none; color:#fff; padding:10px 20px;
          border-radius:12px; font:600 13.5px Inter; cursor:pointer; transition:.18s; }
  .btn:hover { filter:brightness(1.12); box-shadow:0 6px 18px -6px rgba(99,102,241,.7); }
  .ghost { background:var(--surface); color:var(--dim); border:1px solid var(--line);
          padding:10px 18px; border-radius:12px; font:500 13px Inter; cursor:pointer;
          transition:.15s; }
  .ghost:hover { color:var(--text); border-color:var(--line2); }
  .board { display:flex; gap:14px; overflow-x:auto; padding:4px 2px 24px; }
  .col { min-width:248px; width:248px; flex-shrink:0; }
  .col h3 { font-size:12px; font-weight:700; color:var(--faint); margin:0 0 10px;
          text-transform:uppercase; letter-spacing:.08em; display:flex; gap:8px; }
  .col h3 .n { color:var(--dim); background:var(--surface); border-radius:999px;
          padding:0 8px; font-size:11px; }
  .pcard { background:var(--surface); border:1px solid var(--line); border-radius:12px;
          padding:12px 14px; margin-bottom:10px; font-size:13px; transition:.15s; }
  .pcard:hover { border-color:var(--line2); }
  .pcard .t { font-weight:600; margin-bottom:6px; line-height:1.35; }
  .pcard a { font-size:11.5px; text-decoration:none; }
  .pcard .row { display:flex; gap:6px; margin-top:9px; flex-wrap:wrap; align-items:center; }
  .pcard textarea { width:100%; min-height:44px; font-size:12px; margin-top:8px;
          padding:7px 10px; border-radius:8px; }
  .pcard select, .pcard input[type=date] { font-size:11.5px; padding:5px 8px; border-radius:8px; }
  .pcard button { background:none; border:1px solid var(--line); color:var(--dim);
          border-radius:8px; padding:4px 10px; font:500 11.5px Inter; cursor:pointer; }
  .pcard button:hover { border-color:var(--indigo); color:var(--text); }
  .note { color:var(--faint); font-size:12px; margin:0 2px 14px; }

  /* ---------- prep & analytics ---------- */
  .panel { background:var(--surface); border:1px solid var(--line);
          border-radius:var(--r); padding:20px 22px; margin-bottom:16px; }
  .panel h3 { margin:0 0 12px; font-size:14px; font-weight:700; color:var(--gold);
          display:flex; align-items:center; gap:10px; }
  #promptbox { width:100%; min-height:300px; font:12px/1.6 Consolas, monospace; }
  .copied { color:var(--green); font-size:12.5px; }
  .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
          gap:12px; margin:18px 0; }
  .stat { background:var(--surface); border:1px solid var(--line); border-radius:var(--r);
          padding:18px; text-align:center; }
  .stat .n { font-size:26px; font-weight:800; letter-spacing:-.03em;
          background:var(--grad); -webkit-background-clip:text;
          background-clip:text; color:transparent; }
  .stat .l { font-size:11.5px; color:var(--dim); margin-top:2px; }
  .stat .g { font-size:11px; color:var(--green); margin-top:4px; }
  .insight { background:var(--surface); border:1px solid var(--line);
          border-left:3px solid var(--gold); border-radius:10px;
          padding:11px 16px; margin-bottom:9px; font-size:13px; }
  table { width:100%; border-collapse:collapse; font-size:12.5px; }
  th, td { text-align:left; padding:9px 10px; border-bottom:1px solid var(--line); }
  th { color:var(--faint); font-weight:600; font-size:11px; text-transform:uppercase;
          letter-spacing:.06em; }
  td a { color:var(--text); text-decoration:none; } td a:hover { color:var(--cyan); }
  .wk { display:flex; gap:6px; align-items:flex-end; height:64px; margin:10px 0 4px; }
  .wk div { width:34px; background:var(--grad); border-radius:6px 6px 0 0; min-height:6px;
          opacity:.9; }
  .wk-l { display:flex; gap:6px; font-size:10.5px; color:var(--faint); }
  .wk-l span { width:34px; text-align:center; }
  .err { color:var(--red); font-size:13px; margin:8px 0; }
  h2.sec { font-size:15px; font-weight:700; margin:26px 0 12px; letter-spacing:-.01em; }

  .toast { position:fixed; bottom:24px; left:50%; transform:translateX(-50%) translateY(8px);
          background:var(--grad); color:#fff; padding:11px 26px; border-radius:999px;
          font:600 13px Inter; opacity:0; transition:.25s; pointer-events:none;
          box-shadow:0 10px 30px -8px rgba(99,102,241,.7); z-index:99; }
  .toast.show { opacity:1; transform:translateX(-50%) translateY(0); }
  @media (max-width:640px) {
    .tabs { margin-left:0; width:100%; justify-content:space-between; }
    .tabs button { padding:7px 10px; font-size:12px; }
  }
</style>
</head>
<body>
<header>
  <div class="hrow">
    <div class="logo"><span class="orb"></span> AI News Radar <small>STUDIO</small></div>
    <nav class="tabs">
      <button id="tabbtn-news" class="active" onclick="switchTab('news')">News</button>
      <button id="tabbtn-plan" onclick="switchTab('plan')">Planner</button>
      <button id="tabbtn-prep" onclick="switchTab('prep')">Prep</button>
      <button id="tabbtn-stats" onclick="switchTab('stats')">Analytics</button>
    </nav>
    <div class="updated">Updated __UPDATED__ · refreshes every hour · 100% free</div>
  </div>
</header>
<div class="wrap">

  <section id="tab-news">
    <div class="trends" id="trends"></div>
    <div class="bar" id="pillars"></div>
    <div class="search"><input id="q" placeholder="Search stories… Gemini, Altman, robots"></div>
    <div class="count" id="count"></div>
    <div id="list"></div>
    <button class="more" id="more" style="display:none">Show more</button>
  </section>

  <section id="tab-plan" hidden>
    <div class="addrow">
      <input id="newidea" style="flex:1;min-width:220px" placeholder="New video idea (or tap 🎬 on any story)">
      <button class="btn" onclick="addIdea()">+ Add</button>
      <button class="ghost" onclick="exportPlans()">Export</button>
      <button class="ghost" onclick="importPlans()">Import</button>
    </div>
    <p class="note">Plans save in this browser. Export → Import moves them between phone and PC.</p>
    <div class="board" id="board"></div>
  </section>

  <section id="tab-prep" hidden>
    <p class="note">Pick a story (📝 on news cards) or paste a link, then copy the prompt
       into your <b style="color:var(--text)">Claude app</b> — Claude reads the link and
       writes your full script kit.</p>
    <div class="addrow">
      <input id="prepurl" style="flex:1;min-width:220px" placeholder="https://… story link">
      <input id="preptitle" style="width:240px" placeholder="title (optional)">
      <button class="btn" onclick="buildPrep()">Build prompt</button>
    </div>
    <div id="prepout" hidden>
      <div class="panel">
        <h3>Prompt for Claude
          <button class="ghost" style="padding:5px 14px;font-size:12px" onclick="copyPrompt()">📋 Copy</button>
          <span id="copyok" class="copied"></span></h3>
        <textarea id="promptbox" readonly></textarea>
      </div>
    </div>
  </section>

  <section id="tab-stats" hidden>
    <div id="yt-setup" hidden>
      <div class="panel" style="max-width:560px">
        <h3>Connect your YouTube channel (one time, free)</h3>
        <ol style="font-size:13px;line-height:2;color:var(--dim)">
          <li>Enable <a target="_blank" href="https://console.cloud.google.com/apis/library/youtube.googleapis.com">YouTube Data API v3</a></li>
          <li>Create an <a target="_blank" href="https://console.cloud.google.com/apis/credentials">API key</a> and copy it</li>
          <li>Paste below — the key is saved <b>only in this browser</b>, never uploaded</li>
        </ol>
        <div id="yt-err" class="err"></div>
        <input id="yt-key" style="width:100%;margin-bottom:10px" placeholder="API key (AIza…)">
        <input id="yt-handle" style="width:100%;margin-bottom:12px" placeholder="Channel handle, e.g. @yourchannel">
        <button class="btn" onclick="ytConnect()">Connect channel</button>
      </div>
    </div>
    <div id="yt-dash" hidden>
      <p class="note">Channel: <b id="yt-title" style="color:var(--text)"></b>
        <a href="#" onclick="ytReset();return false" style="font-size:12px;margin-left:10px">change</a>
        <span id="yt-err2" class="err"></span></p>
      <div class="stats" id="yt-stats"></div>
      <h2 class="sec">💡 Insights</h2>
      <div id="yt-insights"></div>
      <h2 class="sec">📅 Uploads per week <span style="color:var(--faint);font-size:11px">(newest first)</span></h2>
      <div class="wk" id="yt-weeks"></div>
      <div class="wk-l" id="yt-weeks-l"></div>
      <h2 class="sec">🎬 Recent videos</h2>
      <div style="overflow-x:auto"><table id="yt-videos"></table></div>
      <h2 class="sec">📱 Other platforms <span style="color:var(--faint);font-size:11px">(enter weekly by hand)</span></h2>
      <div class="addrow">
        <select id="soc-p"><option>TikTok</option><option>Instagram</option><option>Facebook</option></select>
        <input id="soc-f" type="number" placeholder="followers" style="width:120px">
        <input id="soc-v" type="number" placeholder="views this week" style="width:150px">
        <button class="btn" onclick="socSave()">Save</button>
      </div>
      <div style="overflow-x:auto"><table id="soc-table"></table></div>
    </div>
  </section>
</div>
<div class="toast" id="toast"></div>

<script>
const PILLARS = __PILLARS__;
const ITEMS = __ITEMS__;
const TRENDS = __TRENDS__;
const PAGE = 60;
const STAGES = [["idea","💡 Idea"],["script","✍️ Script"],["record","🎥 Record"],
  ["edit","✂️ Edit"],["uploaded","⬆️ Uploaded"],["published","✅ Published"]];
let pillar = 0, hideDone = false, hotOnly = false, topMode = false, q = "", shown = PAGE;
const doneSet = new Set(JSON.parse(localStorage.getItem("done") || "[]"));
let plans = JSON.parse(localStorage.getItem("plans") || "[]");

function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg; t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 1900);
}
function savePlans() { localStorage.setItem("plans", JSON.stringify(plans)); }
function switchTab(name) {
  ["news","plan","prep","stats"].forEach(n => {
    document.getElementById("tab-" + n).hidden = n !== name;
    document.getElementById("tabbtn-" + n).classList.toggle("active", n === name);
  });
  if (name === "plan") renderBoard();
  if (name === "stats") ytInit();
}
function ago(iso) {
  if (!iso) return "";
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 3600) return Math.max(1, s/60|0) + " min ago";
  if (s < 86400) return (s/3600|0) + "h ago";
  return (s/86400|0) + "d ago";
}
function esc(t) { const d = document.createElement("div"); d.textContent = t; return d.innerHTML; }
function fmt(n) { return (+n).toLocaleString("en-US"); }

/* ---------------- News ---------------- */
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
      hot = '<span class="pill hot">🔥 ' + (it.l.length + 1) + " sources</span>";
      extra = '<div class="extra">also covered by: ' + it.l.map(x =>
        '<a href="' + esc(x.url) + '" target="_blank" rel="noopener">' + esc(x.source) + "</a>").join("") + "</div>";
    }
    const why = (topMode && it.r && it.r.length)
      ? '<div class="why">⭐ score ' + it.sc + " — " + esc(it.r.join(" · ")) + "</div>" : "";
    d.innerHTML =
      '<h2><a href="' + esc(it.u) + '" target="_blank" rel="noopener">' + esc(it.t) + "</a></h2>" +
      '<div class="meta"><span class="pill">' + PILLARS[it.p] + "</span>" + hot +
      "<span>" + esc(it.s) + "</span><span>" + ago(it.d) + "</span>" +
      '<span class="actions">' +
      '<button class="plan-btn">🎬 plan</button>' +
      '<button class="prep-btn">📝</button>' +
      '<button class="db">' + (doneSet.has(it.u) ? "undo" : "done ✓") + "</button>" +
      "</span></div>" + why + extra;
    d.querySelector(".db").onclick = () => {
      doneSet.has(it.u) ? doneSet.delete(it.u) : doneSet.add(it.u);
      localStorage.setItem("done", JSON.stringify([...doneSet]));
      render();
    };
    d.querySelector(".plan-btn").onclick = () => addPlan(it.t, it.u);
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
  top.innerHTML = "⭐ Top Picks";
  top.className = "gold" + (topMode ? " active" : "");
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
  hot.innerHTML = "🔥 Hot";
  hot.className = hotOnly ? "active" : "";
  hot.onclick = () => { hotOnly = !hotOnly; shown = PAGE; bar(); render(); };
  el.appendChild(hot);
  const h = document.createElement("button");
  h.textContent = "Hide covered";
  h.className = hideDone ? "active" : "";
  h.onclick = () => { hideDone = !hideDone; shown = PAGE; bar(); render(); };
  el.appendChild(h);
}
function trendsBar() {
  const el = document.getElementById("trends");
  TRENDS.forEach(t => {
    const c = document.createElement("button");
    c.className = "chip";
    c.innerHTML = (t.status === "new" ? "🆕" : "🚀") + " " + esc(t.display) +
      " <small>" + t.now + (t.prev ? " (was " + t.prev + ")" : "") + "</small>";
    c.onclick = () => {
      q = t.display; document.getElementById("q").value = t.display;
      shown = PAGE; render();
    };
    el.appendChild(c);
  });
}

/* ---------------- Planner ---------------- */
function addPlan(title, url) {
  plans.unshift({ id: Date.now(), title, url: url || "", notes: "",
                  platform: "both", date: "", stage: "idea" });
  savePlans();
  toast("Added to Planner 🎬");
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
    col.innerHTML = "<h3>" + label + ' <span class="n">' + cards.length + "</span></h3>";
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
        '<textarea class="pnotes" placeholder="notes…">' + esc(p.notes || "") + "</textarea>" +
        '<div class="row">' +
        (si > 0 ? '<button class="mv-prev">←</button>' : "") +
        (si < STAGES.length - 1 ? '<button class="mv-next">→</button>' : "") +
        '<button class="do-prep" style="color:var(--gold)">📝 prep</button>' +
        '<button class="del">✕</button></div>';
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
    .then(() => toast("Plans copied — paste in Import on the other device"));
}
function importPlans() {
  const txt = prompt("Paste the exported plans text here:");
  if (!txt) return;
  try {
    const arr = JSON.parse(txt);
    if (Array.isArray(arr)) { plans = arr; savePlans(); renderBoard(); toast("Plans imported"); }
  } catch (e) { alert("That text is not valid plans data."); }
}

/* ---------------- Prep ---------------- */
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
  const prompt = [
"You are my video scriptwriter for my AI news YouTube channel. My audience is Pakistan and India - simple people who love AI news in easy Roman Urdu/Hindi.",
"",
"THE STORY: " + title,
"SOURCE LINK: " + url,
"",
"FIRST: open and read the source link above.",
"",
"RELATED COVERAGE (read if useful, for extra angles):",
rel.length ? rel.join("\n") : "(none)",
"",
"CREATE FOR ME:",
"",
"1. LONG VIDEO SCRIPT (5-8 minutes, Roman Urdu/Hindi):",
"   - Hook in first 10 seconds (a question or shocking fact)",
"   - Explain the story simply, like talking to a friend",
"   - Why it matters for normal people in Pakistan/India",
"   - My opinion section (leave a placeholder for me)",
"   - Ending with subscribe call-to-action",
"",
"2. SHORT/REEL SCRIPT (45-60 seconds, Roman Urdu/Hindi):",
"   - Hook -> 3 punchy facts -> strong ending line",
"",
"3. FIVE TITLE OPTIONS (mix Roman Urdu + English keywords people search)",
"",
"4. YOUTUBE DESCRIPTION (2-3 lines + hashtags + 15 SEO tags)",
"",
"5. THREE THUMBNAIL TEXT IDEAS (max 4 words each, curiosity-making)",
"",
"Keep all language SIMPLE. Avoid difficult English words. Energy high."].join("\n");
  document.getElementById("promptbox").value = prompt;
  document.getElementById("prepout").hidden = false;
}
function copyPrompt() {
  navigator.clipboard.writeText(document.getElementById("promptbox").value)
    .then(() => document.getElementById("copyok").textContent = "copied! paste it in Claude");
}

/* ---------------- Analytics (browser -> YouTube API directly) ---------------- */
const YTAPI = "https://www.googleapis.com/youtube/v3";
let ytLoaded = false;

async function ytGet(path, params) {
  const u = new URL(YTAPI + "/" + path);
  Object.entries(params).forEach(([k, v]) => u.searchParams.set(k, v));
  const r = await fetch(u);
  const data = await r.json();
  if (data.error) throw new Error(data.error.message || "YouTube API error");
  return data;
}
function ytInit() {
  const key = localStorage.getItem("yt_key"), cid = localStorage.getItem("yt_cid");
  document.getElementById("yt-setup").hidden = !!(key && cid);
  document.getElementById("yt-dash").hidden = !(key && cid);
  if (key && cid && !ytLoaded) ytRefresh();
}
async function ytConnect() {
  const key = document.getElementById("yt-key").value.trim();
  const handle = document.getElementById("yt-handle").value.trim();
  const err = document.getElementById("yt-err");
  err.textContent = "";
  try {
    let cid = (handle.match(/UC[\w-]{22}/) || [])[0];
    if (!cid) {
      const name = (handle.match(/@([\w.-]+)/) || [null, handle])[1];
      const data = await ytGet("channels", { part: "snippet", forHandle: "@" + name, key });
      if (!data.items || !data.items.length) throw new Error('Channel "@' + name + '" not found - check the handle.');
      cid = data.items[0].id;
    }
    localStorage.setItem("yt_key", key);
    localStorage.setItem("yt_cid", cid);
    ytLoaded = false;
    ytInit();
  } catch (e) { err.textContent = e.message; }
}
function ytReset() {
  localStorage.removeItem("yt_key"); localStorage.removeItem("yt_cid");
  ytLoaded = false; ytInit();
}
function parseDur(iso) {
  const h = /(\d+)H/.exec(iso), m = /(\d+)M/.exec(iso), s = /(\d+)S/.exec(iso);
  return (h ? +h[1] * 3600 : 0) + (m ? +m[1] * 60 : 0) + (s ? +s[1] : 0);
}
async function ytRefresh() {
  const key = localStorage.getItem("yt_key"), cid = localStorage.getItem("yt_cid");
  const err = document.getElementById("yt-err2");
  err.textContent = "";
  try {
    const ch = (await ytGet("channels",
      { part: "statistics,contentDetails,snippet", id: cid, key })).items[0];
    const st = ch.statistics;
    const subs = +st.subscriberCount || 0, views = +st.viewCount || 0, vidn = +st.videoCount || 0;
    document.getElementById("yt-title").textContent = ch.snippet.title;

    // daily snapshot in localStorage -> growth since first day
    const snaps = JSON.parse(localStorage.getItem("yt_snaps") || "{}");
    const today = new Date().toISOString().slice(0, 10);
    snaps[today] = { subs, views };
    localStorage.setItem("yt_snaps", JSON.stringify(snaps));
    const firstDay = Object.keys(snaps).sort()[0];
    const growth = firstDay !== today
      ? { subs: subs - snaps[firstDay].subs, views: views - snaps[firstDay].views, since: firstDay }
      : null;

    // recent videos
    let videos = [];
    const pl = ch.contentDetails.relatedPlaylists.uploads;
    const items = (await ytGet("playlistItems",
      { part: "contentDetails", playlistId: pl, maxResults: 15, key })).items || [];
    if (items.length) {
      const ids = items.map(i => i.contentDetails.videoId).join(",");
      videos = ((await ytGet("videos",
        { part: "snippet,statistics,contentDetails", id: ids, key })).items || []).map(v => ({
          title: v.snippet.title, published: v.snippet.publishedAt,
          views: +v.statistics.viewCount || 0, likes: +v.statistics.likeCount || 0,
          secs: parseDur(v.contentDetails.duration),
          url: "https://youtu.be/" + v.id,
        }));
      videos.forEach(v => v.short = v.secs <= 65);
      videos.sort((a, b) => b.published.localeCompare(a.published));
    }

    // consistency
    const perWeek = Array(8).fill(0), wd = {};
    const now = Date.now();
    videos.forEach(v => {
      const dt = new Date(v.published);
      const wk = ((now - dt.getTime()) / 86400000 / 7) | 0;
      if (wk < 8) perWeek[wk]++;
      const day = dt.toLocaleDateString("en-US", { weekday: "long" });
      (wd[day] = wd[day] || []).push(v.views);
    });
    const daysSince = videos.length ? ((now - new Date(videos[0].published).getTime()) / 86400000) | 0 : null;
    let bestDay = "";
    let bestAvg = -1;
    for (const [d, arr] of Object.entries(wd)) {
      const avg = arr.reduce((a, b) => a + b, 0) / arr.length;
      if (avg > bestAvg) { bestAvg = avg; bestDay = d; }
    }

    // render stats
    const sEl = document.getElementById("yt-stats");
    sEl.innerHTML = "";
    [[fmt(subs), "subscribers", growth ? "+" + fmt(growth.subs) + " since " + growth.since : ""],
     [fmt(views), "total views", growth ? "+" + fmt(growth.views) : ""],
     [vidn, "videos", ""],
     [daysSince === null ? "—" : daysSince, "days since upload", ""]].forEach(([n, l, g]) => {
      sEl.innerHTML += '<div class="stat"><div class="n">' + n + '</div><div class="l">' +
        l + "</div>" + (g ? '<div class="g">' + g + "</div>" : "") + "</div>";
    });

    // insights
    const tips = [];
    if (!videos.length) tips.push("No videos yet — upload your first one and stats will appear here!");
    else {
      const sh = videos.filter(v => v.short), lg = videos.filter(v => !v.short);
      if (sh.length && lg.length) {
        const as = sh.reduce((a, v) => a + v.views, 0) / sh.length;
        const al = lg.reduce((a, v) => a + v.views, 0) / lg.length;
        if (as > al * 1.5) tips.push("Shorts get " + (as / Math.max(al, 1)).toFixed(1) + "x more views than long videos — Shorts pull new people in.");
        else if (al > as * 1.5) tips.push("Long videos get " + (al / Math.max(as, 1)).toFixed(1) + "x more views than Shorts — your audience likes depth.");
      }
      const best = videos.slice().sort((a, b) => b.views - a.views)[0];
      tips.push('Best recent video: "' + best.title.slice(0, 60) + '" (' + fmt(best.views) + " views) — make more on this topic.");
      if (daysSince >= 7) tips.push("⚠ " + daysSince + " days since your last upload — consistency is the #1 growth factor.");
      else if (daysSince <= 2) tips.push("Good consistency — last upload was very recent. Keep the rhythm!");
      const recent4 = perWeek.slice(0, 4).reduce((a, b) => a + b, 0);
      if (recent4 && recent4 < 4) tips.push("Only " + recent4 + " uploads in the last 4 weeks — aim for at least 2 per week (1 long + 1 short).");
      if (bestDay) tips.push("Your " + bestDay + " videos get the most views on average — schedule big stories for that day.");
    }
    document.getElementById("yt-insights").innerHTML =
      tips.map(t => '<div class="insight">' + esc(t) + "</div>").join("");

    // weeks chart
    document.getElementById("yt-weeks").innerHTML =
      perWeek.map(n => '<div style="height:' + (6 + n * 14) + 'px" title="' + n + ' uploads"></div>').join("");
    document.getElementById("yt-weeks-l").innerHTML =
      perWeek.map(n => "<span>" + n + "</span>").join("");

    // videos table
    document.getElementById("yt-videos").innerHTML =
      "<tr><th>Video</th><th>Type</th><th>Views</th><th>Likes</th><th>When</th></tr>" +
      videos.map(v => "<tr><td><a href='" + v.url + "' target='_blank'>" +
        esc(v.title.slice(0, 65)) + "</a></td><td>" + (v.short ? "Short" : "Long") +
        "</td><td>" + fmt(v.views) + "</td><td>" + fmt(v.likes) + "</td><td>" +
        v.published.slice(0, 10) + "</td></tr>").join("");

    socRender();
    ytLoaded = true;
  } catch (e) {
    err.textContent = e.message;
  }
}
function socSave() {
  const arr = JSON.parse(localStorage.getItem("social") || "[]");
  arr.unshift({ date: new Date().toISOString().slice(0, 10),
    platform: document.getElementById("soc-p").value,
    followers: +document.getElementById("soc-f").value || 0,
    views: +document.getElementById("soc-v").value || 0 });
  localStorage.setItem("social", JSON.stringify(arr.slice(0, 60)));
  socRender();
  toast("Saved 📱");
}
function socRender() {
  const arr = JSON.parse(localStorage.getItem("social") || "[]");
  document.getElementById("soc-table").innerHTML = arr.length
    ? "<tr><th>Date</th><th>Platform</th><th>Followers</th><th>Views</th></tr>" +
      arr.slice(0, 12).map(s => "<tr><td>" + s.date + "</td><td>" + s.platform +
        "</td><td>" + fmt(s.followers) + "</td><td>" + fmt(s.views) + "</td></tr>").join("")
    : "";
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
