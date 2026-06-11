"""
AI x Ahmad - Radar Studio site generator

Reads news.db and writes docs/index.html - published free on GitHub Pages.
The cloud server regenerates it every hour after fetching news.

Design: light, clean SaaS look (Notion/Asana style). Tabs:
  News      - audience-ranked "Video-worthy" view, local-angle badges
  Trends    - rising model/tool names week over week
  Research  - papers tab for Ahmad's own learning
  Board     - Asana-style ticket board: drag & drop, ticket modal, avatars
  Prep      - clipboard prompt buttons (Short/Long/Post Pack) + X generator

Access gate: SHA-256 hash of the code is embedded; the code itself comes
from the SITE_PASSCODE secret (cloud) or site_passcode.txt (local, gitignored).
Prompt templates live in docs/templates.js. Run manually: python generate_site.py
"""

import hashlib
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
<meta name="theme-color" content="#ffffff">
<title>AI x Ahmad — Radar Studio</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700;12..96,800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:#ffffff; --surface:#ffffff; --surface2:#f5f6f4;
    --text:#1d2025; --dim:#5f6671; --faint:#979ea8;
    --line:#e9eaec; --line2:#d8dadd;
    --indigo:#6366f1; --indigo-soft:#eef0fe; --cyan:#06b6d4;
    --cta:#a5e573; --cta-dark:#16321a; --cta-hover:#93dd5c;
    --gold:#b45309; --gold-soft:#fef3c7;
    --green:#059669; --green-soft:#ecfdf5;
    --red:#dc2626; --red-soft:#fee2e2;
    --orange:#c2410c; --orange-soft:#ffedd5;
    --purple:#7c3aed; --purple-soft:#f3e8ff;
    --blue:#2563eb; --blue-soft:#dbeafe;
    --shadow-sm:0 1px 2px rgba(16,24,40,.06);
    --shadow:0 4px 16px -4px rgba(16,24,40,.12);
    --shadow-lg:0 20px 50px -12px rgba(16,24,40,.25);
    --r:12px;
    --display:"Bricolage Grotesque", Inter, system-ui, sans-serif;
  }
  * { box-sizing:border-box; }
  [hidden] { display:none !important; }
  body { margin:0; background:var(--bg); color:var(--text);
         font:14px/1.55 Inter, system-ui, "Segoe UI", sans-serif;
         -webkit-font-smoothing:antialiased; }
  a { color:var(--indigo); }
  .wrap { max-width:1080px; margin:0 auto; padding:0 20px 80px; }

  /* ---------- header ---------- */
  header { position:sticky; top:0; z-index:50; background:rgba(255,255,255,.85);
           backdrop-filter:blur(12px); border-bottom:1px solid var(--line); }
  .hrow { max-width:1080px; margin:0 auto; padding:12px 20px;
          display:flex; align-items:center; gap:16px; flex-wrap:wrap; }
  .logo { display:flex; align-items:center; gap:9px; font-weight:800;
          font-size:17px; letter-spacing:-.02em; font-family:var(--display); }
  .logo .orb { width:28px; height:28px; border-radius:9px;
          background:linear-gradient(135deg,#6366f1,#06b6d4);
          display:flex; align-items:center; justify-content:center;
          color:#fff; font-size:14px; font-weight:800; }
  .logo small { font-weight:600; color:var(--faint); font-size:10.5px;
          font-family:Inter; letter-spacing:.06em; }
  .tabs { display:flex; gap:2px; margin-left:auto; }
  .tabs button { background:none; border:none; color:var(--dim); padding:9px 15px;
          border-radius:999px; font:600 13.5px Inter; cursor:pointer; transition:.15s; }
  .tabs button:hover { background:var(--surface2); color:var(--text); }
  .tabs button.active { background:var(--text); color:#fff; }

  /* ---------- home dashboard ---------- */
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }
  .live { display:inline-block; width:8px; height:8px; border-radius:50%;
          background:#22c55e; box-shadow:0 0 0 3px rgba(34,197,94,.2);
          animation:pulse 2s infinite; }
  .homedate { color:var(--dim); font-size:13px; margin:22px 2px 14px;
          display:flex; align-items:center; gap:9px; }
  .toppick .picktag { color:var(--dim); font:600 12px Inter; display:block;
          margin-bottom:8px; }
  .toppick h2 { font-family:var(--display); font-size:clamp(19px, 3vw, 26px);
          font-weight:700; letter-spacing:-.02em; line-height:1.3; margin:0 0 14px; }
  .toppick h2 a { color:var(--text); text-decoration:none; }
  .toppick h2 a:hover { color:var(--indigo); }
  .pickrow { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
  .badge { border-radius:999px; padding:3.5px 12px; font:600 11.5px Inter; }
  .badge.score { background:var(--gold-soft); color:var(--gold); }
  .badge.localb { background:var(--green-soft); color:var(--green); }
  .badge.src { background:var(--indigo-soft); color:var(--indigo); }
  .pickrow .btn { margin-left:auto; }
  .statgrid { display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr));
          gap:12px; margin:14px 0; }
  .scard { background:var(--surface); border:1px solid var(--line);
          border-radius:14px; padding:16px 18px; box-shadow:var(--shadow-sm); }
  .scard .l { color:var(--dim); font-size:12px; font-weight:500; margin-bottom:4px; }
  .scard .n { font-family:var(--display); font-size:26px; font-weight:800;
          letter-spacing:-.02em; }
  .scard .n.orange { color:var(--orange); } .scard .n.green { color:var(--green); }
  .scard .n.indigo { color:var(--indigo); }
  .homecols { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
  @media (max-width:720px) { .homecols { grid-template-columns:1fr; } }
  .pipe { display:flex; align-items:center; gap:9px; padding:10px 2px;
          border-bottom:1px solid var(--line); cursor:pointer; font-size:13px; }
  .pipe:last-child { border-bottom:none; }
  .pipe:hover { background:var(--surface2); border-radius:8px; }
  .pipe .st { font-size:10.5px; font-weight:600; color:var(--dim);
          background:var(--surface2); border:1px solid var(--line);
          border-radius:5px; padding:1.5px 7px; flex-shrink:0; }
  .pipe .who { margin-left:auto; font-weight:600; font-size:12px; flex-shrink:0; }
  .pipe .who.ahmad { color:var(--indigo); } .pipe .who.editor { color:#d97706; }
  .qa { display:block; width:100%; text-align:left; background:var(--surface);
          border:1px solid var(--line); color:var(--text); border-radius:10px;
          padding:13px 16px; font:500 13.5px Inter; cursor:pointer;
          margin-bottom:10px; transition:.15s; }
  .qa:hover { border-color:var(--cta); background:#f7fdf2; }
  .updated { width:100%; color:var(--faint); font-size:11px; }

  /* ---------- controls ---------- */
  .search { display:flex; gap:10px; margin:20px 0 4px; }
  .search input { flex:1; background:var(--surface); border:1px solid var(--line);
          color:var(--text); padding:10px 16px; border-radius:var(--r); font:14px Inter;
          outline:none; transition:.15s; box-shadow:var(--shadow-sm); }
  .search input:focus { border-color:var(--indigo); box-shadow:0 0 0 3px var(--indigo-soft); }
  .bar { display:flex; flex-wrap:wrap; gap:8px; margin:14px 0; align-items:center; }
  .bar button { background:var(--surface); color:var(--dim); border:1px solid var(--line);
          padding:6px 13px; border-radius:999px; font:500 12.5px Inter;
          cursor:pointer; transition:.15s; box-shadow:var(--shadow-sm); }
  .bar button:hover { border-color:var(--line2); color:var(--text); }
  .bar button.active { background:var(--text); border-color:var(--text); color:#fff; font-weight:600; }
  .bar button.gold.active { background:var(--cta); border-color:var(--cta); color:var(--cta-dark); }
  .bar select { background:var(--surface); border:1px solid var(--line); color:var(--dim);
          padding:6px 12px; border-radius:999px; font:500 12.5px Inter; outline:none;
          box-shadow:var(--shadow-sm); }
  .count { color:var(--faint); font-size:12.5px; margin:8px 2px 14px; }

  /* ---------- story cards ---------- */
  .card { background:var(--surface); border:1px solid var(--line); border-radius:var(--r);
          padding:15px 18px; margin-bottom:10px; transition:.15s; box-shadow:var(--shadow-sm); }
  .card:hover { box-shadow:var(--shadow); border-color:var(--line2); }
  .card.done { opacity:.45; }
  .card h2 { font-size:14.5px; font-weight:600; margin:0 0 8px; line-height:1.45;
          letter-spacing:-.01em; }
  .card h2 a { color:var(--text); text-decoration:none; }
  .card h2 a:hover { color:var(--indigo); }
  .meta { font-size:12px; color:var(--dim); display:flex; flex-wrap:wrap;
          gap:6px 12px; align-items:center; }
  .pill { background:var(--indigo-soft); color:var(--indigo); padding:2px 9px;
          border-radius:999px; font-weight:500; font-size:11px; }
  .pill.hot { background:var(--orange-soft); color:var(--orange); }
  .pill.local { background:var(--green-soft); color:var(--green); font-weight:600; }
  .actions { margin-left:auto; display:flex; gap:5px; }
  .meta button { background:none; border:1px solid var(--line); color:var(--dim);
          border-radius:7px; padding:3.5px 10px; font:500 11.5px Inter; cursor:pointer;
          transition:.15s; }
  .meta button:hover { border-color:var(--indigo); color:var(--indigo);
          background:var(--indigo-soft); }
  .extra { font-size:12px; margin-top:7px; color:var(--dim); }
  .extra a { text-decoration:none; margin-right:12px; }
  .why { font-size:11.5px; color:var(--gold); margin-top:7px; }
  .more { display:block; margin:22px auto; background:var(--surface); color:var(--dim);
          border:1px solid var(--line); padding:10px 32px; border-radius:999px;
          font:600 13px Inter; cursor:pointer; transition:.15s; box-shadow:var(--shadow-sm); }
  .more:hover { color:var(--indigo); border-color:var(--indigo); }
  .empty { color:var(--faint); text-align:center; padding:60px 0; }
  .note { color:var(--faint); font-size:12.5px; margin:16px 2px 14px; }

  /* ---------- trends ---------- */
  .trends { display:flex; flex-wrap:wrap; gap:8px; margin:6px 0; }
  .chip { display:inline-flex; align-items:center; gap:6px; background:var(--green-soft);
          color:var(--green); border:1px solid #bbe7d2; padding:6px 14px;
          border-radius:999px; font:500 12.5px Inter; cursor:pointer; transition:.15s; }
  .chip:hover { box-shadow:var(--shadow-sm); transform:translateY(-1px); }
  .chip small { opacity:.65; font-weight:400; }

  /* ---------- inputs & buttons ---------- */
  input, select, textarea { background:var(--surface); border:1px solid var(--line);
          color:var(--text); padding:9px 13px; border-radius:var(--r); font:13.5px Inter;
          outline:none; transition:.15s; }
  input:focus, textarea:focus, select:focus { border-color:var(--indigo);
          box-shadow:0 0 0 3px var(--indigo-soft); }
  .btn { background:var(--cta); border:none; color:var(--cta-dark); padding:10px 20px;
          border-radius:999px; font:700 13px Inter; cursor:pointer; transition:.15s; }
  .btn:hover { background:var(--cta-hover); box-shadow:var(--shadow); }
  .ghost { background:var(--surface); color:var(--dim); border:1px solid var(--line);
          padding:9px 16px; border-radius:999px; font:500 13px Inter; cursor:pointer;
          transition:.15s; }
  .ghost:hover { color:var(--text); border-color:var(--line2); box-shadow:var(--shadow-sm); }
  .addrow { display:flex; gap:10px; margin:20px 0 10px; flex-wrap:wrap; }

  /* ---------- publish board (Buffer style) ---------- */
  .avatar { width:22px; height:22px; border-radius:50%; font-size:10.5px; font-weight:700;
          display:inline-flex; align-items:center; justify-content:center; color:#fff;
          flex-shrink:0; }
  .avatar.ahmad { background:var(--indigo); }
  .avatar.editor { background:#f59e0b; }
  .tag { font-size:10px; font-weight:600; color:var(--dim); background:var(--surface2);
          border:1px solid var(--line); border-radius:5px; padding:1.5px 6px; }
  .qday { font:700 12px Inter; color:var(--faint); text-transform:uppercase;
          letter-spacing:.07em; margin:20px 2px 8px; }
  .qrow { display:flex; align-items:center; gap:10px; background:var(--surface);
          border:1px solid var(--line); border-radius:12px; padding:13px 16px;
          margin-bottom:8px; cursor:pointer; transition:.15s; box-shadow:var(--shadow-sm); }
  .qrow:hover { box-shadow:var(--shadow); border-color:var(--line2); }
  .qtime { font:700 12.5px Inter; color:var(--indigo); width:46px; flex-shrink:0; }
  .qtext { font-weight:500; font-size:13.5px; flex:1; min-width:0; overflow:hidden;
          text-overflow:ellipsis; white-space:nowrap; }
  .qtags { display:flex; gap:4px; flex-shrink:0; }
  .ideagrid { display:grid; grid-template-columns:repeat(auto-fill, minmax(230px, 1fr));
          gap:12px; }
  .ideacard { background:var(--surface); border:1px solid var(--line); border-radius:12px;
          padding:14px 16px; box-shadow:var(--shadow-sm); transition:.15s; }
  .ideacard:hover { box-shadow:var(--shadow); }
  .ideacard .t { font-weight:600; font-size:13px; line-height:1.4; margin-bottom:6px; }
  .ideacard a { font-size:11.5px; }
  .calhead { display:flex; align-items:center; gap:10px; margin:16px 0 12px; }
  .calhead b { font-family:var(--display); font-size:16px; }
  .calhead .ghost { padding:6px 13px; }
  .calgrid { display:grid; grid-template-columns:repeat(7, 1fr); gap:8px; }
  @media (max-width:860px) { .calgrid { grid-template-columns:repeat(2, 1fr); } }
  .calcell { background:var(--surface); border:1px solid var(--line); border-radius:12px;
          padding:10px; min-height:130px; display:flex; flex-direction:column; gap:5px; }
  .calcell.today { border-color:var(--cta); box-shadow:0 0 0 2px #e3f7d2; }
  .calcell .cd { font:700 11.5px Inter; color:var(--dim); margin-bottom:2px; }
  .calcell.today .cd { color:var(--green); }
  .calpost { font:500 10.5px Inter; border-radius:6px; padding:4px 7px; cursor:pointer;
          overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .calpost.scheduled { background:var(--indigo-soft); color:var(--indigo); }
  .calpost.draft { background:var(--gold-soft); color:var(--gold); }
  .calpost.posted { background:var(--green-soft); color:var(--green); }
  .calplus { margin-top:auto; background:none; border:none; color:var(--faint);
          font-size:15px; cursor:pointer; border-radius:6px; padding:2px; }
  .calplus:hover { background:var(--surface2); color:var(--indigo); }
  .tplgrid { display:grid; grid-template-columns:repeat(auto-fill, minmax(225px, 1fr));
          gap:12px; margin-bottom:18px; }
  .tplcard { background:var(--surface); border:1px solid var(--line); border-radius:14px;
          padding:18px 16px 14px; cursor:pointer; transition:.15s;
          box-shadow:var(--shadow-sm); display:flex; flex-direction:column; gap:6px;
          align-items:flex-start; }
  .tplcard:hover { box-shadow:var(--shadow); border-color:var(--cta);
          transform:translateY(-2px); }
  .tplcard .te { font-size:26px; }
  .tplcard .tn { font-family:var(--display); font-weight:700; font-size:14.5px;
          line-height:1.3; }
  .tplcard .td { color:var(--dim); font-size:12px; line-height:1.5; flex:1; }

  /* ---------- ticket modal ---------- */
  #modal { position:fixed; inset:0; z-index:300; background:rgba(15,23,42,.35);
          display:flex; align-items:center; justify-content:center; padding:18px; }
  .mbox { background:var(--surface); border-radius:16px; box-shadow:var(--shadow-lg);
          width:min(520px, 96vw); max-height:92vh; overflow-y:auto; padding:26px 26px 22px; }
  .mbox input[type=text], .mbox textarea { width:100%; }
  .mbox .mtitle { font-size:15px; font-weight:700; border:none; padding:4px 2px;
          box-shadow:none; }
  .mbox .mtitle:focus { box-shadow:none; border:none; }
  .mrow { display:flex; align-items:center; gap:10px; margin:12px 0; flex-wrap:wrap; }
  .mrow .lbl { width:84px; color:var(--faint); font-size:12px; font-weight:600;
          flex-shrink:0; }
  .mplats { display:flex; flex-wrap:wrap; gap:6px; }
  .mplats label { font-size:11.5px; font-weight:500; color:var(--dim);
          background:var(--surface2); border:1px solid var(--line); border-radius:999px;
          padding:4px 11px; cursor:pointer; user-select:none; transition:.12s; }
  .mplats label.on { color:#fff; background:var(--indigo); border-color:var(--indigo); }
  .mfoot { display:flex; gap:8px; margin-top:18px; }
  .danger { background:none; border:1px solid var(--line); color:var(--red);
          padding:9px 14px; border-radius:var(--r); font:500 12.5px Inter; cursor:pointer; }
  .danger:hover { background:var(--red-soft); border-color:var(--red); }

  /* ---------- prep panels ---------- */
  .panel { background:var(--surface); border:1px solid var(--line);
          border-radius:14px; padding:22px 24px; margin-bottom:16px;
          box-shadow:var(--shadow-sm); }
  .panel h3 { margin:0 0 6px; font-size:14px; font-weight:700;
          display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
  .panel .sub { color:var(--faint); font-size:12.5px; margin:0 0 14px; }
  .genrow { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:10px; }
  #promptbox { width:100%; min-height:260px; font:12px/1.6 Consolas, monospace;
          background:var(--surface2); }
  .copied { color:var(--green); font-size:12.5px; }
  .err { color:var(--red); font-size:13px; margin:8px 0; }

  /* ---------- lock ---------- */
  #lock { position:fixed; inset:0; z-index:400; background:var(--bg);
          display:flex; align-items:center; justify-content:center; }
  .lockbox { background:var(--surface); border:1px solid var(--line);
          border-radius:18px; padding:38px 34px; width:min(360px, 90vw);
          text-align:center; box-shadow:var(--shadow-lg); }
  .lockbox .orb { width:44px; height:44px; border-radius:12px;
          background:linear-gradient(135deg,#6366f1,#06b6d4); color:#fff;
          font-size:20px; font-weight:800; display:flex; align-items:center;
          justify-content:center; margin:0 auto 16px; }
  .lockbox h2 { font-size:18px; margin:0 0 4px; font-family:var(--display); }
  .lockbox p { color:var(--faint); font-size:12.5px; margin:0 0 18px; }
  .lockbox input { width:100%; text-align:center; letter-spacing:.08em; margin-bottom:12px; }

  .toast { position:fixed; bottom:24px; left:50%; transform:translateX(-50%) translateY(8px);
          background:var(--text); color:#fff; padding:10px 24px; border-radius:999px;
          font:600 12.5px Inter; opacity:0; transition:.25s; pointer-events:none;
          box-shadow:var(--shadow-lg); z-index:500; }
  .toast.show { opacity:1; transform:translateX(-50%) translateY(0); }
  @media (max-width:720px) {
    .tabs { margin-left:0; width:100%; }
    .tabs button { padding:8px 9px; font-size:12px; flex:1; }
  }
</style>
</head>
<body>
<div id="lock" hidden>
  <div class="lockbox">
    <div class="orb">A</div>
    <h2>AI x Ahmad — Radar Studio</h2>
    <p>Private studio. Enter your access code.</p>
    <div class="err" id="lockerr"></div>
    <input id="lockcode" type="password" placeholder="access code" autocomplete="off">
    <button class="btn" style="width:100%" onclick="tryUnlock()">Enter</button>
  </div>
</div>
<header>
  <div class="hrow">
    <div class="logo"><span class="orb">A</span> AI x Ahmad <small>RADAR STUDIO</small></div>
    <nav class="tabs">
      <button id="tabbtn-home" class="active" onclick="switchTab('home')">Home</button>
      <button id="tabbtn-news" onclick="switchTab('news')">News</button>
      <button id="tabbtn-trends" onclick="switchTab('trends')">Trends</button>
      <button id="tabbtn-research" onclick="switchTab('research')">Research</button>
      <button id="tabbtn-plan" onclick="switchTab('plan')">Buffer</button>
      <button id="tabbtn-prep" onclick="switchTab('prep')">Prep</button>
    </nav>
    <div class="updated">The World of AI, in Simple Urdu · @aixahmad</div>
  </div>
</header>
<div class="wrap">

  <section id="tab-home">
    <p class="homedate" id="homedate"><span class="live"></span> <span id="homedatetxt"></span></p>
    <div class="panel toppick" id="toppick"></div>
    <div class="statgrid" id="statgrid"></div>
    <div class="homecols">
      <div class="panel">
        <h3>📋 This week's pipeline</h3>
        <div id="pipeline"></div>
      </div>
      <div class="panel">
        <h3>⚡ Quick actions</h3>
        <button class="qa" onclick="qaShort()">🎬 Generate short script</button>
        <button class="qa" onclick="qaX()">💬 New X engagement post</button>
        <button class="qa" onclick="qaNews()">🎯 Open video-worthy list</button>
      </div>
    </div>
  </section>

  <section id="tab-news" hidden>
    <div class="search" style="margin-top:20px"><input id="q" placeholder="Search stories… Gemini, jobs, WhatsApp"></div>
    <div class="bar" id="pillars"></div>
    <div class="count" id="count"></div>
    <div id="list"></div>
    <button class="more" id="more" style="display:none">Show more</button>
  </section>

  <section id="tab-trends" hidden>
    <p class="note">🚀 Which models and tools are rising this week vs last week — your early-warning
       radar for the next big thing. Tap any chip to see its stories.</p>
    <div class="trends" id="trends"></div>
  </section>

  <section id="tab-research" hidden>
    <p class="note">📚 Research papers — for your own learning. Never ranked as video candidates.</p>
    <div id="rlist"></div>
  </section>

  <section id="tab-plan" hidden>
    <div class="addrow" style="align-items:center">
      <div class="bar" id="boardnav" style="margin:0"></div>
      <button class="btn" style="margin-left:auto" onclick="openComposer(null)">+ New post</button>
      <button class="ghost" onclick="exportPlans()">⬇</button>
      <button class="ghost" onclick="document.getElementById('importfile').click()">⬆</button>
      <input type="file" id="importfile" accept=".json" hidden>
    </div>
    <div id="boardview"></div>
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
</div>

<div id="modal" hidden>
  <div class="mbox">
    <div class="mrow" style="margin-top:0"><span class="lbl">Channels</span>
      <span class="mplats" id="m-plats"></span></div>
    <textarea id="m-title" style="width:100%;min-height:120px;font-size:14px"
      placeholder="Write your post / video title… (ya template chuno 👇)"></textarea>
    <div class="mrow"><span class="lbl">Template</span>
      <select id="m-tpl" style="flex:1"><option value="">— plug &amp; play template —</option></select></div>
    <div class="mrow"><span class="lbl">Link</span>
      <input type="text" id="m-url" style="flex:1" placeholder="https://… story or video link (optional)"></div>
    <div class="mrow"><span class="lbl">Schedule</span>
      <input type="date" id="m-date"><input type="time" id="m-time" value="18:00">
      <select id="m-status">
        <option value="idea">💡 Idea</option><option value="draft">📝 Draft</option>
        <option value="scheduled">🗓 Scheduled</option><option value="posted">✅ Posted</option>
      </select></div>
    <div class="mrow"><span class="lbl">Owner</span>
      <select id="m-ass"><option>Ahmad</option><option>Editor</option></select></div>
    <div class="mrow" style="align-items:flex-start"><span class="lbl">Notes</span>
      <textarea id="m-notes" style="flex:1;min-height:70px"
        placeholder="script paste, b-roll list, instructions for editor…"></textarea></div>
    <div class="mfoot">
      <button class="btn" onclick="closeModal()">Save</button>
      <button class="ghost" onclick="modalPrep()">🤖 Write with Claude</button>
      <button class="danger" style="margin-left:auto" onclick="modalDelete()">Delete</button>
    </div>
  </div>
</div>
<div class="toast" id="toast"></div>

<script src="templates.js"></script>
<script>
/* ---- access gate (light protection - keeps casual visitors out) ---- */
const LOCKHASH = "__LOCKHASH__";
async function sha256(t) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t));
  return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join("");
}
async function tryUnlock() {
  const code = document.getElementById("lockcode").value.trim();
  if (await sha256(code) === LOCKHASH) {
    localStorage.setItem("unlock", LOCKHASH);
    document.getElementById("lock").hidden = true;
  } else {
    document.getElementById("lockerr").textContent = "Wrong code - try again.";
  }
}
if (LOCKHASH && localStorage.getItem("unlock") !== LOCKHASH) {
  document.getElementById("lock").hidden = false;
  setTimeout(() => {
    document.getElementById("lockcode").addEventListener("keydown",
      e => { if (e.key === "Enter") tryUnlock(); });
  }, 0);
}

const PILLARS = __PILLARS__;
const ITEMS = __ITEMS__;
const TRENDS = __TRENDS__;
const PAGE = 60;
const STATUSES = [
  ["idea", "Idea", "#94a3b8"], ["script", "Script", "#2563eb"],
  ["filming", "Filming", "#c2410c"], ["editing", "Editing", "#7c3aed"],
  ["posted", "Posted", "#059669"]];
const PLATFORMS = [["yt","YT long"],["shorts","Shorts"],["tiktok","TikTok"],["ig","IG Reels"],
  ["fb","FB Reels"],["x","X"],["wa","WhatsApp"],["li","LinkedIn"]];
let pillar = 0, hideDone = false, hotOnly = false, mode = "worthy", q = "", shown = PAGE;
let assFilter = "All", editingId = null;
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
if (localStorage.getItem("plans_v") !== "3") {
  plans = plans.map(p => ({
    id: p.id, title: p.title, url: p.url || "", notes: p.notes || "",
    status: ({script:"draft",filming:"draft",editing:"draft"})[p.status] || p.status || "idea",
    assignee: p.assignee || "Ahmad",
    platforms: p.platforms || ["yt","shorts"],
    when: p.when || (p.due ? p.due + "T18:00" : ""),
  }));
  localStorage.setItem("plans_v", "3");
  localStorage.setItem("plans", JSON.stringify(plans));
}

function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg; t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 1900);
}
function savePlans() { localStorage.setItem("plans", JSON.stringify(plans)); }
function switchTab(name) {
  ["home","news","trends","research","plan","prep"].forEach(n => {
    document.getElementById("tab-" + n).hidden = n !== name;
    document.getElementById("tabbtn-" + n).classList.toggle("active", n === name);
  });
  if (name === "home") renderHome();
  if (name === "plan") renderBoard();
  if (name === "research") renderResearch();
}
function ago(iso) {
  if (!iso) return "";
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 3600) return Math.max(1, s/60|0) + " min ago";
  if (s < 86400) return (s/3600|0) + "h ago";
  return (s/86400|0) + "d ago";
}
function esc(t) { const d = document.createElement("div"); d.textContent = t; return d.innerHTML; }

/* ---------------- News ---------------- */
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
    d.querySelector(".plan-btn").onclick = () => { addPlan(it.t, it.u); };
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
  const sel = document.createElement("select");
  sel.innerHTML = '<option value="0">All categories</option>' +
    Object.entries(PILLARS).filter(([k]) => +k !== 9).map(([k, v]) =>
      '<option value="' + k + '"' + (+k === pillar ? " selected" : "") + ">" + v + "</option>").join("");
  sel.onchange = e => { pillar = +e.target.value; shown = PAGE; render(); };
  el.appendChild(sel);
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
      shown = PAGE; switchTab("news"); render();
    };
    el.appendChild(c);
  });
}

