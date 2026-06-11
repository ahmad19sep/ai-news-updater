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

  /* ---------- hero (Buffer style) ---------- */
  .hero { position:relative; text-align:center; padding:54px 0 30px; }
  .hero .tagline { display:inline-flex; align-items:center; gap:8px;
          background:var(--surface2); border:1px solid var(--line);
          color:var(--dim); border-radius:999px; padding:7px 16px;
          font:600 12px Inter; margin-bottom:22px; }
  .hero .tagline .live { width:8px; height:8px; border-radius:50%;
          background:#22c55e; box-shadow:0 0 0 3px rgba(34,197,94,.2);
          animation:pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }
  .hero h1 { font-family:var(--display); font-size:clamp(34px, 6vw, 58px);
          font-weight:800; letter-spacing:-.03em; line-height:1.08; margin:0 0 14px; }
  .hero h1 em { font-style:normal; position:relative; white-space:nowrap; }
  .hero h1 em::after { content:""; position:absolute; left:0; right:0; bottom:6px;
          height:.32em; background:var(--cta); z-index:-1; border-radius:4px; }
  .hero .sub { color:var(--dim); font-size:16px; margin:0 auto 26px; max-width:480px; }
  .herostats { display:flex; gap:10px; justify-content:center; flex-wrap:wrap; }
  .herostats span { background:var(--surface); border:1px solid var(--line);
          border-radius:999px; padding:8px 18px; font:600 12.5px Inter;
          color:var(--text); box-shadow:var(--shadow-sm); }
  .float { position:absolute; width:52px; height:52px; border-radius:14px;
          display:flex; align-items:center; justify-content:center; font-size:24px;
          box-shadow:var(--shadow-sm); border:1px solid rgba(0,0,0,.04);
          animation:bob 5s ease-in-out infinite; }
  @keyframes bob { 0%,100%{transform:translateY(0) rotate(var(--rot,0deg))}
                   50%{transform:translateY(-9px) rotate(var(--rot,0deg))} }
  .f1 { left:2%;  top:18%; background:#fde9e9; --rot:-7deg; }
  .f2 { left:9%;  top:62%; background:#e8f4fd; --rot:5deg;  animation-delay:.6s; }
  .f3 { right:3%; top:14%; background:#eef9e7; --rot:8deg;  animation-delay:.3s; }
  .f4 { right:10%; top:58%; background:#fdf3e2; --rot:-5deg; animation-delay:.9s; }
  .f5 { left:20%; top:6%;  background:#f3e8ff; --rot:4deg;  animation-delay:1.2s; }
  .f6 { right:21%; top:74%; background:#e6fbf3; --rot:-8deg; animation-delay:1.5s; }
  @media (max-width:860px) { .float { display:none; } .hero { padding-top:34px; } }
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

  /* ---------- board (Asana style) ---------- */
  .board { display:flex; gap:14px; overflow-x:auto; padding:8px 2px 28px;
           align-items:flex-start; }
  .col { min-width:268px; width:268px; flex-shrink:0; background:var(--surface2);
         border-radius:12px; padding:10px 10px 12px; }
  .col h3 { font-size:12.5px; font-weight:700; color:var(--text); margin:4px 6px 12px;
          display:flex; align-items:center; gap:8px; }
  .col h3 .dot { width:9px; height:9px; border-radius:50%; }
  .col h3 .n { color:var(--faint); font-weight:600; font-size:11.5px; margin-left:auto; }
  .colbody { min-height:30px; border-radius:8px; transition:.15s; }
  .colbody.dragover { background:var(--indigo-soft); outline:2px dashed var(--indigo); }
  .tcard { background:var(--surface); border:1px solid var(--line); border-radius:10px;
          padding:12px 13px; margin-bottom:9px; cursor:grab; transition:.15s;
          box-shadow:var(--shadow-sm); }
  .tcard:hover { box-shadow:var(--shadow); border-color:var(--line2); }
  .tcard:active { cursor:grabbing; }
  .tcard .t { font-weight:600; font-size:13px; line-height:1.4; margin-bottom:8px; }
  .tcard .crow { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
  .avatar { width:22px; height:22px; border-radius:50%; font-size:10.5px; font-weight:700;
          display:inline-flex; align-items:center; justify-content:center; color:#fff; }
  .avatar.ahmad { background:var(--indigo); }
  .avatar.editor { background:#f59e0b; }
  .tag { font-size:10px; font-weight:600; color:var(--dim); background:var(--surface2);
          border:1px solid var(--line); border-radius:5px; padding:1.5px 6px; }
  .duetag { font-size:10.5px; font-weight:600; color:var(--dim); margin-left:auto; }
  .duetag.late { color:var(--red); }
  .addcard { width:100%; background:none; border:none; color:var(--faint); text-align:left;
          padding:8px 10px; border-radius:8px; font:500 12.5px Inter; cursor:pointer; }
  .addcard:hover { background:var(--surface); color:var(--indigo); }

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
      <button id="tabbtn-news" class="active" onclick="switchTab('news')">News</button>
      <button id="tabbtn-trends" onclick="switchTab('trends')">Trends</button>
      <button id="tabbtn-research" onclick="switchTab('research')">Research</button>
      <button id="tabbtn-plan" onclick="switchTab('plan')">Board</button>
      <button id="tabbtn-prep" onclick="switchTab('prep')">Prep</button>
    </nav>
    <div class="updated">AI Ki Duniya, Simple Urdu Mein · @aixahmad</div>
  </div>
</header>
<div class="wrap">

  <section id="tab-news">
    <div class="hero">
      <div class="float f1">🤖</div>
      <div class="float f2">📺</div>
      <div class="float f3">⚡</div>
      <div class="float f4">🎬</div>
      <div class="float f5">💡</div>
      <div class="float f6">🔥</div>
      <span class="tagline"><span class="live"></span> Live radar · updated __UPDATED__</span>
      <h1>Aaj kya <em>film</em> karein?</h1>
      <p class="sub">Poori AI duniya ki news — aapki audience ke liye ranked,
         scripts ready, ek hi jagah.</p>
      <div class="herostats" id="herostats"></div>
    </div>
    <div class="search"><input id="q" placeholder="Search stories… Gemini, jobs, WhatsApp"></div>
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
    <div class="addrow">
      <input id="newidea" style="flex:1;min-width:200px" placeholder="New ticket title…">
      <button class="btn" onclick="addIdea()">+ New ticket</button>
      <button class="ghost" onclick="exportPlans()">⬇ Export</button>
      <button class="ghost" onclick="document.getElementById('importfile').click()">⬆ Import</button>
      <input type="file" id="importfile" accept=".json" hidden>
    </div>
    <div class="bar" id="assfilter"></div>
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
</div>

<div id="modal" hidden>
  <div class="mbox">
    <input type="text" id="m-title" class="mtitle" placeholder="Ticket title">
    <div class="mrow"><span class="lbl">Source</span>
      <input type="text" id="m-url" style="flex:1" placeholder="https://… (optional)"></div>
    <div class="mrow"><span class="lbl">Assignee</span>
      <select id="m-ass"><option>Ahmad</option><option>Editor</option></select>
      <span class="lbl" style="width:auto">Due</span>
      <input type="date" id="m-due"></div>
    <div class="mrow"><span class="lbl">Platforms</span>
      <span class="mplats" id="m-plats"></span></div>
    <div class="mrow" style="align-items:flex-start"><span class="lbl">Notes</span>
      <textarea id="m-notes" style="flex:1;min-height:110px"
        placeholder="script paste, links, instructions for editor…"></textarea></div>
    <div class="mfoot">
      <button class="btn" onclick="closeModal()">Done</button>
      <button class="ghost" onclick="modalPrep()">📝 Prep</button>
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

function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg; t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 1900);
}
function savePlans() { localStorage.setItem("plans", JSON.stringify(plans)); }
function switchTab(name) {
  ["news","trends","research","plan","prep"].forEach(n => {
    document.getElementById("tab-" + n).hidden = n !== name;
    document.getElementById("tabbtn-" + n).classList.toggle("active", n === name);
  });
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

/* ---------------- Board (Asana style: drag & drop + ticket modal) ---------------- */
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
  STATUSES.forEach(([key, label, color]) => {
    const col = document.createElement("div");
    col.className = "col";
    const cards = plans.filter(p => p.status === key &&
      (assFilter === "All" || p.assignee === assFilter));
    col.innerHTML = '<h3><span class="dot" style="background:' + color + '"></span>' +
      label + ' <span class="n">' + cards.length + "</span></h3>";
    const body = document.createElement("div");
    body.className = "colbody";
    body.dataset.status = key;
    body.addEventListener("dragover", e => { e.preventDefault(); body.classList.add("dragover"); });
    body.addEventListener("dragleave", () => body.classList.remove("dragover"));
    body.addEventListener("drop", e => {
      e.preventDefault();
      body.classList.remove("dragover");
      const id = +e.dataTransfer.getData("text/plain");
      const p = plans.find(x => x.id === id);
      if (p && p.status !== key) { p.status = key; savePlans(); renderBoard(); }
    });
    cards.forEach(p => {
      const c = document.createElement("div");
      c.className = "tcard";
      c.draggable = true;
      const late = p.due && p.due < new Date().toISOString().slice(0, 10) && key !== "posted";
      const plats = p.platforms.slice(0, 3).map(k => {
        const f = PLATFORMS.find(x => x[0] === k);
        return '<span class="tag">' + (f ? f[1] : k) + "</span>";
      }).join("") + (p.platforms.length > 3 ? '<span class="tag">+' + (p.platforms.length - 3) + "</span>" : "");
      c.innerHTML =
        '<div class="t">' + esc(p.title) + "</div>" +
        '<div class="crow">' +
        '<span class="avatar ' + (p.assignee === "Editor" ? "editor" : "ahmad") + '">' +
        (p.assignee === "Editor" ? "E" : "A") + "</span>" + plats +
        (p.due ? '<span class="duetag' + (late ? " late" : "") + '">📅 ' +
          p.due.slice(5) + "</span>" : "") +
        "</div>";
      c.addEventListener("dragstart", e =>
        e.dataTransfer.setData("text/plain", String(p.id)));
      c.onclick = () => openTicket(p.id);
      body.appendChild(c);
    });
    col.appendChild(body);
    const add = document.createElement("button");
    add.className = "addcard";
    add.textContent = "+ Add ticket";
    add.onclick = () => {
      const title = prompt("Ticket title:");
      if (title && title.trim()) {
        plans.unshift({ id: Date.now(), title: title.trim(), url: "", notes: "",
          status: key, assignee: "Ahmad", platforms: ["yt", "shorts"], due: "" });
        savePlans();
        renderBoard();
      }
    };
    col.appendChild(add);
    board.appendChild(col);
  });
}

/* ---- ticket modal ---- */
function openTicket(id) {
  const p = plans.find(x => x.id === id);
  if (!p) return;
  editingId = id;
  document.getElementById("m-title").value = p.title;
  document.getElementById("m-url").value = p.url || "";
  document.getElementById("m-ass").value = p.assignee;
  document.getElementById("m-due").value = p.due || "";
  document.getElementById("m-notes").value = p.notes || "";
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
  p.title = document.getElementById("m-title").value.trim() || p.title;
  p.url = document.getElementById("m-url").value.trim();
  p.assignee = document.getElementById("m-ass").value;
  p.due = document.getElementById("m-due").value;
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
  if (!confirm("Delete this ticket?")) return;
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
    document.getElementById("preptitle").value = p.title;
    document.getElementById("prepurl").value = p.url || "";
    switchTab("prep");
    toast("Ticket loaded — pick a button 📝");
  }
}
document.getElementById("modal").addEventListener("click", e => {
  if (e.target.id === "modal") closeModal();
});

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

function heroStats() {
  const day = Date.now() - 86400000;
  const today = ITEMS.filter(it => it.p !== 9 && new Date(it.d).getTime() > day);
  const hot = today.filter(it => it.l && it.l.length).length;
  const el = document.getElementById("herostats");
  const bits = ["🗞 " + today.length + " stories aaj"];
  if (hot) bits.push("🔥 " + hot + " hot");
  if (TRENDS.length) bits.push("🚀 rising: " + TRENDS[0].display);
  const local = today.filter(it => it.lo).length;
  if (local) bits.push("🇵🇰🇮🇳 " + local + " local");
  el.innerHTML = bits.map(b => "<span>" + b + "</span>").join("");
}

document.getElementById("q").addEventListener("input", e => {
  q = e.target.value.trim(); shown = PAGE; render();
});
document.getElementById("more").onclick = () => { shown += PAGE; render(); };
trendsBar(); bar(); heroStats(); render();
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
