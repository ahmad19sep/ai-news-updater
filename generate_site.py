"""
AI x Ahmad - Radar Studio site generator

Reads news.db and writes docs/index.html - published free on GitHub Pages.
The cloud server regenerates it every hour after fetching news.

Tabs (all client-side, no server, no API keys in the page):
  News      - audience-ranked "Video-worthy" view, local-angle badges
  Research  - papers tab for Ahmad's own learning (never video candidates)
  Planner   - Jira-style ticket board for the 2-person team (localStorage)
  Prep      - clipboard prompt buttons (Short/Long/Post Pack) + X generator
  Analytics - YouTube stats via the browser (key stays in localStorage)

Prompt templates live in docs/templates.js (separate, reusable later by a
Cloudflare Worker). Run manually:  python generate_site.py
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
<title>AI x Ahmad — Radar Studio</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:#0b0f17; --surface:#131a26; --surface2:#18202e;
    --text:#e7ecf3; --dim:#8b96a5; --faint:#5c6675;
    --line:rgba(255,255,255,.07); --line2:rgba(255,255,255,.12);
    --indigo:#6366f1; --cyan:#22d3ee; --gold:#fbbf24; --green:#34d399;
    --red:#f87171; --orange:#fb923c;
    --grad:linear-gradient(135deg,#6366f1 0%,#22d3ee 100%);
    --shadow:0 10px 30px -12px rgba(0,0,0,.55);
    --r:14px;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:radial-gradient(1200px 500px at 70% -10%, #141c30 0%, var(--bg) 55%);
         color:var(--text); font:14.5px/1.55 Inter, system-ui, "Segoe UI", sans-serif;
         -webkit-font-smoothing:antialiased; }
  ::selection { background:rgba(99,102,241,.35); }
  a { color:var(--cyan); }
  .wrap { max-width:1020px; margin:0 auto; padding:0 16px 80px; }

  header { position:sticky; top:0; z-index:50; backdrop-filter:blur(14px);
           background:rgba(11,15,23,.72); border-bottom:1px solid var(--line); }
  .hrow { max-width:1020px; margin:0 auto; padding:13px 16px;
          display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
  .logo { display:flex; align-items:center; gap:10px; font-weight:800;
          font-size:17px; letter-spacing:-.02em; }
  .logo .orb { width:11px; height:11px; border-radius:50%; background:var(--grad);
          box-shadow:0 0 14px rgba(34,211,238,.8); animation:pulse 2.4s infinite; }
  @keyframes pulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(.78);opacity:.7} }
  .logo small { font-weight:500; color:var(--faint); font-size:11px; margin-left:2px; }
  .tabs { display:flex; gap:4px; background:var(--surface); border:1px solid var(--line);
          padding:4px; border-radius:999px; margin-left:auto; }
  .tabs button { background:none; border:none; color:var(--dim); padding:7px 14px;
          border-radius:999px; font:600 13px Inter, sans-serif; cursor:pointer;
          transition:.18s; white-space:nowrap; }
  .tabs button:hover { color:var(--text); }
  .tabs button.active { background:var(--grad); color:#fff;
          box-shadow:0 4px 14px -4px rgba(99,102,241,.6); }
  .updated { width:100%; color:var(--faint); font-size:11.5px; }

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
  .pill.local { background:rgba(52,211,153,.14); color:var(--green); font-weight:600; }
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
  .col { min-width:262px; width:262px; flex-shrink:0; }
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
  .pcard textarea { width:100%; min-height:42px; font-size:12px; margin-top:8px;
          padding:7px 10px; border-radius:8px; }
  .pcard select, .pcard input[type=date] { font-size:11.5px; padding:5px 8px; border-radius:8px; }
  .pcard button { background:none; border:1px solid var(--line); color:var(--dim);
          border-radius:8px; padding:4px 10px; font:500 11.5px Inter; cursor:pointer; }
  .pcard button:hover { border-color:var(--indigo); color:var(--text); }
  .plats { display:flex; flex-wrap:wrap; gap:4px; margin-top:8px; }
  .plats label { font-size:10.5px; color:var(--dim); background:var(--surface2);
          border:1px solid var(--line); border-radius:6px; padding:2px 7px;
          cursor:pointer; user-select:none; }
  .plats label.on { color:#fff; background:rgba(99,102,241,.45); border-color:var(--indigo); }
  .ass { font-size:11px; padding:3px 8px; border-radius:6px; }
  .ass.ahmad { background:rgba(99,102,241,.2); color:#a5b4fc; }
  .ass.editor { background:rgba(251,191,36,.15); color:var(--gold); }
  .note { color:var(--faint); font-size:12px; margin:0 2px 14px; }

  .panel { background:var(--surface); border:1px solid var(--line);
          border-radius:var(--r); padding:20px 22px; margin-bottom:16px; }
  .panel h3 { margin:0 0 12px; font-size:14px; font-weight:700; color:var(--gold);
          display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
  .panel .sub { color:var(--faint); font-size:12px; margin:-6px 0 12px; }
  #promptbox { width:100%; min-height:260px; font:12px/1.6 Consolas, monospace; }
  .copied { color:var(--green); font-size:12.5px; }
  .genrow { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:6px; }
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
  @media (max-width:720px) {
    .tabs { margin-left:0; width:100%; justify-content:space-between; }
    .tabs button { padding:7px 8px; font-size:11.5px; }
  }
</style>
</head>
<body>
<header>
  <div class="hrow">
    <div class="logo"><span class="orb"></span> AI x Ahmad <small>RADAR STUDIO</small></div>
    <nav class="tabs">
      <button id="tabbtn-news" class="active" onclick="switchTab('news')">News</button>
      <button id="tabbtn-research" onclick="switchTab('research')">Research</button>
      <button id="tabbtn-plan" onclick="switchTab('plan')">Board</button>
      <button id="tabbtn-prep" onclick="switchTab('prep')">Prep</button>
      <button id="tabbtn-stats" onclick="switchTab('stats')">Analytics</button>
    </nav>
    <div class="updated">AI Ki Duniya, Simple Urdu Mein · @aixahmad · updated __UPDATED__ · refreshes hourly</div>
  </div>
</header>
<div class="wrap">

  <section id="tab-news">
    <div class="trends" id="trends"></div>
    <div class="bar" id="pillars"></div>
    <div class="search"><input id="q" placeholder="Search stories… Gemini, jobs, WhatsApp"></div>
    <div class="count" id="count"></div>
    <div id="list"></div>
    <button class="more" id="more" style="display:none">Show more</button>
  </section>

  <section id="tab-research" hidden>
    <p class="note">📚 Research papers — for your own learning. Never ranked as video candidates.</p>
    <div id="rlist"></div>
  </section>

  <section id="tab-plan" hidden>
    <div class="addrow">
      <input id="newidea" style="flex:1;min-width:200px" placeholder="New ticket (or tap 🎬 on any story)">
      <button class="btn" onclick="addIdea()">+ Ticket</button>
      <button class="ghost" onclick="exportPlans()">⬇ Export file</button>
      <button class="ghost" onclick="document.getElementById('importfile').click()">⬆ Import</button>
      <input type="file" id="importfile" accept=".json" hidden>
    </div>
    <div class="bar" id="assfilter"></div>
    <p class="note">Board saves in this browser. Export the file → send to your editor → he Imports it.</p>
    <div class="board" id="board"></div>
  </section>

  <section id="tab-prep" hidden>
    <div class="panel">
      <h3>🎬 Script &amp; Post generator</h3>
      <p class="sub">Fill the story, press a button — the complete prompt is copied. Paste it in your Claude app, paste the result back into your ticket notes.</p>
      <div class="genrow">
        <input id="preptitle" style="flex:1;min-width:200px" placeholder="Story / video topic">
        <input id="prepurl" style="flex:1;min-width:200px" placeholder="https://… source link">
      </div>
      <div class="genrow">
        <input id="prepsum" style="flex:1;min-width:200px" placeholder="Key point in one line (optional — Claude reads the link anyway)">
        <select id="prepdur">
          <option value="60">Short: 60 sec</option>
          <option value="45">Short: 45 sec</option>
          <option value="75">Short: 75 sec</option>
          <option value="120">Long-short: 2 min (rare big story)</option>
        </select>
      </div>
      <div class="genrow">
        <button class="btn" onclick="genPrompt('shortScript')">🎬 Short Script</button>
        <button class="btn" onclick="genPrompt('longScript')">📺 Long Script</button>
        <button class="btn" onclick="genPrompt('postPack')">📦 Post Pack</button>
        <span id="copyok" class="copied"></span>
      </div>
    </div>
    <div class="panel">
      <h3>💬 X engagement post</h3>
      <p class="sub">Reply-driving posts with real value. 3–4 per week, mixed with news posts. Each button copies a ready prompt.</p>
      <div class="genrow">
        <input id="xtopic" style="flex:1;min-width:220px" placeholder="Topic (default: AI aur rozmarra zindagi)">
      </div>
      <div class="genrow">
        <button class="ghost" onclick="genX('promptShare')">🎁 Prompt-share</button>
        <button class="ghost" onclick="genX('testAndTell')">⚔️ Test &amp; tell</button>
        <button class="ghost" onclick="genX('debateLocal')">🗣️ Local debate</button>
        <button class="ghost" onclick="genX('fillBlank')">✏️ Fill-the-blank</button>
      </div>
    </div>
    <div class="panel" id="prepout" hidden>
      <h3>Generated prompt <button class="ghost" style="padding:5px 14px;font-size:12px" onclick="copyPrompt()">📋 Copy again</button></h3>
      <textarea id="promptbox" readonly></textarea>
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
        <input id="yt-handle" style="width:100%;margin-bottom:12px" placeholder="Channel handle, e.g. @aixahmad">
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
        <select id="soc-p"><option>TikTok</option><option>Instagram</option><option>Facebook</option><option>X</option><option>WhatsApp</option><option>LinkedIn</option></select>
        <input id="soc-f" type="number" placeholder="followers" style="width:120px">
        <input id="soc-v" type="number" placeholder="views this week" style="width:150px">
        <button class="btn" onclick="socSave()">Save</button>
      </div>
      <div style="overflow-x:auto"><table id="soc-table"></table></div>
    </div>
  </section>
</div>
<div class="toast" id="toast"></div>

<script src="templates.js"></script>
<script>
const PILLARS = __PILLARS__;
const ITEMS = __ITEMS__;
const TRENDS = __TRENDS__;
const PAGE = 60;
const STATUSES = [["idea","💡 Idea"],["script","✍️ Script"],["filming","🎥 Filming"],
  ["editing","✂️ Editing"],["posted","✅ Posted"]];
const PLATFORMS = [["yt","YT long"],["shorts","Shorts"],["tiktok","TikTok"],["ig","IG Reels"],
  ["fb","FB Reels"],["x","X"],["wa","WhatsApp"],["li","LinkedIn"]];
let pillar = 0, hideDone = false, hotOnly = false, mode = "worthy", q = "", shown = PAGE;
let assFilter = "All";
const doneSet = new Set(JSON.parse(localStorage.getItem("done") || "[]"));
let plans = JSON.parse(localStorage.getItem("plans") || "[]");

/* migrate old planner cards to ticket format */
if (localStorage.getItem("plans_v") !== "2") {
  const map = { record: "filming", edit: "editing", uploaded: "posted", published: "posted" };
  plans = plans.map(p => ({
    id: p.id, title: p.title, url: p.url || "", notes: p.notes || "",
    status: p.status || map[p.stage] || p.stage || "idea",
    assignee: p.assignee || "Ahmad",
    platforms: p.platforms || (p.platform === "long" ? ["yt"] :
               p.platform === "short" ? ["shorts"] : ["yt", "shorts"]),
    due: p.due || p.date || "",
  }));
  localStorage.setItem("plans_v", "2");
  localStorage.setItem("plans", JSON.stringify(plans));
}

function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg; t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 1900);
}
function savePlans() { localStorage.setItem("plans", JSON.stringify(plans)); }
function switchTab(name) {
  ["news","research","plan","prep","stats"].forEach(n => {
    document.getElementById("tab-" + n).hidden = n !== name;
    document.getElementById("tabbtn-" + n).classList.toggle("active", n === name);
  });
  if (name === "plan") renderBoard();
  if (name === "research") renderResearch();
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

/* ---------------- News (audience-ranked) ---------------- */
function filtered() {
  const needle = q.toLowerCase();
  let items = ITEMS.filter(it =>
    it.p !== 9 &&
    (!pillar || it.p === pillar) &&
    (!hideDone || !doneSet.has(it.u)) &&
    (!hotOnly || (it.l && it.l.length)) &&
    (!needle || it.t.toLowerCase().includes(needle)));
  if (mode === "worthy") items = items.slice().sort((a, b) => b.sc - a.sc);
  return items;
}
function render() {
  const items = filtered();
  document.getElementById("count").textContent =
    items.length + " stories" + (q ? ' for "' + q + '"' : "") +
    (pillar ? " in " + PILLARS[pillar] : "") +
    (mode === "worthy" ? " · ranked by: should you film this today?" : " · newest first");
  const list = document.getElementById("list");
  list.innerHTML = items.length ? "" : '<div class="empty">No stories found.</div>';
  items.slice(0, shown).forEach(it => {
    const d = document.createElement("div");
    d.className = "card" + (doneSet.has(it.u) ? " done" : "");
    let extra = "", hot = "", local = "";
    if (it.l && it.l.length) {
      hot = '<span class="pill hot">🔥 ' + (it.l.length + 1) + " sources</span>";
      extra = '<div class="extra">also covered by: ' + it.l.map(x =>
        '<a href="' + esc(x.url) + '" target="_blank" rel="noopener">' + esc(x.source) + "</a>").join("") + "</div>";
    }
    if (it.lo) local = '<span class="pill local">🇵🇰🇮🇳 Local angle</span>';
    const why = (mode === "worthy" && it.sc >= 6 && it.r && it.r.length)
      ? '<div class="why">⭐ ' + it.sc + " — " + esc(it.r.join(" · ")) + "</div>" : "";
    d.innerHTML =
      '<h2><a href="' + esc(it.u) + '" target="_blank" rel="noopener">' + esc(it.t) + "</a></h2>" +
      '<div class="meta"><span class="pill">' + PILLARS[it.p] + "</span>" + local + hot +
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
      document.getElementById("preptitle").value = it.t;
      document.getElementById("prepurl").value = it.u;
      switchTab("prep");
      toast("Story loaded — pick a button 📝");
    };
    list.appendChild(d);
  });
  document.getElementById("more").style.display = items.length > shown ? "block" : "none";
}
function bar() {
  const el = document.getElementById("pillars");
  el.innerHTML = "";
  const worthy = document.createElement("button");
  worthy.innerHTML = "🎯 Video-worthy";
  worthy.className = "gold" + (mode === "worthy" ? " active" : "");
  worthy.onclick = () => { mode = "worthy"; shown = PAGE; bar(); render(); };
  el.appendChild(worthy);
  const latest = document.createElement("button");
  latest.innerHTML = "🕒 Latest";
  latest.className = mode === "latest" ? "active" : "";
  latest.onclick = () => { mode = "latest"; shown = PAGE; bar(); render(); };
  el.appendChild(latest);
  Object.entries(PILLARS).forEach(([k, v]) => {
    if (+k === 9) return;  // research lives in its own tab
    const b = document.createElement("button");
    b.textContent = v;
    b.className = +k === pillar ? "active" : "";
    b.onclick = () => { pillar = pillar === +k ? 0 : +k; shown = PAGE; bar(); render(); };
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

/* ---------------- Research tab ---------------- */
let researchDone = false;
function renderResearch() {
  if (researchDone) return;
  researchDone = true;
  const el = document.getElementById("rlist");
  const papers = ITEMS.filter(it => it.p === 9);
  el.innerHTML = papers.length ? "" : '<div class="empty">No papers yet.</div>';
  papers.forEach(it => {
    const d = document.createElement("div");
    d.className = "card";
    d.innerHTML = '<h2><a href="' + esc(it.u) + '" target="_blank" rel="noopener">' +
      esc(it.t) + '</a></h2><div class="meta"><span>' + esc(it.s) +
      "</span><span>" + ago(it.d) + "</span></div>";
    el.appendChild(d);
  });
}

/* ---------------- Ticket board ---------------- */
function addPlan(title, url) {
  plans.unshift({ id: Date.now(), title, url: url || "", notes: "",
    status: "idea", assignee: "Ahmad", platforms: ["yt", "shorts"], due: "" });
  savePlans();
  toast("Ticket created 🎬");
}
function addIdea() {
  const inp = document.getElementById("newidea");
  if (!inp.value.trim()) return;
  addPlan(inp.value.trim(), "");
  inp.value = "";
  renderBoard();
}
function assBar() {
  const el = document.getElementById("assfilter");
  el.innerHTML = "";
  ["All", "Ahmad", "Editor"].forEach(a => {
    const b = document.createElement("button");
    b.textContent = a === "All" ? "All tickets" : (a === "Ahmad" ? "🧑 Ahmad" : "✂️ Editor");
    b.className = assFilter === a ? "active" : "";
    b.onclick = () => { assFilter = a; renderBoard(); };
    el.appendChild(b);
  });
}
function renderBoard() {
  assBar();
  const board = document.getElementById("board");
  board.innerHTML = "";
  STATUSES.forEach(([key, label], si) => {
    const col = document.createElement("div");
    col.className = "col";
    const cards = plans.filter(p => p.status === key &&
      (assFilter === "All" || p.assignee === assFilter));
    col.innerHTML = "<h3>" + label + ' <span class="n">' + cards.length + "</span></h3>";
    cards.forEach(p => {
      const c = document.createElement("div");
      c.className = "pcard";
      c.innerHTML =
        '<div class="t">' + esc(p.title) + "</div>" +
        (p.url ? '<a href="' + esc(p.url) + '" target="_blank">source link</a>' : "") +
        '<div class="row">' +
        '<select class="ass-sel ass ' + (p.assignee === "Editor" ? "editor" : "ahmad") + '">' +
        ["Ahmad", "Editor"].map(a => '<option' + (p.assignee === a ? " selected" : "") + ">" + a + "</option>").join("") +
        '</select><input type="date" class="pdate" value="' + esc(p.due || "") + '"></div>' +
        '<div class="plats">' + PLATFORMS.map(([k, name]) =>
          '<label class="' + (p.platforms.includes(k) ? "on" : "") + '" data-k="' + k + '">' + name + "</label>").join("") + "</div>" +
        '<textarea class="pnotes" placeholder="notes / script paste…">' + esc(p.notes || "") + "</textarea>" +
        '<div class="row">' +
        (si > 0 ? '<button class="mv-prev">←</button>' : "") +
        (si < STATUSES.length - 1 ? '<button class="mv-next">→</button>' : "") +
        '<button class="do-prep" style="color:var(--gold)">📝 prep</button>' +
        '<button class="del">✕</button></div>';
      c.querySelector(".ass-sel").onchange = e => { p.assignee = e.target.value; savePlans(); renderBoard(); };
      c.querySelector(".pdate").onchange = e => { p.due = e.target.value; savePlans(); };
      c.querySelector(".pnotes").onchange = e => { p.notes = e.target.value; savePlans(); };
      c.querySelectorAll(".plats label").forEach(lab => {
        lab.onclick = () => {
          const k = lab.dataset.k;
          p.platforms = p.platforms.includes(k)
            ? p.platforms.filter(x => x !== k) : p.platforms.concat(k);
          savePlans();
          lab.classList.toggle("on");
        };
      });
      const prev = c.querySelector(".mv-prev");
      if (prev) prev.onclick = () => { p.status = STATUSES[si - 1][0]; savePlans(); renderBoard(); };
      const next = c.querySelector(".mv-next");
      if (next) next.onclick = () => { p.status = STATUSES[si + 1][0]; savePlans(); renderBoard(); };
      c.querySelector(".do-prep").onclick = () => {
        document.getElementById("preptitle").value = p.title;
        document.getElementById("prepurl").value = p.url;
        switchTab("prep");
        toast("Ticket loaded — pick a button 📝");
      };
      c.querySelector(".del").onclick = () => {
        if (confirm("Delete this ticket?")) {
          plans = plans.filter(x => x.id !== p.id); savePlans(); renderBoard();
        }
      };
      col.appendChild(c);
    });
    board.appendChild(col);
  });
}
function exportPlans() {
  const blob = new Blob([JSON.stringify(plans, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "aixahmad-board.json";
  a.click();
  toast("Board file downloaded — send it to your editor");
}
document.getElementById("importfile").addEventListener("change", e => {
  const f = e.target.files[0];
  if (!f) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const arr = JSON.parse(reader.result);
      if (Array.isArray(arr)) { plans = arr; savePlans(); renderBoard(); toast("Board imported ✓"); }
    } catch (err) { alert("That file is not a valid board export."); }
  };
  reader.readAsText(f);
});

/* ---------------- Prep: clipboard prompts ---------------- */
const COMMONW = new Set(["the","and","for","with","that","this","from","what",
  "how","why","new","its","has","have","are","was","will","can","you","your",
  "says","after","about","over","into","more","most"]);
function wordsOf(t) {
  return new Set((t.toLowerCase().match(/[a-z0-9]{3,}/g) || []).filter(w => !COMMONW.has(w)));
}
function relatedBlock(title, url) {
  const tw = wordsOf(title);
  const rel = [];
  for (const it of ITEMS) {
    if (it.u === url) continue;
    let common = 0;
    for (const w of wordsOf(it.t)) if (tw.has(w)) common++;
    if (common >= 2) rel.push([common, it]);
  }
  rel.sort((a, b) => b[0] - a[0]);
  if (!rel.length) return "";
  return "\n\nEXTRA SOURCES (optional, for more angles):\n" +
    rel.slice(0, 4).map(r => "- " + r[1].t + " — " + r[1].u).join("\n");
}
function fillTemplate(tpl, vars) {
  return tpl.replace(/\{(\w+)\}/g, (m, k) => (vars[k] !== undefined ? vars[k] : m));
}
function showAndCopy(prompt, okMsg) {
  document.getElementById("promptbox").value = prompt;
  document.getElementById("prepout").hidden = false;
  navigator.clipboard.writeText(prompt)
    .then(() => { toast(okMsg); document.getElementById("copyok").textContent = "✓ copied"; });
}
function genPrompt(kind) {
  const title = document.getElementById("preptitle").value.trim();
  const url = document.getElementById("prepurl").value.trim();
  if (!title && !url) { toast("Add a story title or link first"); return; }
  const vars = {
    title: title || url,
    url: url || "(no link — explain from the summary)",
    summary: document.getElementById("prepsum").value.trim() || "(read the link for details)",
    duration: document.getElementById("prepdur").value,
  };
  let prompt = fillTemplate(window.TEMPLATES[kind], vars);
  if (kind !== "postPack") prompt += relatedBlock(vars.title, url);
  showAndCopy(prompt, "Prompt copied — paste in Claude 🤖");
}
function genX(format) {
  const topic = document.getElementById("xtopic").value.trim() ||
    "AI aur rozmarra zindagi (daily life, jobs, paisa)";
  const prompt = fillTemplate(window.TEMPLATES.xFormats[format], { topic });
  showAndCopy(prompt, "X post prompt copied 💬");
}
function copyPrompt() {
  navigator.clipboard.writeText(document.getElementById("promptbox").value)
    .then(() => toast("Copied again 📋"));
}

/* ---------------- Analytics ---------------- */
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
    const snaps = JSON.parse(localStorage.getItem("yt_snaps") || "{}");
    const today = new Date().toISOString().slice(0, 10);
    snaps[today] = { subs, views };
    localStorage.setItem("yt_snaps", JSON.stringify(snaps));
    const firstDay = Object.keys(snaps).sort()[0];
    const growth = firstDay !== today
      ? { subs: subs - snaps[firstDay].subs, views: views - snaps[firstDay].views, since: firstDay }
      : null;
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
    let bestDay = "", bestAvg = -1;
    for (const [d, arr] of Object.entries(wd)) {
      const avg = arr.reduce((a, b) => a + b, 0) / arr.length;
      if (avg > bestAvg) { bestAvg = avg; bestDay = d; }
    }
    const sEl = document.getElementById("yt-stats");
    sEl.innerHTML = "";
    [[fmt(subs), "subscribers", growth ? "+" + fmt(growth.subs) + " since " + growth.since : ""],
     [fmt(views), "total views", growth ? "+" + fmt(growth.views) : ""],
     [vidn, "videos", ""],
     [daysSince === null ? "—" : daysSince, "days since upload", ""]].forEach(([n, l, g]) => {
      sEl.innerHTML += '<div class="stat"><div class="n">' + n + '</div><div class="l">' +
        l + "</div>" + (g ? '<div class="g">' + g + "</div>" : "") + "</div>";
    });
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
    document.getElementById("yt-weeks").innerHTML =
      perWeek.map(n => '<div style="height:' + (6 + n * 14) + 'px" title="' + n + ' uploads"></div>').join("");
    document.getElementById("yt-weeks-l").innerHTML =
      perWeek.map(n => "<span>" + n + "</span>").join("");
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
    hot_terms = scoring.rising_terms(trends)[:15]
    conn.close()

    now = datetime.now(timezone.utc)
    items = []
    for r in rows:
        links = json.loads(r["links"] or "[]")
        when = r["published"] or r["fetched"]
        try:
            age_h = (now - datetime.fromisoformat(when)).total_seconds() / 3600
        except ValueError:
            age_h = 999
        score, reasons, local = scoring.audience_score(
            r["title"], r["pillar"], len(links), age_h, hot_terms)
        items.append({
            "t": r["title"], "u": r["url"], "s": r["source"], "p": r["pillar"],
            "d": when, "l": links,
            "sc": score, "r": reasons, "lo": local,
        })

    updated = now.strftime("%d %b %Y, %H:%M UTC")
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