/* ---------------- Research ---------------- */
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

/* ---------------- Publish board (Buffer style) ---------------- */
let boardView = "queue", calOffset = 0;

function addPlan(title, url) {
  plans.unshift({ id: Date.now(), title, url: url || "", notes: "",
    status: "idea", assignee: "Ahmad", platforms: ["yt", "shorts"], when: "" });
  savePlans();
  toast("Saved to Ideas 💡");
}

function boardNav() {
  const el = document.getElementById("boardnav");
  el.innerHTML = "";
  [["queue","🗓 Queue"],["calendar","📅 Calendar"],["drafts","📝 Drafts"],
   ["ideas","💡 Ideas"],["templates","🧩 Templates"],["posted","✅ Posted"]].forEach(([k, label]) => {
    const b = document.createElement("button");
    b.innerHTML = label;
    b.className = boardView === k ? "active" : "";
    b.onclick = () => { boardView = k; renderBoard(); };
    el.appendChild(b);
  });
}

function renderBoard() {
  boardNav();
  const el = document.getElementById("boardview");
  el.innerHTML = "";
  if (boardView === "queue") renderQueue(el);
  else if (boardView === "calendar") renderCalendar(el);
  else if (boardView === "drafts") renderList(el, ["draft"], "No drafts yet. Turn an idea into a draft, or press + New post.");
  else if (boardView === "ideas") renderIdeas(el);
  else if (boardView === "templates") renderTemplates(el);
  else renderList(el, ["posted"], "Nothing posted yet — your history will appear here.");
}

