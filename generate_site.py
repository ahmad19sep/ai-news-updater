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
  .scard.click { cursor:pointer; transition:.15s; }
  .scard.click:hover { box-shadow:var(--shadow); border-color:var(--line2);
          transform:translateY(-2px); }
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
  .tplcard.on { border-color:var(--cta); box-shadow:0 0 0 2px #e3f7d2; }
  .wstep { display:flex; gap:14px; margin:20px 0; }
  .wnum { width:28px; height:28px; border-radius:50%; background:var(--text); color:#fff;
          font:700 13px Inter; display:flex; align-items:center; justify-content:center;
          flex-shrink:0; margin-top:2px; }
  .wbody { flex:1; min-width:0; }
  .wbody h4 { margin:2px 0 10px; font-size:14px; font-weight:700;
          font-family:var(--display); }
  .typecards { display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));
          gap:12px; }
  .typecard { background:var(--surface); border:1px solid var(--line); border-radius:14px;
          padding:18px 16px; cursor:pointer; transition:.15s; display:flex;
          flex-direction:column; gap:4px; box-shadow:var(--shadow-sm); }
  .typecard:hover { box-shadow:var(--shadow); transform:translateY(-2px); }
  .typecard.on { border-color:var(--cta); box-shadow:0 0 0 2px #e3f7d2; }
  .typecard .te { font-size:26px; }
  .typecard b { font-family:var(--display); font-size:14.5px; }
  .typecard span { color:var(--dim); font-size:12px; line-height:1.45; }
  .whint { color:var(--faint); font-size:12px; }
  .chkrow { display:flex; flex-wrap:wrap; gap:8px 18px; margin:10px 0; }
  .chk { font-size:13px; color:var(--dim); display:flex; align-items:center; gap:7px;
          cursor:pointer; }
  .chk input { width:16px; height:16px; accent-color:#65a30d; }
  .scriptbox summary { cursor:pointer; font-size:12.5px; color:var(--indigo);
          margin:6px 0; }
  .scriptbox pre { background:var(--surface2); border:1px solid var(--line);
          border-radius:10px; padding:12px 14px; font:12px/1.6 Consolas, monospace;
          white-space:pre-wrap; max-height:260px; overflow-y:auto; }
  .calpost.publish { background:var(--gold-soft); color:var(--gold); }

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
  /* ---------- dark theme ---------- */
  .themebtn { background:var(--surface); border:1px solid var(--line); border-radius:50%;
          width:38px; height:38px; font-size:16px; cursor:pointer; transition:.15s;
          flex-shrink:0; }
  .themebtn:hover { border-color:var(--line2); box-shadow:var(--shadow-sm); }
  body.dark {
    --bg:#0b0f17; --surface:#131a26; --surface2:#1a2230;
    --text:#e7ecf3; --dim:#9aa3b2; --faint:#647082;
    --line:rgba(255,255,255,.08); --line2:rgba(255,255,255,.17);
    --indigo-soft:rgba(99,102,241,.18);
    --gold:#fbbf24; --gold-soft:rgba(251,191,36,.13);
    --green:#34d399; --green-soft:rgba(52,211,153,.12);
    --red:#f87171; --red-soft:rgba(248,113,113,.15);
    --orange:#fb923c; --orange-soft:rgba(251,146,60,.13);
    --purple:#a78bfa; --purple-soft:rgba(167,139,250,.15);
    --blue:#60a5fa; --blue-soft:rgba(96,165,250,.15);
    --shadow-sm:0 1px 2px rgba(0,0,0,.4);
    --shadow:0 4px 16px -4px rgba(0,0,0,.55);
    --shadow-lg:0 20px 50px -12px rgba(0,0,0,.75);
  }
  body.dark { background:var(--bg); }
  body.dark header { background:rgba(11,15,23,.82); }
  body.dark .tabs button.active { background:var(--indigo); color:#fff; }
  body.dark .bar button.active { background:var(--indigo); border-color:var(--indigo); color:#fff; }
  body.dark .bar button.gold.active { background:var(--cta); border-color:var(--cta); color:var(--cta-dark); }
  body.dark .toast { background:var(--indigo); }
  body.dark .chip { background:rgba(52,211,153,.1); border-color:rgba(52,211,153,.28); }
  body.dark .qa:hover { background:rgba(165,229,115,.08); }
  body.dark .calcell.today,
  body.dark .typecard.on,
  body.dark .tplcard.on { box-shadow:0 0 0 2px rgba(165,229,115,.3); }
  body.dark .pill { color:#b6bdfc; }

  /* ---------- responsive: phone-first fixes ---------- */
  html, body { max-width:100%; overflow-x:hidden; }
  @media (max-width:768px) {
    .wrap { padding:0 12px 70px; }
    .hrow { padding:10px 12px; gap:8px; }
    .logo { font-size:15px; }
    .updated { display:none; }
    .tabs { margin-left:0; width:100%; overflow-x:auto; flex-wrap:nowrap;
            -webkit-overflow-scrolling:touch; scrollbar-width:none; }
    .tabs::-webkit-scrollbar { display:none; }
    .tabs button { flex:0 0 auto; padding:10px 14px; font-size:13px; min-height:42px; }
    .bar { overflow-x:auto; flex-wrap:nowrap; scrollbar-width:none;
           -webkit-overflow-scrolling:touch; padding-bottom:3px; }
    .bar::-webkit-scrollbar { display:none; }
    .bar button, .bar select { flex:0 0 auto; padding:9px 14px; font-size:12.5px;
           min-height:40px; white-space:nowrap; }
    .search input { padding:12px 14px; }
    .card { padding:13px 14px; }
    .card h2 { font-size:14px; }
    .meta { gap:5px 10px; }
    .actions { margin-left:0; width:100%; margin-top:6px; }
    .meta button { padding:8px 13px; min-height:40px; font-size:12px; }
    .qrow { flex-wrap:wrap; row-gap:8px; padding:12px; }
    .qtext { flex:1 1 100%; white-space:normal; overflow:visible; }
    .qrow input[type=date], .qrow input[type=time] { padding:9px 10px; font-size:13px; }
    .qrow button { min-height:40px; }
    .mbox { padding:18px 14px 16px; border-radius:14px; }
    .mrow .lbl { width:100%; }
    .mfoot { flex-wrap:wrap; gap:8px; }
    .mfoot .btn, .mfoot .ghost, .mfoot .danger { min-height:44px; flex:1 1 auto; }
    .btn, .ghost { min-height:42px; }
    .typecards { grid-template-columns:1fr; }
    .typecard { flex-direction:row; align-items:center; gap:12px; padding:14px; }
    .typecard .te { font-size:22px; }
    .typecard span { flex:1; }
    .tplgrid { grid-template-columns:1fr 1fr; gap:9px; }
    .tplcard { padding:13px 12px 11px; }
    .tplcard .te { font-size:20px; }
    .panel { padding:16px 14px; }
    .genrow input, .genrow select { flex:1 1 100%; width:100%; }
    .genrow .bar { width:100%; }
    .wstep { gap:10px; margin:16px 0; }
    .wnum { width:24px; height:24px; font-size:11.5px; }
    .homecols { grid-template-columns:1fr; }
    .pickrow .btn { margin-left:0; width:100%; }
    .statgrid { grid-template-columns:1fr 1fr; gap:9px; }
    .scard { padding:13px 14px; }
    .scard .n { font-size:21px; }
    .toppick h2 { font-size:17px; }
    .calgrid { grid-template-columns:1fr 1fr; }
    .calcell { min-height:96px; }
    .chkrow { flex-direction:column; align-items:flex-start; gap:11px; }
    .chk { min-height:30px; }
    .qa { min-height:48px; }
    .pipe { padding:12px 4px; }
    .ideagrid { grid-template-columns:1fr; }
    #promptbox, .scriptbox pre { font-size:11px; }
  }
  @media (max-width:400px) {
    .tplgrid { grid-template-columns:1fr; }
    .statgrid { grid-template-columns:1fr 1fr; }
    .calgrid { grid-template-columns:1fr; }
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
      <button id="tabbtn-editors" onclick="switchTab('editors')">Editors</button>
    </nav>
    <button class="themebtn" id="cloudbtn" onclick="cloudClick()" title="Live sync">☁️</button>
    <button class="themebtn" id="rolebtn" onclick="roleSwitch(event)" title="Owner / editor mode">👤</button>
    <button class="themebtn" id="themebtn" onclick="toggleTheme()" title="Light / dark theme">🌙</button>
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
        <button class="qa" onclick="qaShort()">🎬 Create a short video</button>
        <button class="qa" onclick="qaX()">💬 Create an X post</button>
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
      <button class="btn" id="newpostbtn" style="margin-left:auto" onclick="openComposer(null)">+ New post</button>
      <button class="ghost" onclick="exportPlans()">⬇</button>
      <button class="ghost" onclick="document.getElementById('importfile').click()">⬆</button>
      <input type="file" id="importfile" accept=".json" hidden>
    </div>
    <div id="boardview"></div>
  </section>

  <section id="tab-editors" hidden>
    <div class="addrow" style="align-items:center;margin-top:20px">
      <div class="bar" id="ednav" style="margin:0"></div>
      <button class="ghost" style="margin-left:auto" title="Download board file" onclick="exportPlans()">⬇</button>
      <button class="ghost" title="Import board file" onclick="document.getElementById('importfile').click()">⬆</button>
    </div>
    <div id="edwork"></div>
  </section>

</div>

<div id="modal" hidden>
  <div class="mbox">
    <div class="mrow" style="margin-top:0"><span class="lbl">Channels</span>
      <span class="mplats" id="m-plats"></span></div>
    <textarea id="m-title" style="width:100%;min-height:120px;font-size:14px"
      placeholder="Write your post / video title… (ya template chuno 👇)"></textarea>
    <div class="mrow"><span class="lbl">Template</span>
      <select id="m-tpl" style="flex:1"><option value="">— quick caption fill —</option></select>
      <button class="ghost" style="padding:8px 13px;font-size:12px"
        onclick="composerToWizard()">✨ Full wizard</button></div>
    <div class="mrow"><span class="lbl">Link</span>
      <input type="text" id="m-url" style="flex:1" placeholder="https://… story or video link (optional)"></div>
    <div class="mrow"><span class="lbl">Schedule</span>
      <input type="date" id="m-date"><input type="time" id="m-time" value="18:00">
      <select id="m-status">
        <option value="idea">💡 Idea</option><option value="script">✍️ Script</option>
        <option value="filming">🎥 Filming</option><option value="editing">✂️ Editing</option>
        <option value="publish">🗓 Publish</option><option value="scheduled">🗓 Scheduled</option>
        <option value="posted">✅ Posted</option>
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
/* ---- repair URL: site/?fix=1 resets this device (role + sync) — board data stays ---- */
if (/[?&]fix=1/.test(location.search)) {
  ["role", "synccfg", "syncid", "boardrev", "edunlock"].forEach(k => localStorage.removeItem(k));
  location.replace(location.pathname);
}

/* ---- editor private link: site/#editor=<id>.<hash>.<syncid>.<name> shows ONLY a password box ---- */
const _edm = location.hash.match(/editor=(\w+)(?:\.([0-9a-f]*))?(?:\.([A-Za-z0-9-]*))?(?:\.([^&]*))?/) || [];
const EDLINK = _edm[1] || "";
const EDKEY = _edm[2] || "";
const EDSYNC = (_edm[3] && /^[0-9a-f]{6,40}$/.test(_edm[3])) ? _edm[3] : "";
const EDNAME = _edm[4] ? decodeURIComponent(_edm[4]) : "";
/* sync config travels in &s= (Firebase) or the legacy syncid segment (bin) */
const _esm = location.hash.match(/[#&]s=([^&]+)/);
const EDSYNCCFG = _esm ? decodeURIComponent(_esm[1]) : (EDSYNC ? "bin:" + EDSYNC : "");
function edGateShow(msg) {
  const ed = edById(EDLINK);
  const name = (ed && ed.name) || EDNAME || "Editor";
  const canCheck = (ed && ed.ph) || EDKEY;
  const box = document.querySelector("#lock .lockbox");
  document.getElementById("lock").hidden = false;
  box.innerHTML = '<div class="orb">A</div>' +
    "<h2>✂️ Editor login</h2>" +
    (canCheck
      ? "<p>Hi <b>" + esc(name) + "</b> — enter the password the owner gave you.</p>" +
        '<div class="err" id="edlockerr">' + (msg || "") + "</div>" +
        '<input id="edlockpass" type="password" placeholder="your password" autocomplete="off">' +
        '<button class="btn" style="width:100%;margin-top:8px" onclick="edTryUnlock()">Enter workspace</button>'
      : "<p>This link is outdated — ask the owner for a fresh link.</p>");
  const inp = document.getElementById("edlockpass");
  if (inp) {
    inp.focus();
    inp.addEventListener("keydown", e => { if (e.key === "Enter") edTryUnlock(); });
  }
}
async function edTryUnlock() {
  let ed = edById(EDLINK);
  const hash = await sha256((document.getElementById("edlockpass").value || "").trim());
  const valid = (ed && ed.ph && hash === ed.ph) || (EDKEY && hash === EDKEY);
  if (!valid) {
    document.getElementById("edlockerr").textContent = "Wrong password — try again.";
    return;
  }
  if (!ed) {            /* first visit on a fresh device: workspace from the link itself */
    ed = { id: EDLINK, name: EDNAME || "Editor", ph: EDKEY };
    editors.push(ed);
    saveEditors();
  }
  localStorage.setItem("edunlock", hash);
  ROLE = ed.id;
  localStorage.setItem("role", ROLE);
  document.getElementById("lock").hidden = true;
  applyRole();
  toast("Welcome, " + ed.name + " ✂️");
}

/* ---- theme ---- */
if (localStorage.getItem("theme") === "dark") {
  document.body.classList.add("dark");
  document.getElementById("themebtn").textContent = "☀️";
}
function toggleTheme() {
  const dark = document.body.classList.toggle("dark");
  localStorage.setItem("theme", dark ? "dark" : "light");
  document.getElementById("themebtn").textContent = dark ? "☀️" : "🌙";
}

if (!EDLINK && LOCKHASH && localStorage.getItem("unlock") !== LOCKHASH) {
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
let pillar = 0, hideDone = false, hotOnly = false, localOnly = false, mode = "worthy", q = "", shown = PAGE;
let assFilter = "All", editingId = null;
const doneSet = new Set(JSON.parse(localStorage.getItem("done") || "[]"));
let plans = JSON.parse(localStorage.getItem("plans") || "[]");
let etasks = JSON.parse(localStorage.getItem("etasks") || "[]");
function saveEtasks() { localStorage.setItem("etasks", JSON.stringify(etasks)); schedulePush(); }

/* ---- multiple editors: each has own workspace, notes, history; role = owner or one editor ---- */
let editors = JSON.parse(localStorage.getItem("editors") || "[]");
let enotes = JSON.parse(localStorage.getItem("enotes") || "{}");
let ehist = JSON.parse(localStorage.getItem("ehist") || "[]");
let ROLE = localStorage.getItem("role") || "owner";
function saveEditors() { localStorage.setItem("editors", JSON.stringify(editors)); schedulePush(); }
function saveEnotes() { localStorage.setItem("enotes", JSON.stringify(enotes)); schedulePush(); }
function saveEhist() { localStorage.setItem("ehist", JSON.stringify(ehist)); schedulePush(); }
function edById(id) { return editors.find(e => e.id === id); }
function holderName(p) {
  return p.assignee === "Editor" ? (edById(p.eid) || { name: "Editor" }).name : "Ahmad";
}
/* legacy items assigned to the old single "Editor" get adopted by the first editor */
function adoptOrphans(eid) {
  etasks.forEach(t => { if (!t.eid) t.eid = eid; });
  plans.forEach(p => { if (p.assignee === "Editor" && !p.eid) p.eid = eid; });
  saveEtasks(); savePlans();
}
if (editors.length) adoptOrphans(editors[0].id);
if (ROLE !== "owner" && !edById(ROLE)) { ROLE = "owner"; localStorage.setItem("role", "owner"); }
/* an item with an editor is never a bare "idea" — their sequence starts at Script */
plans.forEach(p => { if (p.assignee === "Editor" && p.status === "idea") p.status = "script"; });

/* ---- live cloud sync ----
   Backends: "fb:<databaseURL>|<secret>"  -> Firebase Realtime Database (recommended,
             instant updates via stream)  |  "bin:<id>" -> free public JSON bin.   */
let SYNCCFG = localStorage.getItem("synccfg") || "";
if (!SYNCCFG && localStorage.getItem("syncid")) {        /* migrate older bin sync */
  SYNCCFG = "bin:" + localStorage.getItem("syncid");
  localStorage.setItem("synccfg", SYNCCFG);
}
if (EDSYNCCFG && EDSYNCCFG !== SYNCCFG) {                /* editor link carries the config */
  SYNCCFG = EDSYNCCFG;
  localStorage.setItem("synccfg", SYNCCFG);
}
let boardRev = +(localStorage.getItem("boardrev") || 0);
let pushTimer = null, syncBusy = false, syncReady = !SYNCCFG, pollTick = 0, syncStream = null;
function isFb() { return SYNCCFG.slice(0, 3) === "fb:"; }
function syncURL() {
  if (isFb()) {
    const parts = SYNCCFG.slice(3).split("|");
    return parts[0].replace(/\/+$/, "") + "/boards/" + (parts[1] || "") + ".json";
  }
  if (SYNCCFG.slice(0, 4) === "bin:") return "https://extendsclass.com/api/json-storage/bin/" + SYNCCFG.slice(4);
  return "";
}

function boardState() {
  return { rev: Date.now(), plans: plans, etasks: etasks, editors: editors, enotes: enotes, ehist: ehist };
}
function applyBoard(data) {
  if (!data || typeof data !== "object") return;
  if (Array.isArray(data.plans)) plans = data.plans;
  if (Array.isArray(data.etasks)) etasks = data.etasks;
  if (Array.isArray(data.editors)) editors = data.editors;
  if (data.enotes && typeof data.enotes === "object") enotes = data.enotes;
  if (Array.isArray(data.ehist)) ehist = data.ehist;
  localStorage.setItem("plans", JSON.stringify(plans));
  localStorage.setItem("etasks", JSON.stringify(etasks));
  localStorage.setItem("editors", JSON.stringify(editors));
  localStorage.setItem("enotes", JSON.stringify(enotes));
  localStorage.setItem("ehist", JSON.stringify(ehist));
}
function setCloudIcon(ok) {
  const b = document.getElementById("cloudbtn");
  if (!b) return;
  b.style.opacity = SYNCCFG ? "1" : ".35";
  b.textContent = SYNCCFG && ok === false ? "⚠️" : isFb() ? "⚡" : "☁️";
  b.title = !SYNCCFG ? "Live sync OFF — click to enable"
    : ok === false ? "Live sync: connection problem"
    : isFb() ? "Firebase live sync ON — instant updates" : "Live sync ON — updates within seconds";
}
function applyRemote(data) {
  if (!(data && data.rev && data.rev > boardRev)) return;
  applyBoard(data);
  boardRev = data.rev;
  localStorage.setItem("boardrev", "" + boardRev);
  rerender();
  if (!document.getElementById("tab-home").hidden) renderHome();
}
function schedulePush() {
  if (!SYNCCFG || !syncReady) return;
  clearTimeout(pushTimer);
  pushTimer = setTimeout(pushBoard, 1200);
}
async function pushBoard() {
  if (!SYNCCFG) return false;
  const state = boardState();
  boardRev = state.rev;
  localStorage.setItem("boardrev", "" + boardRev);
  try {
    const r = await fetch(syncURL(), { method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state) });
    setCloudIcon(r.ok);
    return r.ok;
  } catch (e) { setCloudIcon(false); return false; }
}
async function pollBoard() {
  if (!SYNCCFG || syncBusy) return;
  syncBusy = true;
  try {
    const r = await fetch(syncURL());
    if (r.ok) {
      applyRemote(await r.json());
      setCloudIcon(true);
    } else { setCloudIcon(false); }
  } catch (e) { setCloudIcon(false); }
  syncBusy = false;
}
/* Firebase streams changes instantly — no waiting on the poll */
function startStream() {
  if (!isFb() || syncStream) return;
  try {
    syncStream = new EventSource(syncURL());
    syncStream.addEventListener("put", e => {
      try {
        const m = JSON.parse(e.data);
        if (m && m.path === "/" && m.data) {
          applyRemote(m.data);
          setCloudIcon(true);
        }
      } catch (err) {}
    });
    syncStream.onerror = () => setCloudIcon(false);
  } catch (e) { syncStream = null; }
}
async function enableSync() {
  const url = (prompt(
    "RECOMMENDED — Firebase Realtime Database URL yahan paste karo\n" +
    "(console.firebase.google.com → Realtime Database → Data tab ka URL)\n\n" +
    "Ya EMPTY chhod do → quick free bin use hoga:") || "").trim();
  if (url) {
    if (!/^https:\/\/[\w.-]+\.(firebasedatabase\.app|firebaseio\.com)\/?$/.test(url)) {
      toast("That doesn't look like a Firebase database URL ❌");
      return;
    }
    const secret = [...crypto.getRandomValues(new Uint8Array(20))]
      .map(b => b.toString(16).padStart(2, "0")).join("");
    SYNCCFG = "fb:" + url.replace(/\/+$/, "") + "|" + secret;
    localStorage.setItem("synccfg", SYNCCFG);
    syncReady = true;
    if (!await pushBoard()) {
      SYNCCFG = "";
      localStorage.removeItem("synccfg");
      setCloudIcon(true);
      toast("Firebase ne mana kar diya — Rules me boards read/write true karo, phir retry");
      return;
    }
    startStream();
    rerender();
    toast("Firebase live sync ON ⚡ — copy FRESH links for your editors");
    return;
  }
  try {
    const r = await fetch("https://extendsclass.com/api/json-storage/bin", { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(boardState()) });
    const id = ((await r.json()) || {}).id || "";
    if (!id) throw new Error("no id");
    SYNCCFG = "bin:" + id;
    syncReady = true;
    localStorage.setItem("synccfg", SYNCCFG);
    setCloudIcon(true);
    rerender();
    toast("Live sync ON ☁️ — now copy FRESH links for your editors");
  } catch (e) {
    toast("Sync service not reachable — try again in a minute");
  }
}
async function cloudClick() {
  if (!SYNCCFG) {
    if (ROLE !== "owner") { toast("Ask the owner to enable live sync"); return; }
    enableSync();
    return;
  }
  if (ROLE === "owner" &&
      confirm("Live sync is ON (" + (isFb() ? "Firebase ⚡" : "free bin ☁️") +
        ").\n\nOK = reconnect / switch backend (e.g. move to Firebase)\nCancel = just check the connection")) {
    if (syncStream) { syncStream.close(); syncStream = null; }
    enableSync();
    return;
  }
  pollBoard();
  toast(isFb() ? "Firebase live sync ON ⚡ — updates are instant" :
    "Live sync ON ☁️ — changes appear within seconds");
}
setInterval(() => {
  pollTick++;
  /* the stream covers Firebase; poll it rarely as a safety net (saves quota) */
  if (isFb() && syncStream && pollTick % 30 !== 0) return;
  pollBoard();
}, 10000);
window.addEventListener("focus", () => { if (!(isFb() && syncStream)) pollBoard(); });

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
if (localStorage.getItem("plans_v") !== "4") {
  plans = plans.map(p => Object.assign(p, {
    status: p.status === "draft" ? "script" : p.status,
    ctype: p.ctype || "", chk: p.chk || {}, ftitle: p.ftitle || "",
  }));
  localStorage.setItem("plans_v", "4");
  localStorage.setItem("plans", JSON.stringify(plans));
}

function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg; t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 1900);
}
function savePlans() { localStorage.setItem("plans", JSON.stringify(plans)); schedulePush(); }
function switchTab(name) {
  if (ROLE !== "owner") name = "editors";   /* editors only see their workspace */
  ["home","news","trends","research","plan","editors"].forEach(n => {
    document.getElementById("tab-" + n).hidden = n !== name;
    document.getElementById("tabbtn-" + n).classList.toggle("active", n === name);
  });
  if (name === "home") renderHome();
  if (name === "plan") renderBoard();
  if (name === "editors") renderEditorsTab();
  if (name === "research") renderResearch();
}
/* re-render whichever workspace is on screen */
function rerender() {
  if (!document.getElementById("tab-editors").hidden) renderEditorsTab();
  else if (!document.getElementById("tab-plan").hidden) renderBoard();
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
    (!localOnly || it.lo) &&
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
    d.querySelector(".prep-btn").onclick = () => openCreate(it.t, it.u);
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
  const loc = document.createElement("button");
  loc.innerHTML = "🇵🇰🇮🇳 Local";
  loc.className = localOnly ? "active" : "";
  loc.onclick = () => { localOnly = !localOnly; shown = PAGE; bar(); render(); };
  el.appendChild(loc);
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
let boardView = "ideas", calOffset = 0, edView = "work", edSel = "";

function addPlan(title, url) {
  plans.unshift({ id: Date.now(), title, url: url || "", notes: "",
    status: "idea", assignee: "Ahmad", platforms: ["yt", "shorts"], when: "" });
  savePlans();
  toast("Saved to Ideas 💡");
}

function edOpenCount(ed) {
  return etasks.filter(t => t.eid === ed.id && !t.done).length +
    plans.filter(p => p.assignee === "Editor" && p.eid === ed.id && p.status !== "posted").length;
}

function boardNav() {
  const el = document.getElementById("boardnav");
  el.innerHTML = "";
  /* items handed to an editor live in the Editors tab, not here */
  const cnt = s => plans.filter(p => p.status === s && p.assignee !== "Editor").length;
  const counts = { ideas: cnt("idea"), script: cnt("script"), filming: cnt("filming"),
    editing: cnt("editing"),
    publish: plans.filter(p => p.assignee !== "Editor" &&
      ((p.status === "publish" && !p.eready) || p.status === "scheduled")).length,
    posted: cnt("posted") };
  const steps = [["ideas","\uD83D\uDCA1 Ideas"],["script","\u270D\uFE0F Script"],
    ["filming","\uD83C\uDFA5 Filming"],["editing","\u2702\uFE0F Editing"],
    ["publish","\uD83D\uDDD3 Publish"],["posted","\u2705 Posted"]];
  steps.forEach(([k, label], i) => {
    const b = document.createElement("button");
    b.innerHTML = label + (counts[k] ? " \u00B7 " + counts[k] : "");
    b.className = boardView === k ? "active" : "";
    b.onclick = () => { boardView = k; renderBoard(); };
    el.appendChild(b);
    if (i < steps.length - 1) {
      const a = document.createElement("span");
      a.textContent = "\u2192";
      a.style.cssText = "color:var(--faint);font-size:12px";
      el.appendChild(a);
    }
  });
  const sep = document.createElement("span");
  sep.textContent = "\u00b7";
  sep.style.cssText = "color:var(--faint);margin:0 2px";
  el.appendChild(sep);
  const asg = plans.filter(p => p.assignee === "Editor").length;
  const ab = document.createElement("button");
  ab.innerHTML = "\ud83d\udccc Assigned" + (asg ? " \u00b7 " + asg : "");
  ab.className = boardView === "assigned" ? "active" : "";
  ab.onclick = () => { boardView = "assigned"; renderBoard(); };
  el.appendChild(ab);
  const rdy = plans.filter(p => p.eready && p.status === "publish").length;
  const rb = document.createElement("button");
  rb.innerHTML = "\ud83d\udcec Ready to Post" + (rdy ? " \u00b7 " + rdy : "");
  rb.className = boardView === "ready" ? "active" : "";
  rb.onclick = () => { boardView = "ready"; renderBoard(); };
  el.appendChild(rb);
}

function renderBoard() {
  /* workspace handlers call renderBoard(); route to whichever tab is on screen */
  if (!document.getElementById("tab-editors").hidden) { renderEditorsTab(); return; }
  if (ROLE !== "owner") return;            /* Buffer is owner-only */
  boardNav();
  const el = document.getElementById("boardview");
  el.innerHTML = "";
  if (boardView === "ideas") renderIdeas(el);
  else if (boardView === "script") renderScriptView(el);
  else if (boardView === "filming") renderStageView(el, "filming", "editing", "Done → Editing", "Nothing in Filming — finish a Script first.");
  else if (boardView === "editing") renderStageView(el, "editing", "publish", "Done → Publish", "Nothing in Editing yet.");
  else if (boardView === "publish") renderPublish(el);
  else if (boardView === "assigned") renderAssignedView(el);
  else if (boardView === "ready") renderReadyView(el);
  else renderList(el, ["posted"], "Nothing posted yet — your history will appear here.");
}

/* ---- Create wizard: topic -> type -> platforms -> settings -> template -> Claude -> save ---- */
let wiz = { topic: "", url: "", type: null, plats: [], dur: "60",
            len: "4-6 min news explainer", tpl: null, prompt: "" };
let tplLang = localStorage.getItem("tpl_lang") || "ur";
let wizBind = null;
const WIZ_PLATS = {
  short: [["yt","YT Shorts"],["tiktok","TikTok"],["ig","IG Reels"],["fb","FB Reels"]],
  long:  [["yt","YouTube"],["fb","Facebook"]],
  post:  [["x","X"],["ig","Instagram"],["fb","Facebook"],["li","LinkedIn"],["wa","WhatsApp"]],
};
const POST_RULES = {
  x:  "X (Twitter): under 280 characters, invites replies, max 1-2 hashtags (more kills reach on X in 2026).",
  ig: "Instagram: scroll-stopping first line, 3-5 short lines, MAX 5 hashtags (Instagram's 2026 hard limit) - use 3-4 niche + 1 broad.",
  fb: "Facebook: very simple words, broad family audience, discussion-friendly, 1-3 hashtags only.",
  li: "LinkedIn: 4-6 lines, professional but warm, one insight + one question, 3-5 hashtags in PascalCase (e.g. #ArtificialIntelligence).",
  wa: "WhatsApp Channel: 2-3 lines, personal tone like messaging friends, link placeholder, no hashtags.",
};
const SHORT_STYLE = {
  yt: "YouTube Shorts style (2026): 30-45s is the retention sweet spot (max 3 min allowed), loop-friendly ending (last line connects to the first), clean on-screen hook text.",
  tiktok: "TikTok native style (2026): 21-34s gets highest engagement, casual and fast, on-screen text per scene, trend-aware.",
  ig: "Instagram Reels style (2026): 30-45s value sweet spot, aesthetic opening frame idea, caption with 2-3 hashtags only (IG limit is 5).",
  fb: "Facebook Reels style: very simple words, broad audience, caption with 1-3 hashtags.",
};
const SHORT_HINT = {
  yt: "YT Shorts: 30-45s ideal, loop ending", tiktok: "TikTok: 21-34s sweet spot, casual",
  ig: "IG Reels: 30-45s, max 2-3 hashtags", fb: "FB Reels: simple words, broad audience",
};

/* ---- pipeline stage views: Filming, Editing, Publish ---- */
const STAGE_CHK = {
  script: [["draft","Draft written"],["final","Final script ready"]],
  filming: [["title","Final title decided"],["poster","Thumbnail / poster made"],["footage","Footage recorded"]],
  editing: [["cut","Rough cut done"],["captions","Captions added"],["export","Final export ready"]],
};
let pubCal = false;

function renderScriptView(el, ed) {
  /* same script wizard for owner and editor — only the item pool differs */
  const inProg = ed
    ? plans.filter(p => p.status === "script" && p.assignee === "Editor" && p.eid === ed.id)
    : plans.filter(p => p.status === "script" && p.assignee !== "Editor");
  if (ed) {
    if (!inProg.length) {
      el.innerHTML = '<div class="empty">No script work right now — assigned topics land here.</div>';
      return;
    }
    if (!inProg.some(p => p.id === wizBind)) {     /* auto-open rejected work first */
      const p0 = inProg.find(p => p.revnote) || inProg[0];
      wizBind = p0.id;
      wiz.topic = p0.title.split("\n")[0];
      wiz.url = p0.url || "";
      wiz.type = p0.ctype || null;
      wiz.plats = []; wiz.tpl = null; wiz.prompt = "";
    }
    const bp = plans.find(x => x.id === wizBind);
    if (bp && bp.revnote) {
      const rv = document.createElement("div");
      rv.style.cssText = "margin:0 0 10px;padding:10px 14px;border:1px solid var(--red);border-radius:10px;color:var(--red);font-size:13px";
      rv.innerHTML = "<b>🔁 Owner wants fixes:</b> " + esc(bp.revnote);
      el.appendChild(rv);
    }
  }
  if (inProg.length) {
    const box = document.createElement("div");
    box.className = "bar";
    box.style.marginTop = "0";
    const lab = document.createElement("span");
    lab.className = "whint";
    lab.textContent = "Working on:";
    box.appendChild(lab);
    inProg.forEach(p => {
      const b = document.createElement("button");
      b.textContent = (p.revnote ? "🔁 " : "✍️ ") + p.title.split("\n")[0].slice(0, 32);
      b.className = wizBind === p.id ? "active" : "";
      b.onclick = () => {
        wizBind = p.id;
        wiz.topic = p.title.split("\n")[0];
        wiz.url = p.url || "";
        wiz.type = p.ctype || null;
        wiz.plats = []; wiz.tpl = null; wiz.prompt = "";
        renderBoard();
      };
      box.appendChild(b);
    });
    if (!ed) {                       /* editors work on assigned topics only */
      const custom = document.createElement("button");
      custom.textContent = "+ Custom topic";
      custom.className = wizBind === null ? "active" : "";
      custom.onclick = () => {
        wizBind = null;
        wiz = { topic: "", url: "", type: null, plats: [], dur: "60",
                len: "4-6 min news explainer", tpl: null, prompt: "" };
        renderBoard();
      };
      box.appendChild(custom);
    }
    el.appendChild(box);
  }
  renderCreate(el);
}

function renderStageView(el, stage, nextStage, nextLabel, emptyMsg) {
  const items = plans.filter(p => p.status === stage && p.assignee !== "Editor");
  if (!items.length) { el.innerHTML = '<div class="empty">' + emptyMsg + "</div>"; return; }
  items.forEach(p => {
    p.chk = p.chk || {};
    const c = document.createElement("div");
    c.className = "panel";
    let inner = '<h3 style="color:var(--text)">' + esc(p.title.split("\n")[0]) +
      (p.ctype ? ' <span class="tag">' + p.ctype + "</span>" : "") + "</h3>";
    if (stage === "filming") {
      inner += '<div class="genrow"><input class="ftitle" style="flex:1;min-width:200px" placeholder="Final video title…" value="' + esc(p.ftitle || "") + '">' +
        '<button class="ghost poster-btn">🎨 Poster prompt</button></div>';
    }
    inner += '<div class="chkrow">' + STAGE_CHK[stage].map(([k, lab]) =>
      '<label class="chk"><input type="checkbox" data-k="' + k + '"' +
      (p.chk[k] ? " checked" : "") + "> " + lab + "</label>").join("") + "</div>";
    if (p.notes) inner += '<details class="scriptbox"><summary>📜 Script / content</summary><pre>' + esc(p.notes) + "</pre></details>";
    inner += '<div class="mfoot"><button class="btn next-btn">' + nextLabel + "</button>" +
      '<button class="ghost edit-btn">✎ Edit details</button>' +
      '<button class="ghost hand-btn">✂️ → Editor</button>' +
      '<button class="danger del-btn" style="margin-left:auto">🗑 Delete</button></div>';
    c.innerHTML = inner;
    const ft = c.querySelector(".ftitle");
    if (ft) ft.addEventListener("change", e => { p.ftitle = e.target.value; savePlans(); });
    const pb = c.querySelector(".poster-btn");
    if (pb) pb.onclick = () => {
      const prompt = 'Design 3 thumbnail/poster concepts for my video: "' +
        (p.ftitle || p.title.split("\n")[0]) +
        '" (AI x Ahmad — AI in simple Urdu, audience Pakistan/India). For each concept give: main poster text (max 4 words, Urdu/English mix), background idea, color scheme, my facial expression, one small visual element. Must be readable on a phone screen.';
      navigator.clipboard.writeText(prompt).then(() => toast("Poster prompt copied — paste in Claude 🎨"));
    };
    c.querySelectorAll(".chk input").forEach(cb => {
      cb.onchange = () => { p.chk[cb.dataset.k] = cb.checked; savePlans(); };
    });
    c.querySelector(".next-btn").onclick = () => {
      p.status = nextStage;
      savePlans();
      boardView = nextStage;
      renderBoard();
      toast("Moved ✓");
    };
    c.querySelector(".edit-btn").onclick = () => openComposer(p.id);
    c.querySelector(".hand-btn").onclick = ev => pickEditorMenu(ev, ed => sendToEditor(p, ed));
    c.querySelector(".del-btn").onclick = () => {
      if (confirm("Delete this item?")) {
        plans = plans.filter(x => x.id !== p.id);
        savePlans();
        renderBoard();
        toast("Deleted 🗑");
      }
    };
    el.appendChild(c);
  });
}

function renderPublish(el) {
  const top = document.createElement("div");
  top.className = "bar";
  top.style.marginTop = "0";
  [["list","🗒 List"],["cal","📅 Calendar"]].forEach(([k, lab]) => {
    const b = document.createElement("button");
    b.textContent = lab;
    b.className = (pubCal ? "cal" : "list") === k ? "active" : "";
    b.onclick = () => { pubCal = k === "cal"; renderBoard(); };
    top.appendChild(b);
  });
  el.appendChild(top);
  if (pubCal) { renderCalendar(el); return; }
  /* eready items wait in the Ready to Post tab until reviewed */
  const ready = plans.filter(p => p.status === "publish" && !p.eready && p.assignee !== "Editor");
  const sched = plans.filter(p => p.status === "scheduled" && p.when && p.assignee !== "Editor")
    .sort((a, b) => a.when.localeCompare(b.when));
  if (!ready.length && !sched.length) {
    const e2 = document.createElement("div");
    e2.className = "empty";
    e2.textContent = "Nothing here yet — items land here after Editing (videos) or Script (posts).";
    el.appendChild(e2);
    return;
  }
  if (ready.length) {
    const h = document.createElement("div");
    h.className = "qday";
    h.textContent = "Ready to schedule";
    el.appendChild(h);
    ready.forEach(p => {
      const d = document.createElement("div");
      d.className = "qrow";
      d.innerHTML = '<span class="qtext">' + esc(p.title.split("\n")[0].slice(0, 55)) + "</span>" +
        '<span class="qtags">' + platTags(p) + "</span>" +
        '<input type="date" class="pd"><input type="time" class="pt" value="18:00">' +
        '<button class="ghost sch">→ Schedule</button>' +
        '<button class="ghost rowdel">✕</button>';
      d.querySelector(".qtext").onclick = () => openComposer(p.id);
      d.querySelector(".rowdel").onclick = e => {
        e.stopPropagation();
        if (confirm("Delete this item?")) {
          plans = plans.filter(x => x.id !== p.id);
          savePlans(); renderBoard(); toast("Deleted 🗑");
        }
      };
      d.querySelector(".sch").onclick = e => {
        e.stopPropagation();
        const date = d.querySelector(".pd").value;
        if (!date) { toast("Pick a date first"); return; }
        p.when = date + "T" + (d.querySelector(".pt").value || "18:00");
        p.status = "scheduled";
        savePlans();
        renderBoard();
        toast("Scheduled 🗓");
      };
      el.appendChild(d);
    });
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
    const d = document.createElement("div");
    d.className = "qrow";
    d.innerHTML = '<span class="qtime">' + p.when.slice(11, 16) + "</span>" +
      '<span class="qtext">' + esc(p.title.split("\n")[0].slice(0, 55)) + "</span>" +
      '<span class="qtags">' + platTags(p) + "</span>" +
      '<button class="ghost donep">✓ Posted</button>' +
      '<button class="ghost rowdel">✕</button>';
    d.querySelector(".qtext").onclick = () => openComposer(p.id);
    d.querySelector(".donep").onclick = e => {
      e.stopPropagation();
      p.status = "posted";
      savePlans();
      renderBoard();
      toast("Posted ✅ Done!");
    };
    d.querySelector(".rowdel").onclick = e => {
      e.stopPropagation();
      if (confirm("Delete this item?")) {
        plans = plans.filter(x => x.id !== p.id);
        savePlans(); renderBoard(); toast("Deleted 🗑");
      }
    };
    el.appendChild(d);
  });
}

function openCreate(topic, url, preset, bindId) {
  wiz = { topic: topic || "", url: url || "",
          type: (preset && preset.type) || null,
          plats: (preset && preset.plats) ? preset.plats.slice() : [],
          dur: "60", len: "4-6 min news explainer", tpl: null, prompt: "" };
  wizBind = bindId || null;
  boardView = "script";
  switchTab("plan");
}

function wstep(el, n, title) {
  const d = document.createElement("div");
  d.className = "wstep";
  d.innerHTML = '<div class="wnum">' + n + '</div><div class="wbody"><h4>' + title + "</h4></div>";
  el.appendChild(d);
  return d.querySelector(".wbody");
}
function platName(k, type) {
  const f = (WIZ_PLATS[type] || []).find(x => x[0] === k);
  return f ? f[1] : k;
}

function renderCreate(el) {
  /* step 1: topic + language */
  const s1 = wstep(el, 1, "Topic");
  const r1 = document.createElement("div");
  r1.className = "genrow";
  r1.innerHTML =
    '<input id="wtopic" style="flex:2;min-width:200px" placeholder="Topic… e.g. Gemini 3 launch, AI for freelancers" value="' + esc(wiz.topic) + '">' +
    '<input id="wurl" style="flex:2;min-width:180px" placeholder="source link (optional)" value="' + esc(wiz.url) + '">' +
    '<span class="bar" style="margin:0">' +
    '<button id="wl-ur" class="' + (tplLang === "ur" ? "active" : "") + '">Roman Urdu</button>' +
    '<button id="wl-en" class="' + (tplLang === "en" ? "active" : "") + '">English</button></span>';
  s1.appendChild(r1);
  r1.querySelector("#wtopic").addEventListener("input", e => { wiz.topic = e.target.value; });
  r1.querySelector("#wurl").addEventListener("input", e => { wiz.url = e.target.value; });
  r1.querySelector("#wl-ur").onclick = () => { tplLang = "ur"; localStorage.setItem("tpl_lang", "ur"); renderBoard(); };
  r1.querySelector("#wl-en").onclick = () => { tplLang = "en"; localStorage.setItem("tpl_lang", "en"); renderBoard(); };

  /* step 2: content type */
  const s2 = wstep(el, 2, "What are you creating?");
  const tc = document.createElement("div");
  tc.className = "typecards";
  [["short","🎬","Short video","45-90 sec vertical — Shorts, TikTok, Reels"],
   ["long","📺","Long video","YouTube main video with chapters"],
   ["post","✍️","Post","Text post — X, IG, FB, LinkedIn, WhatsApp"]].forEach(([k, e2, n, d2]) => {
    const c = document.createElement("div");
    c.className = "typecard" + (wiz.type === k ? " on" : "");
    c.innerHTML = '<div class="te">' + e2 + "</div><b>" + n + "</b><span>" + d2 + "</span>";
    c.onclick = () => { wiz.type = k; wiz.plats = []; wiz.tpl = null; wiz.prompt = ""; renderBoard(); };
    tc.appendChild(c);
  });
  s2.appendChild(tc);
  if (!wiz.type) return;

  /* step 3: platforms (multi or all) */
  const s3 = wstep(el, 3, "Platforms — one, many, or all");
  const pb = document.createElement("div");
  pb.className = "bar";
  pb.style.margin = "0";
  const allKeys = WIZ_PLATS[wiz.type].map(x => x[0]);
  const all = document.createElement("button");
  all.textContent = "All";
  all.className = wiz.plats.length === allKeys.length ? "active" : "";
  all.onclick = () => {
    wiz.plats = wiz.plats.length === allKeys.length ? [] : allKeys.slice();
    wiz.tpl = null; wiz.prompt = ""; renderBoard();
  };
  pb.appendChild(all);
  WIZ_PLATS[wiz.type].forEach(([k, name]) => {
    const b = document.createElement("button");
    b.textContent = name;
    b.className = wiz.plats.includes(k) ? "active" : "";
    b.onclick = () => {
      wiz.plats = wiz.plats.includes(k)
        ? wiz.plats.filter(x => x !== k) : wiz.plats.concat(k);
      wiz.tpl = null; wiz.prompt = ""; renderBoard();
    };
    pb.appendChild(b);
  });
  s3.appendChild(pb);
  if (!wiz.plats.length) return;

  /* step 4: settings (videos only) - general for many, tuned for one */
  let nextStep = 4;
  if (wiz.type === "short" || wiz.type === "long") {
    const single = wiz.plats.length === 1;
    const s4 = wstep(el, nextStep++, "Settings" +
      (single ? " — tuned for " + platName(wiz.plats[0], wiz.type)
              : " — general, works on all selected"));
    const row = document.createElement("div");
    row.className = "genrow";
    row.style.alignItems = "center";
    const sel = document.createElement("select");
    if (wiz.type === "short") {
      ["30","45","60","75","90"].forEach(d2 => {
        sel.innerHTML += '<option value="' + d2 + '"' + (wiz.dur === d2 ? " selected" : "") + ">" + d2 + " seconds</option>";
      });
      sel.onchange = e => { wiz.dur = e.target.value; wiz.prompt = ""; };
    } else {
      ["4-6 min news explainer","8-12 min tutorial","12-20 min deep dive"].forEach(d2 => {
        sel.innerHTML += "<option" + (wiz.len === d2 ? " selected" : "") + ">" + d2 + "</option>";
      });
      sel.onchange = e => { wiz.len = e.target.value; wiz.prompt = ""; };
    }
    row.appendChild(sel);
    if (single && wiz.type === "short") {
      const hint = document.createElement("span");
      hint.className = "whint";
      hint.textContent = SHORT_HINT[wiz.plats[0]] || "";
      row.appendChild(hint);
    }
    s4.appendChild(row);
  }

  /* step 5: templates filtered by type + platforms */
  const s5 = wstep(el, nextStep, "Pick a template");
  const grid = document.createElement("div");
  grid.className = "tplgrid";
  let list = (window.WIZ || []).filter(t => t.type === wiz.type &&
    (t.plats[0] === "*" || t.plats.some(p => wiz.plats.includes(p))));
  if (wiz.plats.length === 1) {
    const k = wiz.plats[0];
    list.sort((a, b) => (b.plats.includes(k) ? 1 : 0) - (a.plats.includes(k) ? 1 : 0));
  }
  list.forEach(t => {
    const c = document.createElement("div");
    c.className = "tplcard" + (wiz.tpl === t ? " on" : "");
    c.innerHTML = '<div class="te">' + t.emoji + '</div><div class="tn">' + esc(t.name) +
      '</div><div class="td">' + esc(t.desc) + "</div>" +
      (t.plats[0] !== "*"
        ? '<span class="tag">' + t.plats.map(p => platName(p, wiz.type)).join(" · ") + "</span>"
        : '<span class="tag">general</span>');
    c.onclick = () => { wiz.tpl = t; buildWiz(); };
    grid.appendChild(c);
  });
  s5.appendChild(grid);

  /* step 6: output */
  if (wiz.prompt) {
    const out = document.createElement("div");
    out.className = "panel";
    out.id = "wizout";
    out.innerHTML =
      "<h3>" + wiz.tpl.emoji + " " + esc(wiz.tpl.name) +
      ' <button class="ghost" style="padding:5px 14px;font-size:12px" onclick="copyWiz()">📋 Copy again</button></h3>' +
      '<p class="sub">1) Paste in your <b>Claude app</b> → 2) create the content, edit in canvas, make your poster → 3) paste the FINAL version below and save. (Google Drive save coming later.)</p>' +
      '<textarea id="wizprompt" readonly style="width:100%;min-height:140px;font:12px/1.6 Consolas,monospace;background:var(--surface2)">' + esc(wiz.prompt) + "</textarea>" +
      '<p class="sub" style="margin-top:14px"><b>Final version</b> (from Claude, after your edits):</p>' +
      '<textarea id="wizfinal" style="width:100%;min-height:120px" placeholder="Paste your final content here…"></textarea>' +
      '<div class="mfoot"><button class="btn" onclick="saveWiz()">✅ Script done → Filming 🎥</button>' +
      '<button class="ghost" onclick="downloadWiz()">⬇ Download file</button></div>';
    el.appendChild(out);
  }
}

function brandHeader() {
  const lang = tplLang === "ur"
    ? "OUTPUT LANGUAGE: simple Roman Urdu with light English (easy to read while filming)."
    : "OUTPUT LANGUAGE: simple, friendly English (no heavy jargon).";
  return 'You are the content writer for "AI x Ahmad" (@aixahmad) — AI explained simply for everyday people in Pakistan and India (students, freelancers, shopkeepers). No jargon, friendly tone, energy high.\n' + lang +
    "\nRULES: facts must come from the source link or be clearly true — never invent. Pacing beats length: every line must earn the next second. Hashtag limits: X 1-2, Instagram max 5, LinkedIn 3-5 PascalCase, Facebook 1-3.\n\n";
}
function typeRules() {
  const names = wiz.plats.map(k => platName(k, wiz.type)).join(", ");
  if (wiz.type === "short") {
    let r = "CONTENT TYPE: vertical short-video script (9:16) for: " + names +
      ". DURATION: " + wiz.dur + " seconds — spoken words MUST fit. " +
      "Base structure: HOOK (0-3s) -> body -> PK/IN local angle -> CTA follow @aixahmad. Add [B-ROLL] notes.";
    if (wiz.plats.length === 1) r += " " + SHORT_STYLE[wiz.plats[0]];
    else r += " Make ONE script that works on all of them, then give caption + hashtags adapted per platform.";
    return r;
  }
  if (wiz.type === "long") {
    let r = "CONTENT TYPE: long YouTube video script. LENGTH: " + wiz.len +
      ". Structure: 20-second hook, sections with [timestamps] + [B-ROLL], simple examples, PK/IN local angle, 3-point recap, outro CTA (subscribe + WhatsApp channel). Also give 3 title options + description + 15 tags.";
    if (wiz.plats.includes("fb")) r += " Also give a 1-paragraph Facebook video description.";
    return r;
  }
  if (wiz.plats.length === 1) return "CONTENT TYPE: text post. " + POST_RULES[wiz.plats[0]];
  return "CONTENT TYPE: text post for: " + names + ". Write ONE core post first, then adapt it for each platform:\n" +
    wiz.plats.map(k => "- " + platName(k, "post") + ": " + POST_RULES[k]).join("\n");
}
function buildWiz() {
  const ti = document.getElementById("wtopic");
  const ui = document.getElementById("wurl");
  if (ti) wiz.topic = ti.value;
  if (ui) wiz.url = ui.value;
  if (!wiz.topic.trim()) { toast("Pehle topic likho 👆"); return; }
  let p = brandHeader() + "TOPIC: " + wiz.topic.trim() + "\n";
  if (wiz.url.trim()) p += "SOURCE LINK: " + wiz.url.trim() + " (open and read it first)\n";
  p += "\n" + typeRules() + "\n\nTEMPLATE / FORMAT:\n" +
    wiz.tpl.body.split("{topic}").join(wiz.topic.trim());
  if (wiz.type !== "post") p += relatedBlock(wiz.topic, wiz.url);
  wiz.prompt = p;
  renderBoard();
  navigator.clipboard.writeText(p).then(() => toast("Prompt copied — paste in Claude 🤖"));
  const out = document.getElementById("wizout");
  if (out) out.scrollIntoView({ behavior: "smooth" });
}
function copyWiz() {
  navigator.clipboard.writeText(wiz.prompt).then(() => toast("Copied 📋"));
}
function saveWiz() {
  const fin = document.getElementById("wizfinal");
  const txt = fin ? fin.value.trim() : "";
  if (!txt) { toast("Paste the final version first"); return; }
  let plats = wiz.plats.slice();
  if (wiz.type === "short") plats = plats.map(k => k === "yt" ? "shorts" : k);
  let p = wizBind ? plans.find(x => x.id === wizBind) : null;
  if (p) {
    p.notes = txt;
    p.platforms = plats.length ? plats : p.platforms;
    p.ctype = wiz.type;
    p.url = wiz.url || p.url;
  } else {
    p = { id: Date.now(), title: wiz.topic, url: wiz.url, notes: txt,
      status: "script", assignee: "Ahmad", platforms: plats, when: "",
      ctype: wiz.type, chk: {}, ftitle: "" };
    plans.unshift(p);
  }
  wizBind = null;
  if (p.assignee === "Editor") {       /* assigned work ALWAYS runs the full sequence:
                                          script -> filming -> editing -> ready */
    p.status = "filming";
    savePlans();
    edView = "filming";
    renderBoard();
    toast("Script done \u2192 Filming \uD83C\uDFA5");
    return;
  }
  p.status = "filming";                /* owner follows the same sequence too */
  savePlans();
  boardView = "filming";
  renderBoard();
  toast("Script done \u2192 Filming \uD83C\uDFA5");
}
function downloadWiz() {
  const fin = document.getElementById("wizfinal");
  const txt = fin ? fin.value.trim() : "";
  if (!txt) { toast("Paste the final version first"); return; }
  const blob = new Blob([txt], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = (wiz.topic || "content").replace(/[^\w\s-]/g, "").slice(0, 40) + ".txt";
  a.click();
  toast("Downloaded — drop it into your Drive folder");
}

/* ---- assign work: the owner picks which editor gets the item ---- */
function closeEdMenu() {
  const m = document.getElementById("edmenu");
  if (m) m.remove();
}
function pickEditorMenu(ev, cb) {
  if (!editors.length) {
    addEditor().then(ok => { if (ok && editors.length) cb(editors[editors.length - 1]); });
    return;
  }
  if (editors.length === 1) { cb(editors[0]); return; }
  closeEdMenu();
  const m = document.createElement("div");
  m.id = "edmenu";
  m.style.cssText = "position:fixed;z-index:99;background:var(--surface);border:1px solid var(--line);" +
    "border-radius:10px;box-shadow:var(--shadow-sm);padding:6px;display:flex;flex-direction:column;gap:4px;min-width:150px";
  const x = ev && ev.clientX ? ev.clientX : innerWidth / 2;
  const y = ev && ev.clientY ? ev.clientY : 90;
  m.style.left = Math.min(x, innerWidth - 180) + "px";
  m.style.top = Math.min(y, innerHeight - 40 * editors.length - 20) + "px";
  editors.forEach(ed => {
    const b = document.createElement("button");
    b.className = "ghost";
    b.style.cssText = "padding:7px 12px;font-size:12.5px;text-align:left";
    b.textContent = "✂️ " + ed.name;
    b.onclick = e => { e.stopPropagation(); closeEdMenu(); cb(ed); };
    m.appendChild(b);
  });
  document.body.appendChild(m);
  setTimeout(() => document.addEventListener("click", closeEdMenu, { once: true }), 0);
}
function sendToEditor(p, ed) {
  p.assignee = "Editor";
  p.eid = ed.id;
  p.eready = false;
  /* the editor continues the SAME sequence from the same stage; a bare topic
     starts at Script (wizard), finished/posted work returns to Editing for fixes */
  const stageMap = { idea: "script", publish: "editing", scheduled: "editing", posted: "editing" };
  if (stageMap[p.status]) p.status = stageMap[p.status];
  savePlans();
  rerender();
  const lbl = { script: "Script", filming: "Filming", editing: "Editing" }[p.status] || p.status;
  toast("Sent to " + ed.name + " ✂️ — in their " + lbl + " section");
}

/* ---- editor management (owner) ---- */
async function addEditor() {
  const name = (prompt("New editor's name?") || "").trim();
  if (!name) return false;
  const pass = (prompt("Set " + name + "'s access password (they log in with it on their private link):") || "").trim();
  if (!pass) { toast("Password zaroori hai — editor isi se login karega 🔑"); return false; }
  const ed = { id: "e" + Date.now(), name: name, ph: await sha256(pass) };
  editors.push(ed);
  saveEditors();
  adoptOrphans(ed.id);
  edSel = ed.id;
  edView = "work";
  switchTab("editors");
  toast(name + " added ✂️ — copy their private link from the workspace");
  return true;
}
function editorLink(ed) {
  /* the link carries id + password-hash + name + sync config: password-only gate, auto data */
  return location.origin + location.pathname + "#editor=" + ed.id + "." +
    (ed.ph || "") + ".." + encodeURIComponent(ed.name) +
    (SYNCCFG ? "&s=" + encodeURIComponent(SYNCCFG) : "");
}
function renameEditor(ed) {
  const name = (prompt("Editor's new name?", ed.name) || "").trim();
  if (!name) return;
  ed.name = name;
  saveEditors(); renderBoard();
}
function removeEditor(ed) {
  if (!confirm("Remove " + ed.name + "? Their pipeline items go back to you; open tasks are deleted (history stays in the export file).")) return;
  plans.forEach(p => { if (p.assignee === "Editor" && p.eid === ed.id) { p.assignee = "Ahmad"; } });
  etasks = etasks.filter(t => t.eid !== ed.id);
  editors = editors.filter(e => e.id !== ed.id);
  delete enotes[ed.id];
  saveEditors(); saveEnotes(); saveEtasks(); savePlans();
  if (ROLE === ed.id) { ROLE = "owner"; localStorage.setItem("role", "owner"); applyRole(true); }
  edSel = "";
  renderBoard();
  toast(ed.name + " removed");
}

/* ---- role: this device acts as owner or as one editor ---- */
async function roleSwitch(ev) {
  if (ROLE !== "owner") {                    /* leaving editor mode needs the owner code */
    if (LOCKHASH) {
      const code = prompt("Owner access code:") || "";
      if (await sha256(code) !== LOCKHASH) { toast("Wrong code ❌"); return; }
    } else if (!confirm("Return to owner mode?")) return;
    ROLE = "owner";
    localStorage.setItem("role", "owner");
    applyRole();
    toast("Owner mode 👤");
    return;
  }
  if (!editors.length) { toast("No editors yet — add one in the Editors tab"); return; }
  pickEditorMenu(ev, ed => {
    ROLE = ed.id;
    localStorage.setItem("role", ROLE);
    if (ed.ph) localStorage.setItem("edunlock", ed.ph);  /* owner device: no password prompt */
    applyRole();
    toast("Editor mode: " + ed.name + " ✂️");
  });
}
function applyRole(noNav) {
  const owner = ROLE === "owner";
  ["home", "news", "trends", "research", "plan"].forEach(n => {
    const b = document.getElementById("tabbtn-" + n);
    if (b) b.style.display = owner ? "" : "none";
  });
  const rb = document.getElementById("rolebtn");
  if (rb) {
    rb.textContent = owner ? "👤" : "✂️";
    rb.title = owner ? "Owner mode — click to act as an editor"
      : "Editor mode: " + edById(ROLE).name + " — click to return to owner mode";
  }
  if (!noNav) switchTab(owner ? "home" : "editors");
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
    '<span class="avatar ahmad" style="cursor:pointer" title="Click to send to an editor">A</span>' +
    (p.eready ? '<span class="tag" style="color:#059669;border-color:#059669">✅ ready</span>' : "") +
    '<span class="qtext">' + esc(p.title.split("\n")[0].slice(0, 80)) + "</span>" +
    '<span class="qtags">' + platTags(p) + "</span>" +
    '<button class="rowdel" style="background:none;border:1px solid var(--line);color:var(--dim);border-radius:7px;padding:3px 9px;font-size:11.5px;cursor:pointer">✕</button>';
  d.onclick = () => openComposer(p.id);
  d.querySelector(".avatar").onclick = e => {
    e.stopPropagation();
    pickEditorMenu(e, ed => sendToEditor(p, ed));
  };
  d.querySelector(".rowdel").onclick = e => {
    e.stopPropagation();
    if (confirm("Delete this item?")) {
      plans = plans.filter(x => x.id !== p.id);
      savePlans(); renderBoard(); toast("Deleted 🗑");
    }
  };
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
  const sched = plans.filter(p => p.status === "scheduled" && p.when && p.assignee !== "Editor")
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

/* ---- Assigned Tasks: what each editor is working on right now ---- */
function renderAssignedView(el) {
  const working = plans.filter(p => p.assignee === "Editor");
  const completed = plans.filter(p => p.eready && p.status === "publish");
  if (!working.length && !completed.length) {
    el.innerHTML = '<div class="empty">Nothing assigned — send any topic to an editor with the ✂️ → Editor button.</div>';
    return;
  }
  const STATUS_LBL = { script: "✍️ Script", filming: "🎥 Filming", editing: "✂️ Editing" };
  const row = (p, done) => {
    const ed = edById(p.eid);
    const d = document.createElement("div");
    d.className = "qrow";
    d.innerHTML =
      '<span class="avatar editor" title="' + esc(ed ? ed.name : "Editor") + '">' +
      esc((ed ? ed.name : "E").slice(0, 1).toUpperCase()) + "</span>" +
      '<span class="qtext">' + esc(p.title.split("\n")[0].slice(0, 70)) + "</span>" +
      '<span style="font-size:11.5px;color:var(--dim);white-space:nowrap">✂️ ' + esc(ed ? ed.name : "Editor") + "</span>" +
      (done
        ? '<span class="tag" style="color:#059669;border-color:#059669">✅ Completed</span>'
        : '<span class="tag">' + (STATUS_LBL[p.status] || p.status) + "</span>") +
      (p.revnote ? '<span class="tag" style="color:var(--red);border-color:var(--red)">🔁 revision</span>' : "") +
      '<button class="rowdel" style="background:none;border:1px solid var(--line);color:var(--dim);border-radius:7px;padding:3px 9px;font-size:11.5px;cursor:pointer">✕</button>';
    d.querySelector(".rowdel").onclick = e => {
      e.stopPropagation();
      if (confirm("Delete this assigned task? It disappears for the editor too.")) {
        plans = plans.filter(x => x.id !== p.id);
        savePlans(); renderBoard(); toast("Deleted 🗑");
      }
    };
    d.onclick = () => {
      if (done) { boardView = "ready"; renderBoard(); return; }
      if (ed) {                              /* jump into that editor's workspace at this stage */
        edSel = ed.id;
        edView = STATUS_LBL[p.status] ? p.status : "work";
        switchTab("editors");
      }
    };
    return d;
  };
  if (working.length) {
    const h = document.createElement("div");
    h.className = "qday";
    h.textContent = "In progress (" + working.length + ")";
    el.appendChild(h);
    working.forEach(p => el.appendChild(row(p, false)));
  }
  if (completed.length) {
    const h2 = document.createElement("div");
    h2.className = "qday";
    h2.textContent = "Completed — waiting for your review (" + completed.length + ")";
    el.appendChild(h2);
    completed.forEach(p => el.appendChild(row(p, true)));
  }
}

/* ---- Ready to Post: work editors sent back, waiting for the owner's review ---- */
function renderReadyView(el) {
  const items = plans.filter(p => p.eready && p.status === "publish")
    .sort((a, b) => (b.ereadyAt || "").localeCompare(a.ereadyAt || ""));
  if (!items.length) {
    el.innerHTML = '<div class="empty">Nothing waiting — when an editor presses "Send Back to Owner", it lands here.</div>';
    return;
  }
  items.forEach(p => {
    const ed = edById(p.eid);
    const d = document.createElement("div");
    d.className = "qrow";
    d.innerHTML =
      '<span class="avatar editor" title="' + esc(ed ? ed.name : "Editor") + '">' +
      esc((ed ? ed.name : "E").slice(0, 1).toUpperCase()) + "</span>" +
      '<span class="qtext">' + esc(p.title.split("\n")[0].slice(0, 70)) + "</span>" +
      '<span class="tag" style="color:#059669;border-color:#059669">✅ completed</span>' +
      '<span style="font-size:11.5px;color:var(--dim);white-space:nowrap">✂️ ' + esc(ed ? ed.name : "Editor") + "</span>" +
      (p.ereadyAt ? '<span style="font-size:11.5px;color:var(--faint);white-space:nowrap">' +
        p.ereadyAt.slice(0, 10) + " " + p.ereadyAt.slice(11, 16) + "</span>" : "") +
      '<span class="qtags">' + platTags(p) + "</span>" +
      '<button class="ok-btn" style="background:none;border:1px solid #059669;color:#059669;border-radius:7px;padding:3px 9px;font-size:11.5px;cursor:pointer;white-space:nowrap">✔ Approve → Publish</button>' +
      '<button class="re-btn" style="background:none;border:1px solid var(--red);color:var(--red);border-radius:7px;padding:3px 9px;font-size:11.5px;cursor:pointer;white-space:nowrap">✕ Reject + notes</button>';
    d.onclick = () => openComposer(p.id);
    d.querySelector(".ok-btn").onclick = e => {
      e.stopPropagation();
      p.eready = false;                        /* reviewed: schedule & post from Publish */
      delete p.revnote;
      savePlans(); renderBoard();
      toast("Approved ✔ — it's in Publish, schedule it 🗓");
    };
    d.querySelector(".re-btn").onclick = e => {
      e.stopPropagation();
      const ed = edById(p.eid);
      if (!ed) { toast("That editor no longer exists"); return; }
      const note = (prompt("What should " + ed.name + " fix?") || "").trim();
      if (!note) { toast("Rejection needs a note for the editor"); return; }
      p.revnote = note;
      p.eready = false;
      /* a post is text — it goes back to their Script wizard; a video to Editing */
      p.status = p.ctype === "post" ? "script" : "editing";
      p.assignee = "Editor";
      savePlans(); renderBoard();
      toast("Rejected — back in " + ed.name + "'s " + (p.status === "script" ? "Script" : "Editing") + " with your notes ✂️");
    };
    el.appendChild(d);
  });
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
  const ideas = plans.filter(p => p.status === "idea" && p.assignee !== "Editor");
  if (!ideas.length) grid.innerHTML =
    '<div class="empty">No ideas yet — the 🎬 plan button on any news story drops it here.</div>';
  ideas.forEach(p => {
    const c = document.createElement("div");
    c.className = "ideacard";
    c.innerHTML = '<div class="t">' + esc(p.title.split("\n")[0]) + "</div>" +
      (p.url ? '<a href="' + esc(p.url) + '" target="_blank">source</a>' : "") +
      '<div style="margin-top:10px;display:flex;gap:6px">' +
      '<button class="ghost" style="padding:5px 12px;font-size:12px">✍️ → Script</button>' +
      '<button class="ghost" style="padding:5px 10px;font-size:12px">✂️ → Editor</button>' +
      '<button class="danger" style="padding:5px 10px;font-size:12px;margin-left:auto">✕</button></div>';
    const btns = c.querySelectorAll("button");
    btns[0].onclick = () => {
      p.status = "script"; savePlans();
      openCreate(p.title.split("\n")[0], p.url || "", p.ctype ? { type: p.ctype } : null, p.id);
    };
    btns[1].onclick = ev => pickEditorMenu(ev, ed => sendToEditor(p, ed));
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

/* ---- per-editor workspace: notes, tasks, pipeline items, performance ---- */
function planKind(p) { return p.ctype === "post" ? "post" : "video"; }

function sendToOwner(p, ed) {
  const now = new Date();
  const today = now.toISOString().slice(0, 10);
  p.eready = true;
  p.ereadyAt = now.toISOString();
  p.assignee = "Ahmad";
  p.status = "publish";                      /* lands in the owner's Ready to Post tab */
  delete p.revnote;                          /* revision handled */
  if (!ehist.some(h => h.ref === p.id)) {
    ehist.unshift({ eid: ed.id, ref: p.id, title: p.title.split("\n")[0].slice(0, 60),
      kind: planKind(p), due: p.when ? p.when.slice(0, 10) : "", doneAt: today,
      late: !!(p.when && today > p.when.slice(0, 10)) });
    saveEhist();
  }
  savePlans();
  rerender();
  toast("Sent back to owner ✅ — it's in their Ready to Post list");
}

/* ---- Editors tab: every editor's workspace lives here, away from Buffer ---- */
function renderEditorsTab() {
  const nav = document.getElementById("ednav");
  const out = document.getElementById("edwork");
  nav.innerHTML = "";
  out.innerHTML = "";
  if (ROLE !== "owner") {                    /* an editor sees only their own workspace */
    const ed = edById(ROLE);
    if (!ed) {
      out.innerHTML = '<div class="empty">No workspace on this device — ask the owner for your link.</div>';
      return;
    }
    const b = document.createElement("button");
    b.innerHTML = "✂️ " + esc(ed.name) + "&rsquo;s workspace";
    b.className = "active";
    nav.appendChild(b);
    renderEditorView(out, ed);
    return;
  }
  editors.forEach(ed => {
    const open = edOpenCount(ed);
    const b = document.createElement("button");
    b.innerHTML = "✂️ " + esc(ed.name) + (open ? " · " + open : "");
    b.className = edSel === ed.id ? "active" : "";
    b.onclick = () => {
      if (edSel !== ed.id) edView = "work";
      edSel = ed.id;
      renderEditorsTab();
    };
    nav.appendChild(b);
  });
  const plus = document.createElement("button");
  plus.textContent = editors.length ? "+ Add editor" : "+ Add your first editor";
  plus.onclick = () => addEditor();
  nav.appendChild(plus);
  if (!editors.length) {
    out.innerHTML = '<div class="empty">No editors yet — add one, set their password, and share their private link with them.</div>';
    return;
  }
  if (!edById(edSel)) edSel = editors[0].id;
  renderEditorView(out, edById(edSel));
}

/* stage cards inside an editor's workspace — like the owner's board, but
   the path ends at "Send to Owner" instead of Publish */
function renderEdStage(el, ed, stage, nextStage, nextLabel) {
  const isOwner = ROLE === "owner";
  const items = plans.filter(p => p.assignee === "Editor" && p.eid === ed.id && p.status === stage);
  if (!items.length) {
    const e2 = document.createElement("div");
    e2.className = "empty";
    e2.textContent = "Nothing in " + stage + (isOwner ? " for " + ed.name : "") + " right now.";
    el.appendChild(e2);
    return;
  }
  items.forEach(p => {
    p.chk = p.chk || {};
    const c = document.createElement("div");
    c.className = "panel";
    let inner = '<h3 style="color:var(--text)">' + esc(p.title.split("\n")[0]) +
      (p.ctype ? ' <span class="tag">' + p.ctype + "</span>" : "") + "</h3>";
    if (p.revnote) inner += '<div style="margin:8px 0;padding:10px 14px;border:1px solid var(--red);border-radius:10px;color:var(--red);font-size:13px"><b>🔁 Owner wants fixes:</b> ' + esc(p.revnote) + "</div>";
    inner += '<div class="chkrow">' + (STAGE_CHK[stage] || []).map(([k, lab]) =>
      '<label class="chk"><input type="checkbox" data-k="' + k + '"' +
      (p.chk[k] ? " checked" : "") + "> " + lab + "</label>").join("") + "</div>";
    if (p.notes) inner += '<details class="scriptbox"><summary>📜 Script / instructions</summary><pre>' + esc(p.notes) + "</pre></details>";
    inner += '<div class="mfoot"><button class="btn next-btn">' + nextLabel + "</button>" +
      (stage !== "editing" ? '<button class="ghost send-btn">📤 Send Back to Owner</button>' : "") +
      (isOwner ? '<button class="ghost edit-btn">✎ Edit details</button>' +
        '<button class="ghost hand-btn" style="margin-left:auto">👤 → Owner</button>' : "") +
      "</div>";
    c.innerHTML = inner;
    c.querySelectorAll(".chk input").forEach(cb => {
      cb.onchange = () => { p.chk[cb.dataset.k] = cb.checked; savePlans(); };
    });
    c.querySelector(".next-btn").onclick = () => {
      if (!nextStage) { sendToOwner(p, ed); return; }
      p.status = nextStage;
      savePlans();
      edView = nextStage;
      renderBoard();
      toast("Moved ✓");
    };
    const sb = c.querySelector(".send-btn");
    if (sb) sb.onclick = () => sendToOwner(p, ed);
    if (isOwner) {
      c.querySelector(".edit-btn").onclick = () => openComposer(p.id);
      c.querySelector(".hand-btn").onclick = () => {
        p.assignee = "Ahmad";
        savePlans(); renderBoard(); toast("Back with you 👤");
      };
    }
    el.appendChild(c);
  });
}

function renderEditorView(el, ed) {
  const isOwner = ROLE === "owner";
  const today = new Date().toISOString().slice(0, 10);
  const myTasks = etasks.filter(t => t.eid === ed.id);
  const myPlans = plans.filter(p => p.assignee === "Editor" && p.eid === ed.id && p.status !== "posted");
  const hist = ehist.filter(h => h.eid === ed.id);

  /* header: who this workspace belongs to + owner controls */
  const head = document.createElement("div");
  head.className = "addrow";
  head.style.alignItems = "center";
  head.innerHTML = '<b style="font-size:16px">✂️ ' + esc(ed.name) + "&rsquo;s workspace</b>" +
    (isOwner
      ? '<button class="ghost" id="ed-link" style="padding:5px 12px;font-size:12px">🔗 Copy their link</button>' +
        '<button class="ghost" id="ed-pass" style="padding:5px 12px;font-size:12px">🔑 Password</button>' +
        '<button class="ghost" id="ed-ren" style="padding:5px 12px;font-size:12px">✎ Rename</button>' +
        '<button class="danger" id="ed-del" style="padding:5px 12px;font-size:12px;margin-left:auto">🗑 Remove editor</button>'
      : '<span class="tag" style="margin-left:auto">you are signed in as the editor</span>');
  el.appendChild(head);
  if (isOwner) {
    head.querySelector("#ed-link").onclick = () => {
      navigator.clipboard.writeText(editorLink(ed)).then(() =>
        toast("Private link copied — send it to " + ed.name + " 🔗"));
    };
    head.querySelector("#ed-pass").onclick = async () => {
      const pass = (prompt("New password for " + ed.name + ":") || "").trim();
      if (!pass) return;
      ed.ph = await sha256(pass);
      saveEditors();
      toast("Password updated 🔑 — send " + ed.name + " their NEW link (the old one stopped working)");
    };
    head.querySelector("#ed-ren").onclick = () => renameEditor(ed);
    head.querySelector("#ed-del").onclick = () => removeEditor(ed);
  }

  /* the editor's own staged board: Script -> Filming -> Editing -> Send to Owner */
  const nav = document.createElement("div");
  nav.className = "bar";
  nav.style.marginTop = "12px";
  const stCnt = s => plans.filter(p => p.assignee === "Editor" && p.eid === ed.id && p.status === s).length;
  [["work", "📋 Board"], ["script", "✍️ Script"], ["filming", "🎥 Filming"], ["editing", "✂️ Editing"]].forEach(([k, lab], i) => {
    const b = document.createElement("button");
    const n = k === "work" ? 0 : stCnt(k);
    b.innerHTML = lab + (n ? " · " + n : "");
    b.className = edView === k ? "active" : "";
    b.onclick = () => { edView = k; renderBoard(); };
    nav.appendChild(b);
    if (i > 0 && i < 3) {
      const a = document.createElement("span");
      a.textContent = "→";
      a.style.cssText = "color:var(--faint);font-size:12px";
      nav.appendChild(a);
    }
  });
  const sendChip = document.createElement("span");
  sendChip.innerHTML = "→ 📤 Send Back to Owner";
  sendChip.style.cssText = "color:var(--faint);font-size:12px";
  nav.appendChild(sendChip);
  el.appendChild(nav);
  if (edView === "script") { renderScriptView(el, ed); return; }   /* same wizard as the owner */
  if (edView === "filming") { renderEdStage(el, ed, "filming", "editing", "Done → Editing"); return; }
  if (edView === "editing") { renderEdStage(el, ed, "editing", "", "📤 Send Back to Owner"); return; }

  /* performance checklist */
  const done = hist.length;
  const stats = document.createElement("div");
  stats.className = "statgrid";
  stats.style.marginTop = "14px";
  stats.innerHTML =
    '<div class="scard click" data-go="ed-hist-h"><div class="l">Posts completed</div><div class="n">' + hist.filter(h => h.kind === "post").length + "</div></div>" +
    '<div class="scard click" data-go="ed-hist-h"><div class="l">Videos completed</div><div class="n indigo">' + hist.filter(h => h.kind === "video").length + "</div></div>" +
    '<div class="scard click" data-go="ed-hist-h"><div class="l">On time</div><div class="n green">' + hist.filter(h => !h.late).length + "</div></div>" +
    '<div class="scard click" data-go="ed-hist-h"><div class="l">Late</div><div class="n orange">' + hist.filter(h => h.late).length + "</div></div>" +
    '<div class="scard click" data-go="ed-tasks-h"><div class="l">Pending</div><div class="n">' + (myTasks.filter(t => !t.done).length + myPlans.length) + "</div></div>";
  stats.querySelectorAll(".scard").forEach(card => {
    card.onclick = () => {
      const t = document.getElementById(card.dataset.go);
      if (t) t.scrollIntoView({ behavior: "smooth", block: "start" });
    };
  });
  el.appendChild(stats);

  /* notes / instructions from the owner */
  const nh = document.createElement("div");
  nh.className = "qday";
  nh.textContent = "📝 Notes from the owner";
  el.appendChild(nh);
  const notes = enotes[ed.id] || [];
  if (!notes.length) {
    const ne = document.createElement("div");
    ne.className = "empty";
    ne.textContent = isOwner ? "No notes yet — leave instructions below." : "No notes from the owner yet.";
    el.appendChild(ne);
  }
  notes.forEach(n => {
    const d = document.createElement("div");
    d.className = "qrow";
    d.style.cursor = "default";
    d.innerHTML = '<span class="qtext" style="cursor:default;white-space:pre-wrap">' + esc(n.text) + "</span>" +
      '<span style="font-size:11px;color:var(--faint);white-space:nowrap">' + n.at + "</span>" +
      (isOwner ? '<button class="rowdel" style="background:none;border:1px solid var(--line);color:var(--dim);border-radius:7px;padding:3px 9px;font-size:11.5px;cursor:pointer">✕</button>' : "");
    if (isOwner) d.querySelector(".rowdel").onclick = () => {
      enotes[ed.id] = (enotes[ed.id] || []).filter(x => x.id !== n.id);
      saveEnotes(); renderBoard();
    };
    el.appendChild(d);
  });
  if (isOwner) {
    const nf = document.createElement("div");
    nf.className = "addrow";
    nf.innerHTML = '<input id="en-text" style="flex:1;min-width:200px" placeholder="Instruction for ' + esc(ed.name) + '… e.g. Use the new intro, captions in Urdu">' +
      '<button class="btn" id="en-add">+ Note</button>';
    el.appendChild(nf);
    const addNote = () => {
      const txt = nf.querySelector("#en-text").value.trim();
      if (!txt) { toast("Note likho pehle"); return; }
      if (!enotes[ed.id]) enotes[ed.id] = [];
      enotes[ed.id].unshift({ id: Date.now(), text: txt, at: today });
      saveEnotes(); renderBoard(); toast("Note left for " + ed.name + " 📝");
    };
    nf.querySelector("#en-add").onclick = addNote;
    nf.querySelector("#en-text").addEventListener("keydown", e => { if (e.key === "Enter") addNote(); });
  }

  /* tasks with due dates (owner assigns, editor ticks done) */
  const th = document.createElement("div");
  th.className = "qday";
  th.id = "ed-tasks-h";
  th.textContent = "✅ Tasks (" + myTasks.filter(t => !t.done).length + " open)";
  el.appendChild(th);
  if (isOwner) {
    const form = document.createElement("div");
    form.className = "addrow";
    form.innerHTML =
      '<input id="et-title" style="flex:1;min-width:200px" placeholder="Task for ' + esc(ed.name) + '… e.g. Edit Gemini video, make 3 banners">' +
      '<input id="et-due" type="date">' +
      '<button class="btn" id="et-add">+ Assign</button>';
    el.appendChild(form);
    form.querySelector("#et-add").onclick = () => {
      const t = form.querySelector("#et-title").value.trim();
      if (!t) { toast("Task likho pehle"); return; }
      etasks.unshift({ id: Date.now(), title: t, eid: ed.id,
        due: form.querySelector("#et-due").value || "", done: false });
      saveEtasks();
      renderBoard();
      toast("Assigned to " + ed.name + " ✂️");
    };
    form.querySelector("#et-title").addEventListener("keydown", e => {
      if (e.key === "Enter") form.querySelector("#et-add").click();
    });
  }
  const pending = myTasks.filter(t => !t.done)
    .sort((a, b) => (a.due || "9999").localeCompare(b.due || "9999"));
  const doneTasks = myTasks.filter(t => t.done);
  if (!myTasks.length) {
    const e2 = document.createElement("div");
    e2.className = "empty";
    e2.textContent = isOwner ? "No tasks for " + ed.name + " — assign one above." : "No tasks assigned to you yet.";
    el.appendChild(e2);
  }
  pending.concat(doneTasks).forEach(t => {
    const late = t.due && t.due < today && !t.done;
    const d = document.createElement("div");
    d.className = "qrow";
    if (t.done) d.style.opacity = ".45";
    d.innerHTML =
      '<input type="checkbox" class="et-chk" style="width:18px;height:18px;accent-color:#65a30d"' + (t.done ? " checked" : "") + ">" +
      '<span class="qtext" style="cursor:default">' + (t.done ? "<s>" + esc(t.title) + "</s>" : esc(t.title)) + "</span>" +
      (t.due ? '<span class="duetag' + (late ? " late" : "") + '" style="font-size:11.5px;font-weight:600;color:' +
        (late ? "var(--red)" : "var(--dim)") + '">📅 ' + t.due.slice(5) + (late ? " LATE" : "") + "</span>" : "") +
      (isOwner ? '<button class="rowdel" style="background:none;border:1px solid var(--line);color:var(--dim);border-radius:7px;padding:3px 9px;font-size:11.5px;cursor:pointer">✕</button>' : "");
    d.querySelector(".et-chk").onchange = e => {
      t.done = e.target.checked;
      if (t.done) {
        t.doneAt = today;
        ehist.unshift({ eid: ed.id, ref: t.id, title: t.title, kind: "task",
          due: t.due || "", doneAt: today, late: !!(t.due && today > t.due) });
      } else {
        delete t.doneAt;
        ehist = ehist.filter(h => h.ref !== t.id);
      }
      saveEhist();
      saveEtasks();
      renderBoard();
      if (t.done) toast("Task done ✓");
    };
    if (isOwner) d.querySelector(".rowdel").onclick = () => {
      if (confirm("Delete this task?")) {
        etasks = etasks.filter(x => x.id !== t.id);
        ehist = ehist.filter(h => h.ref !== t.id);
        saveEhist(); saveEtasks();
        renderBoard();
      }
    };
    el.appendChild(d);
  });

  /* pipeline items handed to this editor */
  if (myPlans.length) {
    const h2 = document.createElement("div");
    h2.className = "qday";
    h2.textContent = "🎬 Pipeline items (" + myPlans.length + ")";
    el.appendChild(h2);
    myPlans.forEach(p => {
      const d = document.createElement("div");
      d.className = "qrow";
      d.innerHTML = '<span class="tag">' + p.status + "</span>" +
        (p.eready ? '<span class="tag" style="color:#059669;border-color:#059669">✅ ready</span>' : "") +
        (p.revnote ? '<span class="tag" style="color:var(--red);border-color:var(--red)">🔁 fixes</span>' : "") +
        '<span class="qtext">' + esc(p.title.split("\n")[0].slice(0, 60)) + "</span>" +
        '<span class="qtags">' + platTags(p) + "</span>" +
        (isOwner
          ? '<button class="back-btn" style="background:none;border:1px solid #d97706;color:#d97706;border-radius:7px;padding:3px 9px;font-size:11.5px;cursor:pointer;white-space:nowrap">👤 → Owner</button>'
          : '<button class="ready-btn" style="background:none;border:1px solid ' + (p.eready ? "#059669;color:#059669" : "var(--line);color:var(--dim)") + ';border-radius:7px;padding:3px 9px;font-size:11.5px;cursor:pointer;white-space:nowrap">' + (p.eready ? "✅ Ready" : "Ready to Post?") + "</button>" +
            '<button class="send-btn" style="background:none;border:1px solid #059669;color:#059669;border-radius:7px;padding:3px 9px;font-size:11.5px;cursor:pointer;white-space:nowrap">📤 Send Back to Owner</button>');
      if (isOwner) {
        d.onclick = () => openComposer(p.id);
        d.querySelector(".back-btn").onclick = e => {
          e.stopPropagation();
          p.assignee = "Ahmad";
          savePlans(); renderBoard(); toast("Back with you 👤");
        };
      } else {
        if (["script", "filming", "editing"].indexOf(p.status) >= 0) {
          d.onclick = () => { edView = p.status; renderBoard(); };
        }
        d.querySelector(".ready-btn").onclick = e => {
          e.stopPropagation();
          p.eready = !p.eready;
          savePlans(); renderBoard();
          toast(p.eready ? "Marked ready to post ✅" : "Ready mark removed");
        };
        d.querySelector(".send-btn").onclick = e => {
          e.stopPropagation();
          sendToOwner(p, ed);
        };
      }
      el.appendChild(d);
      if (!isOwner && p.notes) {                      /* editor reads the brief, no composer access */
        const det = document.createElement("details");
        det.className = "scriptbox";
        det.innerHTML = "<summary>📜 Script / instructions</summary><pre>" + esc(p.notes) + "</pre>";
        el.appendChild(det);
      }
    });
  }

  /* completion history */
  const hh = document.createElement("div");
  hh.className = "qday";
  hh.id = "ed-hist-h";
  hh.textContent = "📜 Completion history (" + done + ")";
  el.appendChild(hh);
  if (!done) {
    const he = document.createElement("div");
    he.className = "empty";
    he.textContent = "Nothing completed yet.";
    el.appendChild(he);
  }
  hist.slice(0, 20).forEach(h => {
    const icon = h.kind === "post" ? "💬" : h.kind === "video" ? "🎬" : "✅";
    const d = document.createElement("div");
    d.className = "qrow";
    d.style.cursor = "default";
    d.innerHTML = '<span style="font-size:14px">' + icon + "</span>" +
      '<span class="qtext" style="cursor:default">' + esc(h.title) + "</span>" +
      '<span style="font-size:11.5px;color:var(--faint);white-space:nowrap">' + h.doneAt + "</span>" +
      '<span style="font-size:11px;font-weight:700;white-space:nowrap;color:' +
      (h.late ? "var(--red)" : "#059669") + '">' + (h.late ? "LATE" : "ON TIME") + "</span>";
    el.appendChild(d);
  });
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
  const assSel = document.getElementById("m-ass");
  assSel.innerHTML = '<option value="Ahmad">👤 Ahmad (owner)</option>' +
    editors.map(e2 => '<option value="' + e2.id + '">✂️ ' + esc(e2.name) + "</option>").join("");
  assSel.value = (p.assignee === "Editor" && edById(p.eid)) ? p.eid : "Ahmad";
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
  const av = document.getElementById("m-ass").value;
  if (av === "Ahmad") { p.assignee = "Ahmad"; }
  else { p.assignee = "Editor"; p.eid = av; }
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
  editingId = null;
  if (p) openCreate(p.title.split("\n")[0].slice(0, 120), p.url || "");
}
function composerToWizard() { modalPrep(); }
document.getElementById("modal").addEventListener("click", e => {
  if (e.target.id === "modal") closeModal();
});

function exportPlans() {
  const blob = new Blob([JSON.stringify({ plans: plans, etasks: etasks,
    editors: editors, enotes: enotes, ehist: ehist }, null, 2)],
    { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "aixahmad-board.json";
  a.click();
  toast(ROLE === "owner" ? "Board file downloaded — send it to your editors"
    : "Board file downloaded — send it back to Ahmad");
}
document.getElementById("importfile").addEventListener("change", e => {
  const f = e.target.files[0];
  if (!f) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const data = JSON.parse(reader.result);
      if (Array.isArray(data)) {            // old format: plans only
        plans = data;
      } else if (data && Array.isArray(data.plans)) {  // new format
        plans = data.plans;
        if (Array.isArray(data.etasks)) { etasks = data.etasks; saveEtasks(); }
        if (Array.isArray(data.editors)) { editors = data.editors; saveEditors(); }
        if (data.enotes && typeof data.enotes === "object") { enotes = data.enotes; saveEnotes(); }
        if (Array.isArray(data.ehist)) { ehist = data.ehist; saveEhist(); }
      } else { throw new Error("bad"); }
      savePlans();
      if (ROLE !== "owner" && !edById(ROLE)) { ROLE = "owner"; localStorage.setItem("role", "owner"); applyRole(true); }
      if (EDLINK && !document.getElementById("lock").hidden) edGateShow();  /* gate now knows the editor */
      renderBoard();
      toast("Board imported ✓");
    } catch (err) { alert("That file is not a valid board export."); }
  };
  reader.readAsText(f);
});


/* ------------- related-coverage helper (used by the Create wizard) ------------- */
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
    rel.slice(0, 4).map(r => "- " + r[1].t + " \u2014 " + r[1].u).join("\n");
}

/* ---------------- Home dashboard ---------------- */
const UPDATED = "__UPDATED__";
function renderHome() {
  document.getElementById("homedatetxt").textContent =
    new Date().toLocaleDateString("en-GB",
      { weekday: "long", day: "numeric", month: "long" }) +
    " · radar updated " + UPDATED;

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

  const day = Date.now() - 86400000;
  const today = ITEMS.filter(it => it.p !== 9 && new Date(it.d).getTime() > day);
  const hot = today.filter(it => it.l && it.l.length).length;
  const local = today.filter(it => it.lo).length;
  const open = plans.filter(x => x.status !== "posted").length;
  const sg = document.getElementById("statgrid");
  sg.innerHTML =
    '<div class="scard click" data-act="today"><div class="l">Stories today</div><div class="n">' + today.length + "</div></div>" +
    '<div class="scard click" data-act="hot"><div class="l">Hot</div><div class="n orange">' + hot + "</div></div>" +
    '<div class="scard click" data-act="local"><div class="l">Local angle</div><div class="n green">' + local + "</div></div>" +
    '<div class="scard click" data-act="tickets"><div class="l">Tickets open</div><div class="n indigo">' + open + "</div></div>";
  sg.querySelectorAll(".scard").forEach(card => {
    card.onclick = () => {
      const act = card.dataset.act;
      if (act === "tickets") { boardView = "ideas"; switchTab("plan"); return; }
      hotOnly = act === "hot";
      localOnly = act === "local";
      if (act === "today") mode = "latest";
      shown = PAGE;
      switchTab("news");
      bar(); render();
    };
  });

  const pl = document.getElementById("pipeline");
  const openPlans = plans.filter(x => x.status !== "posted").slice(0, 6);
  pl.innerHTML = openPlans.length ? "" :
    '<p style="color:var(--faint);font-size:13px">No open tickets — plan a video from News.</p>';
  openPlans.forEach(p => {
    const d = document.createElement("div");
    d.className = "pipe";
    d.innerHTML = '<span class="st">' + p.status + "</span>" +
      "<span>" + esc(p.title.split("\n")[0].slice(0, 48)) + "</span>" +
      '<span class="who ' + (p.assignee === "Editor" ? "editor" : "ahmad") + '">' +
      esc(holderName(p)) + "</span>";
    d.onclick = () => switchTab("plan");
    pl.appendChild(d);
  });
}
function qaShort() {
  openCreate("", "", { type: "short" });
}
function qaX() {
  openCreate("", "", { type: "post", plats: ["x"] });
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
if (EDLINK) {                       /* arrived via an editor's private link */
  let _ed = edById(EDLINK);
  const _key = (_ed && _ed.ph) || EDKEY;
  if (_key && localStorage.getItem("edunlock") === _key) {
    if (!_ed) {                     /* fresh device, already unlocked before */
      _ed = { id: EDLINK, name: EDNAME || "Editor", ph: EDKEY };
      editors.push(_ed);
      saveEditors();
    }
    ROLE = _ed.id;
    localStorage.setItem("role", ROLE);
    applyRole();                    /* already logged in on this device */
  } else {
    edGateShow();                   /* just the password box — nothing else */
  }
} else {
  applyRole(ROLE === "owner");      /* editor-mode devices jump straight to their workspace */
}
setCloudIcon(true);
if (SYNCCFG) {
  pollBoard().then(() => { syncReady = true; });   /* pull latest before pushing */
  startStream();
}
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