/* ---- Templates gallery (Buffer "Create > Templates" style) ---- */
let tplCat = "All", tplLang = localStorage.getItem("tpl_lang") || "ur";
let tplTopic = "", tplCurrent = null, tplPlat = "all";
const TPL_PLATS = [
  ["all", "🌐 All platforms"], ["shorts", "🎬 Short/Reel/TikTok"], ["yt", "📺 YouTube"],
  ["x", "𝕏 X"], ["igfb", "📸 IG + FB"], ["li", "💼 LinkedIn"], ["wa", "💬 WhatsApp"]];
const TPL_PLAT_RULES = {
  all: "TARGET: ALL PLATFORMS. First write ONE core version of this post. Then adapt it per platform: (a) YouTube — 2-3 title options under 60 chars + description + 10 tags, (b) TikTok/IG Reels/FB Reels — caption + hashtags (slightly different per platform), (c) X — one post under 280 chars that invites replies, (d) WhatsApp Channel — 2-line announcement, (e) LinkedIn — 4-6 line professional-tone version.",
  shorts: "TARGET: vertical short video (YouTube Shorts / TikTok / IG Reels / FB Reels). Format as a 45-75 second script: HOOK (0-3s) -> body -> local angle -> CTA follow @aixahmad. Add [B-ROLL] notes + one caption with hashtags.",
  yt: "TARGET: YouTube main video. Give 3 title options (under 60 chars, curiosity-driven), a 2-paragraph description, 15 SEO tags, and a pinned-comment suggestion.",
  x: "TARGET: X (Twitter). ONE post under 280 characters that invites replies. No hashtags spam (max 1-2).",
  igfb: "TARGET: Instagram + Facebook. One caption: scroll-stopping first line, 3-5 short lines, then 8 hashtags for IG and 4 for FB (listed separately).",
  li: "TARGET: LinkedIn. 4-6 lines, professional but warm, one insight + one question at the end, max 3 hashtags.",
  wa: "TARGET: WhatsApp Channel. 2-3 line announcement, friendly, one emoji max per line, with a link placeholder.",
};
function renderTemplates(el) {
  const head = document.createElement("div");
  head.className = "addrow";
  head.innerHTML =
    '<input id="tpltopic" style="flex:1;min-width:220px" placeholder="Your topic… e.g. ChatGPT se paise kamana, Gemini 3, AI in farming" value="' + esc(tplTopic) + '">' +
    '<div class="bar" style="margin:0">' +
    '<button id="lang-ur" class="' + (tplLang === "ur" ? "active" : "") + '">اردو Roman Urdu</button>' +
    '<button id="lang-en" class="' + (tplLang === "en" ? "active" : "") + '">English</button></div>';
  el.appendChild(head);
  head.querySelector("#tpltopic").addEventListener("input", e => { tplTopic = e.target.value; });
  head.querySelector("#lang-ur").onclick = () => { tplLang = "ur"; localStorage.setItem("tpl_lang", "ur"); renderBoard(); };
  head.querySelector("#lang-en").onclick = () => { tplLang = "en"; localStorage.setItem("tpl_lang", "en"); renderBoard(); };

  const platbar = document.createElement("div");
  platbar.className = "bar";
  platbar.style.marginTop = "0";
  TPL_PLATS.forEach(([k, label]) => {
    const b = document.createElement("button");
    b.innerHTML = label;
    b.className = tplPlat === k ? "active" : "";
    b.onclick = () => { tplPlat = k; renderBoard(); };
    platbar.appendChild(b);
  });
  el.appendChild(platbar);

  const cats = ["All"].concat([...new Set((window.GALLERY || []).map(t => t.cat))]);
  const chipbar = document.createElement("div");
  chipbar.className = "bar";
  cats.forEach(c => {
    const b = document.createElement("button");
    b.textContent = c;
    b.className = tplCat === c ? "active" : "";
    b.onclick = () => { tplCat = c; renderBoard(); };
    chipbar.appendChild(b);
  });
  el.appendChild(chipbar);

  const grid = document.createElement("div");
  grid.className = "tplgrid";
  (window.GALLERY || []).filter(t => tplCat === "All" || t.cat === tplCat).forEach(t => {
    const c = document.createElement("div");
    c.className = "tplcard";
    c.innerHTML = '<div class="te">' + t.emoji + '</div><div class="tn">' + esc(t.name) +
      '</div><div class="td">' + esc(t.desc) + '</div><span class="tag">' + esc(t.cat) + "</span>";
    c.onclick = () => useTemplate(t);
    grid.appendChild(c);
  });
  el.appendChild(grid);

  const flow = document.createElement("div");
  flow.className = "panel";
  flow.id = "tplflow";
  flow.hidden = !tplCurrent;
  flow.innerHTML = tplCurrent ? tplFlowHtml() : "";
  el.appendChild(flow);
  if (tplCurrent) wireTplFlow();
}
function brandHeader() {
  const lang = tplLang === "ur"
    ? "OUTPUT LANGUAGE: simple Roman Urdu with light English (easy to read while filming)."
    : "OUTPUT LANGUAGE: simple, friendly English (no heavy jargon).";
  return 'You are the content writer for "AI x Ahmad" (@aixahmad) — AI explained simply for everyday people in Pakistan and India (students, freelancers, shopkeepers). No jargon, friendly tone, energy high.\n' + lang + "\n\n";
}
function useTemplate(t) {
  tplCurrent = t;
  const topic = (document.getElementById("tpltopic") || {}).value || tplTopic;
  tplTopic = (topic || "").trim();
  if (!tplTopic) { toast("Pehle topic likho 👆"); return; }
  renderBoard();
  const prompt = brandHeader() + t.body.split("{topic}").join(tplTopic) +
    "\n\n" + TPL_PLAT_RULES[tplPlat];
  document.getElementById("tplprompt").value = prompt;
  navigator.clipboard.writeText(prompt).then(() => toast("Prompt copied — paste in Claude 🤖"));
  document.getElementById("tplflow").scrollIntoView({ behavior: "smooth" });
}
function tplFlowHtml() {
  return '<h3>' + tplCurrent.emoji + " " + esc(tplCurrent.name) +
    ' <button class="ghost" style="padding:5px 14px;font-size:12px" onclick="copyTpl()">📋 Copy again</button></h3>' +
    '<p class="sub">1) Paste in your <b>Claude app</b> → 2) edit in canvas, make your poster → 3) paste the FINAL version below and save.</p>' +
    '<textarea id="tplprompt" readonly style="width:100%;min-height:130px;font:12px/1.6 Consolas,monospace;background:var(--surface2)"></textarea>' +
    '<p class="sub" style="margin-top:14px"><b>Final version</b> (from Claude, after your edits):</p>' +
    '<textarea id="tplfinal" style="width:100%;min-height:120px" placeholder="Paste your final content here…"></textarea>' +
    '<div class="mfoot">' +
    '<button class="btn" onclick="saveTplFinal()">💾 Save to Drafts</button>' +
    '<button class="ghost" onclick="downloadTplFinal()">⬇ Download file</button>' +
    '<a class="ghost" style="text-decoration:none" target="_blank" href="https://drive.google.com/drive/my-drive">Open Google Drive ↗</a></div>';
}
function wireTplFlow() { /* buttons use onclick attrs */ }
function copyTpl() {
  navigator.clipboard.writeText(document.getElementById("tplprompt").value)
    .then(() => toast("Copied 📋"));
}
function saveTplFinal() {
  const txt = document.getElementById("tplfinal").value.trim();
  if (!txt) { toast("Paste the final version first"); return; }
  const platMap = { all: ["yt","shorts","tiktok","ig","fb","x","wa","li"],
    shorts: ["shorts","tiktok","ig","fb"], yt: ["yt"], x: ["x"],
    igfb: ["ig","fb"], li: ["li"], wa: ["wa"] };
  plans.unshift({ id: Date.now(), title: tplTopic + " — " + tplCurrent.name,
    url: "", notes: txt, status: "draft", assignee: "Ahmad",
    platforms: platMap[tplPlat] || ["yt","shorts"], when: "" });
  savePlans();
  toast("Saved to Drafts 📝 — schedule it from there");
}
function downloadTplFinal() {
  const txt = document.getElementById("tplfinal").value.trim();
  if (!txt) { toast("Paste the final version first"); return; }
  const blob = new Blob([txt], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = (tplTopic || "post").replace(/[^\w\s-]/g, "").slice(0, 40) + ".txt";
  a.click();
  toast("Downloaded — drop it into your Drive folder");
}

function platTags(p, max) {
  max = max || 4;
  return p.platforms.slice(0, max).map(k => {
    const f = PLATFORMS.find(x => x[0] === k);
    return '<span class="tag">' + (f ? f[1] : k) + "</span>";
  }).join("") + (p.platforms.length > max ? '<span class="tag">+' + (p.platforms.length - max) + "</span>" : "");
}

function postRow(p, withTime) {
  const d = document.createElement("div");
  d.className = "qrow";
  d.innerHTML =
    (withTime ? '<span class="qtime">' + (p.when ? p.when.slice(11, 16) : "--:--") + "</span>" : "") +
    '<span class="avatar ' + (p.assignee === "Editor" ? "editor" : "ahmad") + '">' +
    (p.assignee === "Editor" ? "E" : "A") + "</span>" +
    '<span class="qtext">' + esc(p.title.split("\n")[0].slice(0, 80)) + "</span>" +
    '<span class="qtags">' + platTags(p) + "</span>";
  d.onclick = () => openComposer(p.id);
  return d;
}

function dayName(iso) {
  const today = new Date();
  const t = today.toISOString().slice(0, 10);
  const tom = new Date(today.getTime() + 86400000).toISOString().slice(0, 10);
  const label = new Date(iso + "T00:00").toLocaleDateString("en-GB",
    { weekday: "long", day: "numeric", month: "long" });
  if (iso === t) return "Today · " + label;
  if (iso === tom) return "Tomorrow · " + label;
  return label;
}

function renderQueue(el) {
  const sched = plans.filter(p => p.status === "scheduled" && p.when)
    .sort((a, b) => a.when.localeCompare(b.when));
  if (!sched.length) {
    el.innerHTML = '<div class="empty">Queue is empty — schedule a draft, or press + New post.</div>';
    return;
  }
  let lastDay = "";
  sched.forEach(p => {
    const day = p.when.slice(0, 10);
    if (day !== lastDay) {
      lastDay = day;
      const h = document.createElement("div");
      h.className = "qday";
      h.textContent = dayName(day);
      el.appendChild(h);
    }
    el.appendChild(postRow(p, true));
  });
}

function renderList(el, statuses, emptyMsg) {
  const items = plans.filter(p => statuses.includes(p.status));
  if (!items.length) { el.innerHTML = '<div class="empty">' + emptyMsg + "</div>"; return; }
  items.forEach(p => el.appendChild(postRow(p, false)));
}

function renderIdeas(el) {
  const top = document.createElement("div");
  top.className = "addrow";
  top.innerHTML = '<input id="ideainp" style="flex:1;min-width:200px" placeholder="Quick idea… (press Enter to save)">';
  el.appendChild(top);
  setTimeout(() => {
    const inp = document.getElementById("ideainp");
    if (inp) inp.addEventListener("keydown", e => {
      if (e.key === "Enter" && e.target.value.trim()) {
        addPlan(e.target.value.trim(), "");
        renderBoard();
      }
    });
  }, 0);
  const grid = document.createElement("div");
  grid.className = "ideagrid";
  const ideas = plans.filter(p => p.status === "idea");
  if (!ideas.length) grid.innerHTML =
    '<div class="empty">No ideas yet — the 🎬 plan button on any news story drops it here.</div>';
  ideas.forEach(p => {
    const c = document.createElement("div");
    c.className = "ideacard";
    c.innerHTML = '<div class="t">' + esc(p.title.split("\n")[0]) + "</div>" +
      (p.url ? '<a href="' + esc(p.url) + '" target="_blank">source</a>' : "") +
      '<div style="margin-top:10px;display:flex;gap:6px">' +
      '<button class="ghost" style="padding:5px 12px;font-size:12px">→ Draft</button>' +
      '<button class="ghost" style="padding:5px 12px;font-size:12px">Open</button>' +
      '<button class="danger" style="padding:5px 10px;font-size:12px;margin-left:auto">✕</button></div>';
    const btns = c.querySelectorAll("button");
    btns[0].onclick = () => { p.status = "draft"; savePlans(); renderBoard(); toast("Moved to Drafts 📝"); };
    btns[1].onclick = () => openComposer(p.id);
    btns[2].onclick = () => {
      if (confirm("Delete idea?")) {
        plans = plans.filter(x => x.id !== p.id); savePlans(); renderBoard();
      }
    };
    grid.appendChild(c);
  });
  el.appendChild(grid);
}

function renderCalendar(el) {
  const now = new Date();
  const monday = new Date(now);
  monday.setDate(now.getDate() - ((now.getDay() + 6) % 7) + calOffset * 7);
  const head = document.createElement("div");
  head.className = "calhead";
  head.innerHTML = '<button class="ghost" id="calprev">←</button>' +
    "<b>" + monday.toLocaleDateString("en-GB", { month: "long", year: "numeric" }) + "</b>" +
    '<button class="ghost" id="calnext">→</button>' +
    '<button class="ghost" id="caltoday">Today</button>';
  el.appendChild(head);
  head.querySelector("#calprev").onclick = () => { calOffset--; renderBoard(); };
  head.querySelector("#calnext").onclick = () => { calOffset++; renderBoard(); };
  head.querySelector("#caltoday").onclick = () => { calOffset = 0; renderBoard(); };
  const grid = document.createElement("div");
  grid.className = "calgrid";
  const todayIso = new Date().toISOString().slice(0, 10);
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    const iso = d.toISOString().slice(0, 10);
    const cell = document.createElement("div");
    cell.className = "calcell" + (iso === todayIso ? " today" : "");
    cell.innerHTML = '<div class="cd">' +
      d.toLocaleDateString("en-GB", { weekday: "short" }) + " " + d.getDate() + "</div>";
    plans.filter(p => p.when && p.when.slice(0, 10) === iso && p.status !== "idea")
      .sort((a, b) => a.when.localeCompare(b.when))
      .forEach(p => {
        const chipEl = document.createElement("div");
        chipEl.className = "calpost " + p.status;
        chipEl.textContent = p.when.slice(11, 16) + " " + p.title.split("\n")[0].slice(0, 22);
        chipEl.onclick = () => openComposer(p.id);
        cell.appendChild(chipEl);
      });
    const plus = document.createElement("button");
    plus.className = "calplus";
    plus.textContent = "+";
    plus.onclick = () => openComposer(null, iso);
    cell.appendChild(plus);
    grid.appendChild(cell);
  }
  el.appendChild(grid);
}

/* ---- composer (Buffer-style) ---- */
function openComposer(id, presetDate) {
  let p = id ? plans.find(x => x.id === id) : null;
  if (!p) {
    p = { id: Date.now(), title: "", url: "", notes: "",
      status: presetDate ? "scheduled" : "draft",
      assignee: "Ahmad", platforms: ["yt", "shorts"],
      when: presetDate ? presetDate + "T18:00" : "" };
    plans.unshift(p);
    savePlans();
  }
  editingId = p.id;
  document.getElementById("m-title").value = p.title;
  document.getElementById("m-url").value = p.url || "";
  document.getElementById("m-ass").value = p.assignee;
  document.getElementById("m-status").value = p.status;
  document.getElementById("m-date").value = p.when ? p.when.slice(0, 10) : "";
  document.getElementById("m-time").value = p.when ? p.when.slice(11, 16) : "18:00";
  document.getElementById("m-notes").value = p.notes || "";
  const tplSel = document.getElementById("m-tpl");
  tplSel.innerHTML = '<option value="">— plug &amp; play template —</option>' +
    (window.POST_TEMPLATES || []).map((t, i) =>
      '<option value="' + i + '">' + t.name + "</option>").join("");
  tplSel.onchange = () => {
    if (tplSel.value !== "") {
      document.getElementById("m-title").value = window.POST_TEMPLATES[+tplSel.value].text;
      tplSel.value = "";
    }
  };
  const pl = document.getElementById("m-plats");
  pl.innerHTML = "";
  PLATFORMS.forEach(([k, name]) => {
    const lab = document.createElement("label");
    lab.textContent = name;
    lab.className = p.platforms.includes(k) ? "on" : "";
    lab.onclick = () => {
      p.platforms = p.platforms.includes(k)
        ? p.platforms.filter(x => x !== k) : p.platforms.concat(k);
      savePlans();
      lab.classList.toggle("on");
    };
    pl.appendChild(lab);
  });
  document.getElementById("modal").hidden = false;
}
function modalSaveFields() {
  const p = plans.find(x => x.id === editingId);
  if (!p) return;
  p.title = document.getElementById("m-title").value.trim() || p.title || "Untitled";
  p.url = document.getElementById("m-url").value.trim();
  p.assignee = document.getElementById("m-ass").value;
  p.status = document.getElementById("m-status").value;
  const date = document.getElementById("m-date").value;
  p.when = date ? date + "T" + (document.getElementById("m-time").value || "18:00") : "";
  if (p.status === "scheduled" && !p.when) p.status = "draft";
  p.notes = document.getElementById("m-notes").value;
  savePlans();
}
function closeModal() {
  modalSaveFields();
  document.getElementById("modal").hidden = true;
  editingId = null;
  renderBoard();
}
function modalDelete() {
  if (!confirm("Delete this post?")) return;
  plans = plans.filter(x => x.id !== editingId);
  savePlans();
  document.getElementById("modal").hidden = true;
  editingId = null;
  renderBoard();
}
function modalPrep() {
  modalSaveFields();
  const p = plans.find(x => x.id === editingId);
  document.getElementById("modal").hidden = true;
  if (p) {
    document.getElementById("preptitle").value = p.title.split("\n")[0].slice(0, 120);
    document.getElementById("prepurl").value = p.url || "";
    switchTab("prep");
    toast("Loaded — pick a button 📝");
  }
}
document.getElementById("modal").addEventListener("click", e => {
  if (e.target.id === "modal") closeModal();
});

function exportPlans() {
  const blob = new Blob([JSON.stringify(plans, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "aixahmad-posts.json";
  a.click();
  toast("Posts file downloaded — send it to your editor");
}
document.getElementById("importfile").addEventListener("change", e => {
  const f = e.target.files[0];
  if (!f) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const arr = JSON.parse(reader.result);
      if (Array.isArray(arr)) { plans = arr; savePlans(); renderBoard(); toast("Imported ✓"); }
    } catch (err) { alert("That file is not a valid export."); }
  };
  reader.readAsText(f);
});


/* ---------------- Prep ---------------- */
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

/* ---------------- Home dashboard ---------------- */
const UPDATED = "__UPDATED__";
function renderHome() {
  document.getElementById("homedatetxt").textContent =
    new Date().toLocaleDateString("en-GB",
      { weekday: "long", day: "numeric", month: "long" }) +
    " · radar updated " + UPDATED;

  // top pick: best video-worthy story not yet covered
  const candidates = ITEMS.filter(it => it.p !== 9 && !doneSet.has(it.u))
    .slice().sort((a, b) => b.sc - a.sc);
  const tp = document.getElementById("toppick");
  if (candidates.length) {
    const p = candidates[0];
    tp.innerHTML =
      '<span class="picktag">✨ Aaj ka top pick</span>' +
      '<h2><a href="' + esc(p.u) + '" target="_blank" rel="noopener">' + esc(p.t) + "</a></h2>" +
      '<div class="pickrow">' +
      '<span class="badge score">Score ' + p.sc + "</span>" +
      (p.lo ? '<span class="badge localb">PK/IN local angle</span>' : "") +
      (p.l && p.l.length ? '<span class="badge src">' + (p.l.length + 1) + " sources</span>" : "") +
      '<button class="btn" id="pickplan">Plan video →</button></div>';
    document.getElementById("pickplan").onclick = () => {
      addPlan(p.t, p.u);
      switchTab("plan");
    };
  } else {
    tp.innerHTML = '<span class="picktag">✨ Aaj ka top pick</span><p>No stories yet today.</p>';
  }

  // stat cards
  const day = Date.now() - 86400000;
  const today = ITEMS.filter(it => it.p !== 9 && new Date(it.d).getTime() > day);
  const hot = today.filter(it => it.l && it.l.length).length;
  const local = today.filter(it => it.lo).length;
  const open = plans.filter(x => x.status !== "posted").length;
  document.getElementById("statgrid").innerHTML =
    '<div class="scard"><div class="l">Stories today</div><div class="n">' + today.length + "</div></div>" +
    '<div class="scard"><div class="l">Hot</div><div class="n orange">' + hot + "</div></div>" +
    '<div class="scard"><div class="l">Local angle</div><div class="n green">' + local + "</div></div>" +
    '<div class="scard"><div class="l">Tickets open</div><div class="n indigo">' + open + "</div></div>";

  // pipeline
  const pl = document.getElementById("pipeline");
  const openPlans = plans.filter(x => x.status !== "posted").slice(0, 6);
  pl.innerHTML = openPlans.length ? "" :
    '<p style="color:var(--faint);font-size:13px">No open tickets — plan a video from News.</p>';
  openPlans.forEach(p => {
    const d = document.createElement("div");
    d.className = "pipe";
    d.innerHTML = '<span class="st">' + p.status + "</span>" +
      "<span>" + esc(p.title.slice(0, 48)) + "</span>" +
      '<span class="who ' + (p.assignee === "Editor" ? "editor" : "ahmad") + '">' +
      esc(p.assignee) + "</span>";
    d.onclick = () => switchTab("plan");
    pl.appendChild(d);
  });
}
function qaShort() {
  switchTab("prep");
  document.getElementById("preptitle").focus();
  toast("Fill the story, then press Short Script 🎬");
}
function qaX() {
  switchTab("prep");
  document.getElementById("xtopic").focus();
  toast("Pick a topic, then choose a format 💬");
}
function qaNews() {
  mode = "worthy";
  switchTab("news");
  bar(); render();
}

document.getElementById("q").addEventListener("input", e => {
  q = e.target.value.trim(); shown = PAGE; render();
});
document.getElementById("more").onclick = () => { shown += PAGE; render(); };
trendsBar(); bar(); renderHome(); render();
</script>
</body>
</html>
"""


def _load_passcode():
    """Access code: env var on the cloud (GitHub secret), local file on PC.
    Only its SHA-256 hash goes into the page."""
    code = os.environ.get("SITE_PASSCODE", "").strip()
    if not code:
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "site_passcode.txt")) as f:
                code = f.read().strip()
        except FileNotFoundError:
            pass
    return code


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

    code = _load_passcode()
    lock_hash = hashlib.sha256(code.encode()).hexdigest() if code else ""

    updated = now.strftime("%d %b %Y, %H:%M UTC")
    html = (PAGE
            .replace("__PILLARS__", json.dumps(config.CATEGORIES))
            .replace("__ITEMS__", json.dumps(items, ensure_ascii=False))
            .replace("__TRENDS__", json.dumps(chips, ensure_ascii=False))
            .replace("__LOCKHASH__", lock_hash)
            .replace("__UPDATED__", updated))

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"docs/index.html written with {len(items)} stories.")


if __name__ == "__main__":
    generate()
