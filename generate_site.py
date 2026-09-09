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
<meta name="theme-color" content="#f6f4ee">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<meta name="robots" content="noindex, nofollow">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>AI x Ahmad — Radar Studio</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Newsreader:opsz,wght@6..72,500;6..72,600;6..72,700&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    /* warm "Claude" light palette: ivory paper, clay accent, serif headings */
    --bg:#f6f4ee; --surface:#ffffff; --surface2:#efece3; --surface3:#e7e2d6;
    --text:#28261f; --dim:#6b6660; --faint:#9b958a;
    --line:#e6e1d4; --line2:#d8d1c2;
    --side-bg:#f0ece2; --topbar-bg:rgba(246,244,238,.82);
    --indigo:#c4633f; --indigo-soft:#f4e7df; --cyan:#1a97ab;
    --cta:#c4633f; --cta-dark:#ffffff; --cta-hover:#af522f;
    --gold:#946400; --gold-soft:#f5ecd1;
    --green:#3d7a39; --green-soft:#e8f0e3;
    --red:#bf3d2c; --red-soft:#f6e2de;
    --orange:#bd5526; --orange-soft:#f6e5d9;
    --purple:#7a59c9; --purple-soft:#ece3f6;
    --blue:#3a6ea5; --blue-soft:#e2ebf3;
    --shadow-sm:0 1px 2px rgba(45,33,16,.05);
    --shadow:0 6px 20px -8px rgba(45,33,16,.16);
    --shadow-lg:0 24px 50px -16px rgba(45,33,16,.22);
    --r:12px;
    --display:"Newsreader", Georgia, serif;
    --mono:"JetBrains Mono", ui-monospace, monospace;
  }
  * { box-sizing:border-box; }
  [hidden] { display:none !important; }
  body { margin:0; background:var(--bg); color:var(--text);
         font:14px/1.55 "Space Grotesk", Inter, system-ui, "Segoe UI", sans-serif;
         -webkit-font-smoothing:antialiased; }
  a { color:var(--indigo); }
  .wrap { max-width:1080px; margin:0 auto; padding:0 20px 80px; }

  /* ---------- header ---------- */
  header { position:sticky; top:0; z-index:50; background:rgba(255,255,255,.85);
           backdrop-filter:blur(12px); border-bottom:1px solid var(--line); }
  .logo .orb { width:28px; height:28px; border-radius:9px;
          background:linear-gradient(135deg,#6366f1,#06b6d4);
          display:flex; align-items:center; justify-content:center;
          color:#fff; font-size:14px; font-weight:800; }
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
  .pipe .st { font-size:10.5px; font-weight:600; color:var(--dim);
          background:var(--surface2); border:1px solid var(--line);
          border-radius:5px; padding:1.5px 7px; flex-shrink:0; }
  .pipe .who { margin-left:auto; font-weight:600; font-size:12px; flex-shrink:0; }
  .pipe .who.ahmad { color:var(--indigo); } .pipe .who.editor { color:#d97706; }
  .qa { display:block; width:100%; text-align:left; background:var(--surface);
          border:1px solid var(--line); color:var(--text); border-radius:10px;
          padding:13px 16px; font:500 13.5px Inter; cursor:pointer;
          margin-bottom:10px; transition:.15s; }
  .qa:hover { border-color:var(--cta); background:#f7efe9; }
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
  .cp { display:inline-flex; align-items:center; gap:5px; background:none; border:1px solid var(--line);
          color:var(--text); border-radius:8px; padding:7px 12px; font:600 12px Inter; cursor:pointer; text-decoration:none; }
  .cp:hover { border-color:var(--indigo); color:var(--indigo); background:var(--indigo-soft); }
  .cp.posted { border-color:var(--cta); color:var(--cta); }
  .cp.done { border-color:var(--cta); color:var(--cta); opacity:.75; }
  .xrpost { font-size:14.5px; line-height:1.5; white-space:pre-wrap; background:var(--surface2);
          border:1px solid var(--line); border-radius:10px; padding:11px 13px; margin:8px 0; }
  .xrpaste { margin-top:8px; }
  .xrpaste textarea { width:100%; min-height:90px; border:1px solid var(--line2); border-radius:9px;
          padding:10px; font:12.5px ui-monospace, monospace; resize:vertical; }
  .xreps { display:flex; flex-direction:column; gap:9px; margin-top:8px; }
  .xrep { border:1px solid var(--line); border-radius:11px; padding:11px 13px; background:var(--surface); }
  .xrep.sel { border-color:var(--cta); box-shadow:0 0 0 2px #f0ddd0; }
  .xrep.rec { border-color:var(--indigo); box-shadow:0 0 0 2px #f4e7df; }
  .xranalysis { font-size:13px; line-height:1.5; background:var(--indigo-soft); border:1px solid var(--line);
          border-radius:10px; padding:10px 13px; margin:8px 0; }
  .xrrec { margin-top:5px; }
  .xrbadge { background:var(--indigo); color:#fff; border-radius:999px; padding:1px 8px; font:700 10px Inter; }
  .xrtag { background:var(--surface3); border:1px solid var(--line); border-radius:999px; padding:1px 8px; font:700 10px var(--mono); color:var(--dim); }
  .xreason { font-size:11.5px; color:var(--dim); font-style:italic; margin-top:5px; }
  .rpimg { display:block; margin:8px 0; }
  .rpimg img { max-width:280px; max-height:200px; border-radius:10px; border:1px solid var(--line); object-fit:cover; }
  .rppanel { margin:8px 0; padding:10px; border:1px solid var(--line); border-radius:10px; background:var(--surface2); }
  .rphead { width:100%; box-sizing:border-box; resize:vertical; font:inherit; padding:8px 10px;
            border:1px solid var(--line); border-radius:8px; background:var(--surface); color:var(--ink); }
  .rpcanvas { max-width:240px; height:auto; border-radius:10px; border:1px solid var(--line); margin-top:8px; }
  .xmchips { display:flex; flex-wrap:wrap; gap:6px; margin:6px 0 10px; }
  .xmsub { font:700 11px var(--mono); color:var(--dim); letter-spacing:.04em; text-transform:uppercase; margin-top:4px; }
  .xbadges { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:8px; }
  .xpill { font:700 11px var(--mono); color:var(--dim); background:var(--surface3); border:1px solid var(--line); border-radius:999px; padding:2px 9px; }
  .xpill.r-low { color:#1a7f37; } .xpill.r-med { color:#b8860b; } .xpill.r-high { color:#bf3d2c; border-color:#e7b6ad; }
  .xsugg ul { margin:6px 0 0; padding-left:18px; } .xsugg li { margin:3px 0; font-size:13px; }
  .pastebox { margin:8px 0 12px; padding:10px; border:1px dashed var(--line); border-radius:10px; background:var(--surface2); }
  .pastebox .rphead { margin-bottom:6px; }
  .xmig { margin-bottom:10px; }
  .xmidea { display:block; width:100%; text-align:left; margin:4px 0; padding:7px 10px; font:inherit; font-size:12.5px;
            color:var(--ink); background:var(--surface); border:1px solid var(--line); border-radius:8px; cursor:pointer; }
  .xmidea:hover { border-color:var(--cta); background:var(--surface2); }
  .xrscore.over { color:#bf3d2c; font-weight:800; }
  .xrall { margin-top:6px; }
  .xgrid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px; margin-top:14px; }
  .xprow { display:flex; align-items:center; gap:9px; padding:7px 0; border-top:1px solid var(--line); }
  .xprow:first-of-type { border-top:none; }
  .xpk { flex:1; min-width:0; font-size:13px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .xrn { font:11px var(--mono); color:var(--faint); flex:none; }
  .xptop .xrtext { font-size:13.5px; }
  .xpmetrics { display:flex; flex-wrap:wrap; gap:8px 12px; align-items:flex-end; margin-top:10px;
          padding-top:10px; border-top:1px solid var(--line); }
  .xpf { display:flex; flex-direction:column; font:600 10.5px Inter; color:var(--dim); gap:3px; }
  .xpf input.xpi { width:74px; border:1px solid var(--line2); border-radius:7px; padding:6px 8px; font:13px Inter; }
  .xpchk { flex-direction:row; align-items:center; gap:6px; font-size:12px; color:var(--text); }
  .xpnotes { flex:1; min-width:160px; }
  .xpnotes input.xpi { width:100%; }
  .xrstyle { font:700 11.5px Inter; color:var(--dim); letter-spacing:.02em; }
  .xrscore { color:var(--gold); }
  .xrtext { font-size:14px; line-height:1.5; margin:6px 0 9px; white-space:pre-wrap; }
  .xractions { display:flex; gap:6px; }
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

  .avatar.editor { background:#f59e0b; }
  .tag { font-size:10px; font-weight:600; color:var(--dim); background:var(--surface2);
          border:1px solid var(--line); border-radius:5px; padding:1.5px 6px; }
  .qrow { display:flex; align-items:center; gap:10px; background:var(--surface);
          border:1px solid var(--line); border-radius:12px; padding:13px 16px;
          margin-bottom:8px; cursor:pointer; transition:.15s; box-shadow:var(--shadow-sm); }
  .qrow:hover { box-shadow:var(--shadow); border-color:var(--line2); }
  .qtext { font-weight:500; font-size:13.5px; flex:1; min-width:0; overflow:hidden;
          text-overflow:ellipsis; white-space:nowrap; }
  .ideacard .t { font-weight:600; font-size:13px; line-height:1.4; margin-bottom:6px; }
  .calhead .ghost { padding:6px 13px; }
  @media (max-width:860px) { .calgrid { grid-template-columns:repeat(2, 1fr); } }
  .calcell.today { border-color:var(--cta); box-shadow:0 0 0 2px #f0ddd0; }
  .calcell.today .cd { color:var(--green); }
  .calpost.draft { background:var(--gold-soft); color:var(--gold); }
  .calpost.posted { background:var(--green-soft); color:var(--green); }
  .tplcard .te { font-size:26px; }
  .tplcard.on { border-color:var(--cta); box-shadow:0 0 0 2px #f0ddd0; }
  .typecard.on { border-color:var(--cta); box-shadow:0 0 0 2px #f0ddd0; }
  .typecard .te { font-size:26px; }
  .chk { font-size:13px; color:var(--dim); display:flex; align-items:center; gap:7px;
          cursor:pointer; }
  .chk input { width:16px; height:16px; accent-color:#65a30d; }
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
  .mrow .lbl { width:84px; color:var(--faint); font-size:12px; font-weight:600;
          flex-shrink:0; }
  .mplats label.on { color:#fff; background:var(--indigo); border-color:var(--indigo); }
  .mfoot { display:flex; gap:8px; margin-top:18px; }

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
  /* ---------- responsive: phone-first fixes ---------- */
  html, body { max-width:100%; overflow-x:hidden; }
  @media (max-width:768px) {
    .wrap { padding:0 12px 70px; }
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
    .typecard .te { font-size:22px; }
    .tplcard .te { font-size:20px; }
    .panel { padding:16px 14px; }
    .genrow input, .genrow select { flex:1 1 100%; width:100%; }
    .genrow .bar { width:100%; }
    .homecols { grid-template-columns:1fr; }
    .pickrow .btn { margin-left:0; width:100%; }
    .statgrid { grid-template-columns:1fr 1fr; gap:9px; }
    .scard { padding:13px 14px; }
    .scard .n { font-size:21px; }
    .toppick h2 { font-size:17px; }
    .chk { min-height:30px; }
    .qa { min-height:48px; }
  }
  @media (max-width:400px) {
    .statgrid { grid-template-columns:1fr 1fr; }
  }

  /* ---------- RadarStudio shell (sidebar + topbar) ---------- */
  @keyframes radarPulse { 0%{transform:scale(.6);opacity:.8} 100%{transform:scale(2.2);opacity:0} }
  .app { display:flex; min-height:100vh; align-items:stretch; }
  .sidebar { width:228px; flex:none; border-right:1px solid var(--line); background:var(--side-bg);
          display:flex; flex-direction:column; padding:16px 13px; position:sticky; top:0;
          height:100vh; overflow-y:auto; }
  .brand { display:flex; align-items:center; gap:11px; padding:6px 8px 4px; text-decoration:none; color:var(--text); }
  .brand .orb { position:relative; width:34px; height:34px; border-radius:10px; flex:none;
          background:radial-gradient(120% 120% at 30% 25%,#d98a6a,#c4633f);
          display:flex; align-items:center; justify-content:center; overflow:hidden; }
  .brand .orb .ring { position:absolute; width:30px; height:30px; border-radius:50%;
          border:1.5px solid rgba(255,255,255,.5); animation:radarPulse 2.6s ease-out infinite; }
  .brand .bt { line-height:1.15; min-width:0; }
  .brand .bt b { font:700 15px var(--display); letter-spacing:-.01em; display:block; }
  .brand .bt small { font:9.5px var(--mono); letter-spacing:.14em; color:var(--faint); display:block; }
  .brand-sub { font-size:11px; color:var(--faint); padding:8px 8px 14px;
          border-bottom:1px solid var(--line); margin-bottom:12px; }
  .sidebar nav { display:flex; flex-direction:column; }
  .navgrp { font-size:10.5px; font-weight:700; letter-spacing:.08em; color:var(--faint);
          text-transform:uppercase; padding:16px 8px 7px; }
  .navitem { display:flex; align-items:center; gap:11px; width:100%; border:none; background:none;
          color:var(--dim); font:500 13.5px "Space Grotesk", sans-serif; padding:9px 10px;
          border-radius:9px; cursor:pointer; text-align:left; margin-bottom:1px; }
  .navitem:hover { background:var(--surface3); color:var(--text); }
  .navitem.active { background:var(--indigo-soft); color:var(--text); font-weight:600;
          box-shadow:inset 2.5px 0 0 var(--indigo); }
  .navitem .navcount { margin-left:auto; font:11px var(--mono); color:var(--faint); }
  .sidefoot { margin-top:auto; display:flex; align-items:center; gap:10px;
          padding:11px 8px 2px; border-top:1px solid var(--line); }
  .sidefoot .av { width:33px; height:33px; border-radius:50%; flex:none; color:#fff;
          background:linear-gradient(135deg,#d98a6a,#c4633f); display:flex;
          align-items:center; justify-content:center; font-weight:700; font-size:13px; }
  .sidefoot .who { line-height:1.2; min-width:0; }
  .sidefoot .who b { font-size:13px; font-weight:600; display:block; }
  .sidefoot .who small { font-size:11px; color:var(--faint); }
  .main { flex:1; min-width:0; display:flex; flex-direction:column; background:var(--bg); }
  .topbar { position:sticky; top:0; z-index:40; display:flex; align-items:center; gap:14px;
          padding:14px 26px; border-bottom:1px solid var(--line);
          background:var(--topbar-bg); backdrop-filter:blur(12px); }
  .ttitle { min-width:0; flex:1; }
  .ttitle .pt { font:600 21px var(--display); letter-spacing:-.01em; }
  .ttitle .ps { font-size:12.5px; color:var(--dim); margin-top:1px; }
  .tutil { flex:none; display:flex; align-items:center; gap:8px; }
  .main > .wrap { max-width:1180px; width:100%; padding:24px 26px 60px; }
  .scard .n, .qtime { font-family:var(--mono); }
  @media (max-width:900px) {
    .app { flex-direction:column; }
    .sidebar { width:100%; height:auto; position:sticky; top:0; flex-direction:row;
            align-items:center; overflow-x:auto; padding:8px 10px; gap:4px;
            border-right:none; border-bottom:1px solid var(--line); }
    .sidebar::-webkit-scrollbar { display:none; }
    .brand-sub, .navgrp, .sidefoot { display:none; }
    .brand { padding:0 6px 0 2px; flex:none; }
    .brand .bt small { display:none; }
    .navitem { width:auto; flex:none; white-space:nowrap; margin:0; }
    .navitem .navcount { display:none; }
    .topbar { padding:12px 16px; }
    .ttitle .pt { font-size:18px; }
    .main > .wrap { padding:16px 14px 60px; }
  }
</style>
</head>
<body class="dark">
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
<div class="app">
  <aside class="sidebar">
    <a class="brand" href="#" onclick="switchTab('home');return false">
      <span class="orb"><span class="ring"></span>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"></circle><path d="M12 12L19 8"></path></svg>
      </span>
      <span class="bt"><b>AI x Ahmad</b><small>RADAR STUDIO</small></span>
    </a>
    <div class="brand-sub">The World of AI, made simple</div>
    <nav>
      <button class="navitem active" id="tabbtn-home" onclick="switchTab('home')">🏠 <span>Home</span></button>
      <button class="navitem" id="tabbtn-news" onclick="switchTab('news')">📰 <span>News</span><span class="navcount" id="nc-news"></span></button>
      <button class="navitem" id="tabbtn-popular" onclick="switchTab('popular')">🔥 <span>Popular</span></button>
      <button class="navitem" id="tabbtn-trends" onclick="switchTab('trends')">📈 <span>Trends</span></button>
      <button class="navitem" id="tabbtn-pulse" onclick="switchTab('pulse')">⚡ <span>Pulse</span></button>
      <button class="navitem" id="tabbtn-research" onclick="switchTab('research')">📚 <span>Research</span></button>
      <div class="navgrp">Engagement</div>
      <button class="navitem" id="tabbtn-repurpose" onclick="switchTab('repurpose')">♻️ <span>Repurpose</span><span class="navcount" id="nc-rp"></span></button>
      <button class="navitem" id="tabbtn-xmini" onclick="switchTab('xmini')">✍️ <span>Write</span><span class="navcount" id="nc-xm"></span></button>
      <button class="navitem" id="tabbtn-inspire" onclick="switchTab('inspire')">💡 <span>Inspire</span></button>
      <button class="navitem" id="tabbtn-me" onclick="switchTab('me')">⭐ <span>Me</span></button>
    </nav>
    <div class="sidefoot">
      <span class="av">A</span>
      <span class="who"><b>@aixahmad</b><small id="rolelabel">Owner</small></span>
    </div>
  </aside>
  <main class="main">
    <header class="topbar">
      <div class="ttitle"><div class="pt" id="pageTitle">Home</div><div class="ps" id="pageSub">Your radar at a glance</div></div>
      <div class="tutil">
        <button class="themebtn" id="cloudbtn" onclick="cloudClick()" title="Live sync">☁️</button>
        <button class="themebtn" id="themebtn" onclick="toggleTheme()" title="Light / dark theme">🌙</button>
      </div>
    </header>
<div class="wrap">

  <section id="tab-home">
    <p class="homedate" id="homedate"><span class="live"></span> <span id="homedatetxt"></span></p>
    <div class="panel toppick" id="toppick"></div>
    <div class="panel" id="dailyx-panel">
      <h3 style="display:flex;align-items:center;gap:8px">✍️ Post on X today
        <button class="cp" id="dailyx-shuffle" style="margin-left:auto">🎲 Shuffle</button></h3>
      <div id="dailyx"></div>
    </div>
    <div class="statgrid" id="statgrid"></div>
    <div class="homecols">
      <div class="panel">
        <h3>⚡ Quick actions</h3>
        <button class="qa" onclick="qaNews()">🎯 Open latest news</button>
        <a class="qa" href="digests/latest.html" target="_blank" style="display:block;text-decoration:none">📄 Weekly digest — open &amp; Save as PDF</a>
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

  <section id="tab-popular" hidden>
    <p class="note">🔥 The AI stories the world is paying attention to right now — most-covered first.
       Great for picking what to post. Publishing one ticks all its copies, on every device.</p>
    <div id="poplist"></div>
  </section>

  <section id="tab-xmini" hidden>
    <div class="bar" style="margin-top:18px">
      <button id="xm-make" class="active" onclick="xmSwitch('make')">✍️ Make</button>
      <button id="xm-perf-btn" onclick="xmSwitch('perf')">📊 Performance</button>
    </div>
    <p class="note" id="xm-note">✍️ The Anthropic Write Engine thinks first, then writes short, original, text-only posts that grow the account. Pick a preset + style, type an idea (or tap one), generate, post. No links, no scraping, no auto-post — you copy &amp; post.</p>
    <div id="xmmake">
      <div class="xmsub">🎭 Style profile</div>
      <div class="xmchips" id="xm-styles"></div>
      <div class="xmsub">🧩 Preset</div>
      <div class="xmchips" id="xm-presets"></div>
      <textarea id="xm-seed" class="rphead" rows="2" placeholder="Type your idea, or paste text to rewrite — or tap an idea from the Idea bank below (optional)"></textarea>
      <div class="actions" style="margin-left:0;margin-top:6px">
        <button class="cp" id="xm-apigen" onclick="xmApiGenerate()">⚡ Generate (API)</button>
        <button class="cp" onclick="xmGen('claude')">🤖 Claude</button>
        <button class="cp" onclick="xmGen('gpt')">💬 ChatGPT</button>
        <button class="cp" onclick="xmPasteToggle()">📥 Paste result</button>
        <button class="cp" onclick="xmIdeasToggle()">💡 Idea bank</button>
        <button class="cp" onclick="xmApiToggle()">⚙️ API setup</button>
      </div>
      <div id="xm-apibox" hidden>
        <div class="note">⚡ One-click generation. One-time setup: paste your free Cloudflare Worker URL (it holds your Anthropic key — see <b>XMINI_API.md</b>). Your key never touches this site.</div>
        <input id="xm-apiurl" class="rphead" placeholder="https://x-writer.you.workers.dev">
        <div class="actions" style="margin-left:0;margin-top:6px"><button class="cp" onclick="xmApiSave()">💾 Save endpoint</button></div>
        <div class="note" id="xm-apistat"></div>
      </div>
      <div id="xm-paste" hidden>
        <textarea id="xm-savejson" class="rphead" rows="3" placeholder="Paste Claude/ChatGPT's JSON here, then Save"></textarea>
        <div class="actions" style="margin-left:0;margin-top:6px"><button class="cp" onclick="xmSave()">💾 Save & show posts</button></div>
      </div>
      <div id="xm-ideas" hidden></div>
      <div id="xm-result"></div>
      <div id="xm-captured"></div>
      <div class="sec-h" style="margin-top:10px">📝 Drafts</div>
      <div id="xm-drafts"></div>
    </div>
    <div id="xmperf" hidden></div>
  </section>

  <section id="tab-inspire" hidden>
    <p class="note">💡 Proven, useful content ideas — interactive posts, save-worthy lists, "what to do with it" news angles.
       Tap ✍️ to write it now or 💎 to get the full value-post pack (slides + infographic + captions).</p>
    <div class="search" style="margin-top:6px"><input id="insp-q" placeholder="Search ideas… prompt, tools, free, beginner"></div>
    <div id="insp-news"></div>
    <div id="insp-list"></div>
  </section>

  <section id="tab-me" hidden>
    <p class="note">⭐ YOU present the news — posters with your face announcing each story (news-anchor style, like the big IG news pages).
       Keep your photos saved in one ChatGPT chat; every prompt here starts with "use the attached photo of Ahmad".</p>
    <div class="pastebox">
      <textarea id="me-own" class="rphead" rows="2" placeholder="Or type your own announcement… e.g. 'I just crossed 1,000 followers' or 'New: my studio now writes posts with one click'"></textarea>
      <div class="actions" style="margin-left:0;margin-top:6px">
        <button class="cp" onclick="mePosterOwn()">🎨 Poster with me</button>
        <button class="cp" onclick="meCaptionOwn()">✍️ Write caption</button>
      </div>
    </div>
    <div id="me-news"></div>
  </section>

  <section id="tab-repurpose" hidden>
    <div class="bar" style="margin-top:18px">
      <button id="rv-inbox" class="active" onclick="rpSwitch('inbox')">♻️ Inbox</button>
      <button id="rv-perf" onclick="rpSwitch('perf')">📊 Performance</button>
    </div>
    <p class="note" id="rp-note">♻️ Capture an X or LinkedIn post → the AI writes original X / LinkedIn / comment versions for
       your brand. No copying, no auto-posting. Hit “✓ Posted” on the one you publish to track its performance.</p>
    <div class="pastebox" id="rp-add">
      <textarea id="rp-addtext" class="rphead" rows="2" placeholder="📋 On mobile? Paste a post here to repurpose it — no extension needed"></textarea>
      <div class="actions" style="margin-left:0;margin-top:6px">
        <button class="cp" id="rp-addx" onclick="rpAddManual('x')">➕ Add as 𝕏 post</button>
        <button class="cp" onclick="rpAddManual('linkedin')">➕ Add as LinkedIn post</button>
      </div>
    </div>
    <div id="rplist"></div>
    <div id="rpperf" hidden></div>
  </section>

  <section id="tab-trends" hidden>
    <p class="note">🚀 Which models and tools are rising this week vs last week — your early-warning
       radar for the next big thing. Tap any chip to see its stories.</p>
    <div class="trends" id="trends"></div>
  </section>

  <section id="tab-pulse" hidden>
    <style>
      .pulse-meta{color:var(--faint);font-size:12.5px;margin:18px 0 4px}
      .pulse-tow{background:var(--gold-soft);border:1px solid var(--gold);color:var(--text);
         border-radius:12px;padding:11px 14px;margin:10px 0 4px;font-size:14px}
      .pulse-fil{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 4px}
      .pulse-fil .chip{cursor:pointer}
      .pulse-h{font:700 14px var(--display);margin:24px 2px 10px}
      .pcard{background:var(--surface);border:1px solid var(--line);border-radius:14px;
         padding:14px 16px;margin-bottom:12px;box-shadow:var(--shadow-sm)}
      .pcard h4{margin:0 0 4px;font:600 16px var(--display);line-height:1.3}
      .pcard .row{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:6px 0}
      .pmom{font:700 10.5px Inter;text-transform:uppercase;letter-spacing:.04em;padding:2px 9px;border-radius:999px}
      .pmom.rising{background:var(--green-soft);color:var(--green)}
      .pmom.hot{background:var(--orange-soft);color:var(--orange)}
      .pmom.cooling{background:var(--blue-soft);color:var(--blue)}
      .pbadge{font-size:11px;color:var(--dim);background:var(--surface2);border:1px solid var(--line);border-radius:999px;padding:2px 9px}
      .pbadge.inf{font-style:italic;opacity:.85}
      .pangle{font-size:13.5px;color:var(--text);margin:6px 0;line-height:1.5}
      .plink{font-size:12px;color:var(--indigo);margin-right:10px;white-space:nowrap}
      .pidea{font-size:13px;color:var(--dim);margin:3px 0 3px 14px;line-height:1.45}
      .pact{display:flex;flex-wrap:wrap;gap:8px;margin-top:11px}
    </style>
    <p class="note">⚡ What people are actually <b>using, searching, and struggling with</b> in AI right now —
       turned into content ideas. Separate from News &amp; Trends; every item links to a real source.</p>
    <div class="pulse-meta" id="pulse-meta"></div>
    <div class="pulse-fil" id="pulse-fil"></div>
    <div id="pulse-body"></div>
  </section>

  <section id="tab-research" hidden>
    <p class="note">📚 Research papers — for your own learning. Never ranked as video candidates.</p>
    <div id="rlist"></div>
  </section>

  <input type="file" id="importfile" accept=".json" hidden>

</div>
  </main>
</div>

<div id="xmodal" hidden>
  <div class="mbox" style="max-width:560px">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
      <b style="font-size:15px">🚀 Post to X</b>
      <span id="x-quota" style="margin-left:auto;font-size:11.5px;color:var(--faint)"></span>
      <button class="ghost" style="padding:6px 11px" onclick="closeXModal()">✕</button>
    </div>
    <div id="x-story" class="note" style="margin:0 0 10px"></div>
    <div class="genrow">
      <select id="x-format" style="flex:1;min-width:130px" title="Format"></select>
      <select id="x-voice" style="flex:1;min-width:130px" title="Style / voice"></select>
    </div>
    <div class="genrow">
      <select id="x-hook" style="flex:1;min-width:130px" title="Opening hook"></select>
      <select id="x-lang"><option value="en">English (global)</option></select>
    </div>
    <div class="genrow" style="align-items:center;flex-wrap:wrap">
      <label style="font-size:12.5px;color:var(--dim);display:flex;align-items:center;gap:7px">
        <input type="checkbox" id="x-auto" style="width:16px;height:16px"> Full-auto (no preview)
      </label>
      <button class="ghost" style="margin-left:auto" id="x-copyprompt">🤖 Copy prompt for Claude</button>
      <button class="btn" id="x-write">✍️ Write (auto)</button>
    </div>
    <div id="x-out" hidden>
      <p class="note" style="margin:12px 0 4px">Review / edit — one tweet per block, separated by a blank line:</p>
      <textarea id="x-tweets" style="width:100%;min-height:170px;font-size:13px"></textarea>
      <div class="mfoot" style="flex-wrap:wrap">
        <button class="btn" id="x-tweet">🚀 Post to X</button>
        <button class="ghost" id="x-copy">📋 Copy thread</button>
        <button class="ghost" id="x-rewrite">↻ Rewrite</button>
        <button class="ghost" id="x-post" title="Needs a paid X API plan (separate from Premium)">🤖 API auto</button>
        <span id="x-result" style="margin-left:auto;font-size:12.5px"></span>
      </div>
      <p class="note" style="margin:8px 2px 0;font-size:11.5px">🚀 opens X with tweet 1 ready — just tap <b>Post</b>. For a thread, the replies are copied so you paste them under it. Make sure <b>@aixahmad</b> is your active X login.</p>
    </div>
  </div>
</div>
<div id="pubmodal" hidden>
  <div class="mbox" style="max-width:600px">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
      <b style="font-size:15px">🌐 Publish to your website</b>
      <button class="ghost" style="margin-left:auto;padding:6px 11px" onclick="closePub()">✕</button>
    </div>
    <input id="pub-title" type="text" style="width:100%;margin-bottom:8px" placeholder="Headline">
    <div class="genrow">
      <select id="pub-cat" style="flex:1;min-width:130px"></select>
      <input id="pub-img" style="flex:2;min-width:180px" placeholder="Image URL (or upload →)">
    </div>
    <div class="genrow" style="align-items:center;flex-wrap:wrap">
      <label class="ghost" style="cursor:pointer;padding:8px 12px;white-space:nowrap">📷 Upload
        <input type="file" id="pub-file" accept="image/*" hidden></label>
      <button class="ghost" type="button" id="pub-poster" title="Make a branded poster from the headline">🖼️ Make poster</button>
      <img id="pub-preview" alt="" style="height:44px;border-radius:8px;display:none;object-fit:cover">
      <span id="pub-imgnote" style="font-size:12px;color:var(--faint)"></span>
    </div>
    <input id="pub-url" type="text" style="width:100%;margin:8px 0" placeholder="Source link (optional)">
    <div class="genrow"><button class="ghost" id="pub-draft">🤖 Copy prompt (write with any AI)</button></div>
    <textarea id="pub-body" style="width:100%;min-height:200px" placeholder="Article body… (write it here, or use the prompt button → paste into any AI → paste the article back here). Leave a blank line between paragraphs."></textarea>
    <div class="mfoot" style="flex-wrap:wrap">
      <button class="btn" id="pub-go">🌐 Publish</button>
      <button class="ghost" id="pub-li" title="Publish first, then share it on LinkedIn">in Share on LinkedIn</button>
      <button class="ghost" id="pub-tweet" title="Optional: publish first, then post it on X">𝕏 Post to X</button>
      <span id="pub-result" style="margin-left:auto;font-size:12.5px"></span>
    </div>
    <div id="pub-list" style="margin-top:14px"></div>
  </div>
</div>
<div id="nrmodal" hidden>
  <div class="mbox" style="max-width:660px">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
      <b style="font-size:15px">in LinkedIn draft</b>
      <span style="font-size:11.5px;color:var(--faint)">one story → one useful post</span>
      <button class="ghost" style="margin-left:auto;padding:6px 11px" onclick="closeNewsroom()">✕</button>
    </div>
    <div id="nr-story" class="note" style="margin:0 0 10px"></div>
    <div class="note" style="margin:0 0 6px">
      <b style="color:var(--dim)">1.</b> Paste the facts you actually have — a few lines from the article. No AI can open the
      link, so without this it either guesses or (with these prompts) asks you for them.
    </div>
    <textarea id="nr-excerpt" style="width:100%;min-height:70px"
      placeholder="Paste 2-5 key sentences from the source: what changed, the numbers, the date, who said it…"></textarea>
    <div class="genrow" style="align-items:center;flex-wrap:wrap;margin-top:8px">
      <input id="nr-aud" type="text" style="flex:1;min-width:230px"
        placeholder="Who is this for? e.g. freelancers picking AI tools">
      <input id="nr-note" type="text" style="flex:1;min-width:230px"
        placeholder="Your own experience with this (optional)">
    </div>
    <div class="genrow" style="align-items:center;flex-wrap:wrap;margin-top:10px">
      <b style="font-size:12.5px;color:var(--dim)">2.</b>
      <button class="btn" id="nr-copy" title="One supported development and what it actually means for your audience">🧠 Insight prompt</button>
      <button class="btn" id="nr-value" title="One action, checklist or tradeoff the source genuinely supports">🛠️ Practical prompt</button>
      <span style="font-size:12px;color:var(--faint)">paste into ChatGPT / Gemini / Claude</span>
    </div>
    <div class="genrow" style="align-items:flex-start;flex-wrap:wrap;margin-top:8px">
      <b style="font-size:12.5px;color:var(--dim);margin-top:8px">3.</b>
      <textarea id="nr-in" style="flex:1;min-width:240px;min-height:80px"
        placeholder="Paste the FULL AI output here (with the [[MARKERS]]), then Validate."></textarea>
      <button class="btn" id="nr-parse" style="margin-top:0">Validate →</button>
    </div>
    <div id="nr-parsed" hidden style="margin-top:12px;border-top:1px solid var(--line);padding-top:12px">
      <div id="nr-status" class="note" style="margin:0 0 8px"></div>
      <textarea id="nr-post" style="width:100%;min-height:170px" placeholder="The LinkedIn post"></textarea>
      <div class="note" id="nr-sources" style="margin:8px 2px 0"></div>
      <details style="margin-top:8px">
        <summary style="cursor:pointer;font-size:12.5px;color:var(--dim)">🔍 Review notes — private, never part of the post</summary>
        <div class="note" id="nr-review" style="margin-top:6px;white-space:pre-wrap"></div>
      </details>
      <div class="mfoot" style="flex-wrap:wrap;margin-top:10px">
        <button class="btn" id="nr-copypost">📋 Copy post</button>
        <button class="ghost" id="nr-open">in Open LinkedIn</button>
        <button class="ghost" id="nr-posted" title="The only thing that marks this story handled">✓ Mark as posted</button>
      </div>
      <div class="note" style="margin:8px 2px 0;color:var(--faint)">
        Copying, or opening LinkedIn, changes nothing — only ✓ Mark as posted takes the story off your lists.
      </div>
      <div class="note" style="margin:12px 2px 4px">Optional — built from the post above, so a visual or version can never claim more than it does:</div>
      <div class="genrow" style="flex-wrap:wrap">
        <button class="ghost" id="nr-info" title="One 4:5 infographic carrying the whole point — 10-format library">🎨 Infographic prompt</button>
        <button class="ghost" id="nr-poster" title="News-style poster with the headline on it">🖼️ Poster prompt</button>
        <button class="ghost" id="nr-xver" title="Optional: adapt this one post for X">𝕏 X version</button>
        <button class="ghost" id="nr-reddit" title="Optional: check whether it fits a subreddit — needs that community's rules">🟠 Reddit check</button>
      </div>
    </div>
  </div>
</div>
<div class="toast" id="toast"></div>

<script src="templates.js?v=__CACHE__"></script>
<script>
/* ---- any crash shows on screen instead of silently blanking the app ---- */
window.onerror = function (msg, src, line) {
  try {
    const el = document.createElement("div");
    el.style.cssText = "position:fixed;bottom:10px;left:10px;right:10px;background:#7f1d1d;color:#fff;" +
      "padding:10px 14px;border-radius:10px;font:12px/1.5 Consolas,monospace;z-index:9999;white-space:pre-wrap";
    el.textContent = "⚠ App error (screenshot this): " + msg + " @ line " + line;
    el.onclick = () => el.remove();
    document.body.appendChild(el);
  } catch (e) {}
};

/* ---- access gate (light protection - keeps casual visitors out) ---- */
const LOCKHASH = "__LOCKHASH__";
const FBURL = "__FBURL__";   /* baked-in Firebase URL: any device auto-connects after unlock */
async function sha256(t) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t));
  return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join("");
}
async function tryUnlock() {
  const code = document.getElementById("lockcode").value.trim();
  if (await sha256(code) === LOCKHASH) {
    localStorage.setItem("unlock", LOCKHASH);
    BOARDKEY = (await sha256("aixboard:" + code)).slice(0, 40);  /* permanent board address from the code */
    localStorage.setItem("boardkey", BOARDKEY);
    document.getElementById("lock").hidden = true;
    autoConnect();   /* baked-in Firebase URL + this code => connect automatically */
  } else {
    document.getElementById("lockerr").textContent = "Wrong code - try again.";
  }
}
/* ---- repair URL: site/?fix=1 resets this device (role + sync) — board data stays ---- */
if (/[?&]fix=1/.test(location.search)) {
  ["role", "synccfg", "syncid", "boardrev", "edunlock"].forEach(k => localStorage.removeItem(k));
  location.replace(location.pathname);
}

/* ---- sync config can ride in the URL (#s=...) so a second device of your own
       pairs by opening one link. The editor-invite link is gone with editors. ---- */
const _esm = location.hash.match(/[#&]s=([^&]+)/);
const LINKSYNCCFG = _esm ? decodeURIComponent(_esm[1]) : "";
/* ---- theme (warm light by default — the Claude look; dark only if chosen) ---- */
if (localStorage.getItem("theme") === "dark") {
  document.body.classList.add("dark");
  document.getElementById("themebtn").textContent = "☀️";
} else {
  document.getElementById("themebtn").textContent = "🌙";
}
function toggleTheme() {
  const dark = document.body.classList.toggle("dark");
  localStorage.setItem("theme", dark ? "dark" : "light");
  document.getElementById("themebtn").textContent = dark ? "☀️" : "🌙";
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
let pillar = 0, hideDone = false, hotOnly = false, localOnly = false, mode = "latest", q = "", shown = PAGE;
let assFilter = "All", editingId = null;
/* storage reads never crash the app — corrupt values fall back to defaults */
function jload(key, fallback) {
  try {
    const v = JSON.parse(localStorage.getItem(key) || fallback);
    return v == null ? JSON.parse(fallback) : v;
  } catch (e) { return JSON.parse(fallback); }
}
const _done = jload("done", "[]");
const doneSet = new Set(Array.isArray(_done) ? _done : []);
/* ---- cross-device "done" + "published" sync via Firebase (every device agrees) ---- */
let POSTED = [];   /* signatures {u,t,l} of everything published, synced everywhere */
function normT(s) { return (s || "").toLowerCase().replace(/[^a-z0-9 ]+/g, "").replace(/\s+/g, " ").trim(); }
function sigHit(it, sig) {
  const keys = new Set([sig.u, ...(sig.l || [])].filter(Boolean));
  const t0 = normT(sig.t);
  return keys.has(it.u) || (it.l || []).some(u => keys.has(u)) || (t0 && normT(it.t) === t0);
}
/* tick every item — current OR newly-arrived later — that matches something published */
function applyPosted() {
  let n = 0;
  ITEMS.forEach(it => {
    if (!it.u || doneSet.has(it.u)) return;
    if (POSTED.some(sig => sigHit(it, sig))) { doneSet.add(it.u); n++; }
  });
  if (n) localStorage.setItem("done", JSON.stringify([...doneSet]));
  return n;
}
function fbRoot() { return FBURL ? FBURL.replace(/\/+$/, "") : ""; }
async function syncPull() {
  if (!FBURL) return;
  const base = fbRoot();
  try {
    const [d, p, pub] = await Promise.all([
      fetch(base + "/news_done.json").then(r => r.json()).catch(() => null),
      fetch(base + "/news_posted.json").then(r => r.json()).catch(() => null),
      fetch(base + "/published.json").then(r => r.json()).catch(() => null),
    ]);
    if (Array.isArray(d)) d.forEach(u => u && doneSet.add(u));
    const sigs = Array.isArray(p) ? p.filter(Boolean) : Object.values(p || {}).filter(Boolean);
    const pubSigs = Object.values(pub || {}).filter(Boolean).map(a => ({ u: a.url || "", t: a.title || "", l: [] }));
    POSTED = sigs.concat(pubSigs);
    applyPosted();
    localStorage.setItem("done", JSON.stringify([...doneSet]));
    try { render(); } catch (e) {}
    try { renderPopular(); } catch (e) {}
    try { navCounts(); } catch (e) {}
  } catch (e) {}
}
async function pushDone() {           /* last-write-wins; safe after syncPull unioned remote */
  if (!FBURL) return;
  try {
    await fetch(fbRoot() + "/news_done.json", { method: "PUT",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify([...doneSet]) });
  } catch (e) {}
}
async function pushPosted(sig) {
  if (!FBURL || !sig) return;
  try {
    let remote = await fetch(fbRoot() + "/news_posted.json").then(r => r.json()).catch(() => null);
    remote = Array.isArray(remote) ? remote.filter(Boolean) : Object.values(remote || {}).filter(Boolean);
    remote.push(sig);
    if (remote.length > 500) remote = remote.slice(-500);   /* keep it small */
    POSTED = remote;
    await fetch(fbRoot() + "/news_posted.json", { method: "PUT",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify(remote) });
  } catch (e) {}
}
let plans = jload("plans", "[]");
let etasks = jload("etasks", "[]");
function saveEtasks() { localStorage.setItem("etasks", JSON.stringify(etasks)); schedulePush(); }

/* ---- multiple editors: each has own workspace, notes, history; role = owner or one editor ---- */
let editors = jload("editors", "[]");
let enotes = jload("enotes", "{}");
let ehist = jload("ehist", "[]");
let settings = jload("settings", "{}");   /* shared config (e.g. Drive hook), synced to everyone */
let chatRead = jload("chatread", "{}");   /* {thread: lastSeenTs} per device — drives unread badges */
let chatCounts = {};                       /* {thread: {total, unread, lastTs}} from the live watcher */
function saveSettings() { localStorage.setItem("settings", JSON.stringify(settings)); schedulePush(); }

/* drop broken entries so one bad item can't blank the whole app */
function sanitizeBoard() {
  if (!Array.isArray(plans)) plans = [];
  plans = plans.filter(p => p && typeof p === "object");
  plans.forEach(p => {
    if (typeof p.title !== "string") p.title = String(p.title || "Untitled");
    if (!Array.isArray(p.platforms)) p.platforms = ["yt", "shorts"];
    if (!p.status) p.status = "idea";
    p.chk = p.chk || {};
  });
  if (!Array.isArray(etasks)) etasks = [];
  etasks = etasks.filter(t => t && typeof t === "object");
  etasks.forEach(t => { if (typeof t.title !== "string") t.title = String(t.title || "Task"); });
  if (!Array.isArray(editors)) editors = [];
  editors = editors.filter(e => e && typeof e === "object" && e.id && e.name);
  if (!enotes || typeof enotes !== "object" || Array.isArray(enotes)) enotes = {};
  if (!Array.isArray(ehist)) ehist = [];
  ehist = ehist.filter(h => h && typeof h === "object");
  if (!settings || typeof settings !== "object" || Array.isArray(settings)) settings = {};
}
sanitizeBoard();
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
/* ---- live cloud sync ----
   Backends: "fb:<databaseURL>|<secret>"  -> Firebase Realtime Database (recommended,
             instant updates via stream)  |  "bin:<id>" -> free public JSON bin.   */
let SYNCCFG = localStorage.getItem("synccfg") || "";
let BOARDKEY = localStorage.getItem("boardkey") || "";   /* permanent board address, derived from owner access code */
if (!SYNCCFG && localStorage.getItem("syncid")) {        /* migrate older bin sync */
  SYNCCFG = "bin:" + localStorage.getItem("syncid");
  localStorage.setItem("synccfg", SYNCCFG);
}
if (LINKSYNCCFG && LINKSYNCCFG !== SYNCCFG) {            /* a pairing link carries the config */
  SYNCCFG = LINKSYNCCFG;
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

/* boot fixes — must run AFTER the sync vars above exist (their saves push to sync) */
if (editors.length) adoptOrphans(editors[0].id);
if (ROLE !== "owner" && !edById(ROLE)) { ROLE = "owner"; localStorage.setItem("role", "owner"); }
/* an item with an editor is never a bare "idea" — their sequence starts at Script */
plans.forEach(p => { if (p.assignee === "Editor" && p.status === "idea") p.status = "script"; });

function boardState() {
  return { rev: Date.now(), plans: plans, etasks: etasks, editors: editors,
    enotes: enotes, ehist: ehist, settings: settings };
}
function applyBoard(data) {
  if (!data || typeof data !== "object") return;
  if (Array.isArray(data.plans)) plans = data.plans;
  if (Array.isArray(data.etasks)) etasks = data.etasks;
  if (Array.isArray(data.editors)) editors = data.editors;
  if (data.enotes && typeof data.enotes === "object") enotes = data.enotes;
  if (Array.isArray(data.ehist)) ehist = data.ehist;
  if (data.settings && typeof data.settings === "object") settings = data.settings;
  sanitizeBoard();
  localStorage.setItem("settings", JSON.stringify(settings));
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
/* make sure we have the permanent board address (derived from the owner access code) */
async function ensureBoardKey() {
  if (BOARDKEY) return BOARDKEY;
  const code = (prompt("Apna owner access code dobara likho — board ka permanent address banane ke liye:") || "").trim();
  if (!code) return "";
  if (await sha256(code) !== LOCKHASH) { toast("Wrong access code ❌"); return ""; }
  BOARDKEY = (await sha256("aixboard:" + code)).slice(0, 40);
  localStorage.setItem("boardkey", BOARDKEY);
  return BOARDKEY;
}
/* point this device at a board path: PULL first (recover), then seed/force-push */
async function connectSync(cfg, seedIfEmpty, forcePush) {
  if (syncStream) { syncStream.close(); syncStream = null; }
  SYNCCFG = cfg;
  localStorage.setItem("synccfg", SYNCCFG);
  syncReady = true;
  boardRev = 0; localStorage.setItem("boardrev", "0");   /* let the remote win the first pull */
  await pollBoard();
  const hasData = (plans && plans.length) || (editors && editors.length) || (etasks && etasks.length);
  let ok = true;
  if (forcePush) ok = await pushBoard();
  else if (seedIfEmpty && !hasData) ok = await pushBoard();
  if (isFb()) { startStream(); }
  setCloudIcon(true);
  rerender();
  if (!document.getElementById("tab-home").hidden) renderHome();
  return ok;
}
/* baked-in Firebase URL + permanent board key => connect with no link pasting */
async function autoConnect() {
  if (SYNCCFG || !FBURL || !BOARDKEY || ROLE !== "owner") return;
  await connectSync("fb:" + FBURL.replace(/\/+$/, "") + "|" + BOARDKEY, true);
  toast(isFb() ? "Live sync ON ⚡ (auto)" : "Live sync ON");
}
/* pull a connection config out of an editor link or a raw config string */
function recoverCfgFrom(text) {
  text = (text || "").trim();
  if (text.slice(0, 3) === "fb:" || text.slice(0, 4) === "bin:") return text;
  const m = text.match(/[#&?]s=([^&\s]+)/);
  if (m) return decodeURIComponent(m[1]);
  const m2 = text.match(/editor=\w+\.[0-9a-f]*\.([0-9a-f]{6,40})/);
  if (m2) return "bin:" + m2[1];
  return "";
}
async function enableSync() {
  const inp = (prompt(
    "Firebase Realtime Database URL paste karo (connect karne ke liye).\n\n" +
    "Kal ka board WAPIS chahiye? Apna purana EDITOR LINK yahan paste karo.\n\n" +
    "Empty chhodo = quick free bin:") || "").trim();
  if (inp) {
    /* --- recovery: pasted an editor link or a saved config string --- */
    const rec = recoverCfgFrom(inp);
    const looksUrl = /^https:\/\/[\w.-]+\.(firebasedatabase\.app|firebaseio\.com)\/?$/.test(inp);
    if (rec && !looksUrl) {
      await connectSync(rec, false);                 /* pull the old board onto this device */
      const recovered = (plans && plans.length) || (editors && editors.length) || (etasks && etasks.length);
      if (!recovered) { toast("Us link par koi board nahi mila — Firebase console check karo"); return; }
      if (rec.slice(0, 3) === "fb:") {               /* migrate it to the permanent address */
        const key = await ensureBoardKey();
        const url = rec.slice(3).split("|")[0];
        if (key) {
          await connectSync("fb:" + url.replace(/\/+$/, "") + "|" + key, false, true);
          toast("Board recover ho gaya ⚡ ab permanent address par hai — naye editor links bhejo");
          return;
        }
      }
      toast("Kal ka board wapis aa gaya ✓");
      return;
    }
    /* --- normal connect via Firebase URL → permanent deterministic path --- */
    if (!looksUrl) { toast("Ye na Firebase URL hai na editor link ❌"); return; }
    const key = await ensureBoardKey();
    if (!key) { toast("Board address ke liye access code chahiye"); return; }
    const ok = await connectSync("fb:" + inp.replace(/\/+$/, "") + "|" + key, true);
    if (!ok) {
      SYNCCFG = ""; localStorage.removeItem("synccfg"); setCloudIcon(true);
      toast("Firebase ne mana kar diya — Rules me boards read/write true karo, phir retry");
      return;
    }
    toast("Firebase live sync ON ⚡ permanent address — naye editor links bhejo");
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

/* keep the live-data tabs (Repurpose) fresh on their own —
   they read the cloud on demand, so without this you'd have to refresh to see a
   newly-approved post or capture. Skip while you're typing so it never wipes
   an input you're editing. */
function autoRefreshLive() {
  const a = document.activeElement;
  if (a && (a.tagName === "TEXTAREA" || a.tagName === "INPUT" || a.isContentEditable)) return;
  const vis = id => { const s = document.getElementById(id); return s && !s.hidden; };
  if (vis("tab-repurpose")) { try { renderRpTab(); } catch (e) {} }
}
setInterval(autoRefreshLive, 20000);
window.addEventListener("focus", autoRefreshLive);

/* migrate old planner cards to ticket format — each step runs ONCE, never again
   (the old !== checks re-ran on every load and stripped newer fields) */
const PV = +(localStorage.getItem("plans_v") || "1") || 1;
if (PV < 2) {
  const map = { record: "filming", edit: "editing", uploaded: "posted", published: "posted" };
  plans = plans.map(p => ({
    id: p.id, title: p.title, url: p.url || "", notes: p.notes || "",
    status: p.status || map[p.stage] || p.stage || "idea",
    assignee: p.assignee || "Ahmad",
    platforms: p.platforms || (p.platform === "long" ? ["yt"] :
               p.platform === "short" ? ["shorts"] : ["yt", "shorts"]),
    due: p.due || p.date || "",
  }));
}
if (PV < 3) {
  plans = plans.map(p => ({
    id: p.id, title: p.title, url: p.url || "", notes: p.notes || "",
    status: ({script:"draft",filming:"draft",editing:"draft"})[p.status] || p.status || "idea",
    assignee: p.assignee || "Ahmad",
    platforms: p.platforms || ["yt","shorts"],
    when: p.when || (p.due ? p.due + "T18:00" : ""),
  }));
}
if (PV < 4) {
  plans = plans.map(p => Object.assign(p, {
    status: p.status === "draft" ? "script" : p.status,
    ctype: p.ctype || "", chk: p.chk || {}, ftitle: p.ftitle || "",
  }));
}
if (PV < 4) {
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
  if (name === "plan" || name === "editors") name = "home";   /* Buffer/Editors removed */
  ["home","news","popular","trends","pulse","research","repurpose","xmini","inspire","me"].forEach(n => {
    const sec = document.getElementById("tab-" + n); if (sec) sec.hidden = n !== name;
    const btn = document.getElementById("tabbtn-" + n); if (btn) btn.classList.toggle("active", n === name);
  });
  const TT = { home:["Home","Your radar at a glance"], news:["News","The latest AI news, newest first"],
    popular:["Popular","What the world is reading right now"],
    trends:["Trends","Rising signals, week over week"], pulse:["Pulse","What people are using & searching"],
    research:["Research","Papers for your own learning"],
    repurpose:["Repurpose","Turn posts you see into your own content"],
    xmini:["Write","Anthropic Write Engine — short posts that grow the account"],
    inspire:["Inspire","Useful content ideas that actually get reach"],
    me:["Me","You present the news — posters with your face"] };
  const tt = TT[name] || ["",""];
  const pt = document.getElementById("pageTitle"), ps = document.getElementById("pageSub");
  if (pt) pt.textContent = tt[0]; if (ps) ps.textContent = tt[1];
  if (name === "home") renderHome();
  if (name === "popular") renderPopular();
  if (name === "repurpose") renderRpTab();
  if (name === "xmini") renderXMini();
  if (name === "inspire") renderInspire();
  if (name === "me") renderMeTab();
  if (name === "research") renderResearch();
  if (name === "pulse") renderPulse();
}
/* Buffer/Editors workspaces removed — kept as a no-op so sync callers are safe */
function rerender() {}
function ago(iso) {
  if (!iso) return "";
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 3600) return Math.max(1, s/60|0) + " min ago";
  if (s < 86400) return (s/3600|0) + "h ago";
  return (s/86400|0) + "d ago";
}
function esc(t) { const d = document.createElement("div"); d.textContent = t; return d.innerHTML; }

/* ---------------- News ---------------- */
/* Freshness multiplier so the "video-worthy" view favours today's stories and
   pushes anything older than ~4 days down (keeps it timely, not just popular). */
function freshFactor(iso) {
  const ageH = (Date.now() - new Date(iso).getTime()) / 3.6e6;
  if (ageH < 24) return 1.35;
  if (ageH < 48) return 1.15;
  if (ageH < 96) return 1.0;
  return 0.6;
}
function worthyRank(it) { return (it.sc || 0) * freshFactor(it.d || it.f); }
function filtered() {
  const needle = q.toLowerCase();
  let items = ITEMS.filter(it =>
    it.p !== 9 &&
    (!pillar || it.p === pillar) &&
    (!hideDone || !doneSet.has(it.u)) &&
    (!hotOnly || (it.l && it.l.length)) &&
    (!localOnly || it.lo) &&
    (!needle || it.t.toLowerCase().includes(needle)));
  items = items.slice().sort((a, b) =>   /* always newest PUBLISHED first */
    (b.d || b.f || "").localeCompare(a.d || a.f || ""));
  return items;
}
/* one news card (shared by the News feed and the Popular tab) */
function makeCard(it) {
  const d = document.createElement("div");
  d.className = "card" + (doneSet.has(it.u) ? " done" : "");
  let extra = "", hot = "";
  if (it.l && it.l.length) {
    hot = '<span class="pill hot">🔥 ' + (it.l.length + 1) + " sources</span>";
    extra = '<div class="extra">also covered by: ' + it.l.map(x =>
      '<a href="' + esc(x.url) + '" target="_blank" rel="noopener">' + esc(x.source) + "</a>").join("") + "</div>";
  }
  const why = "";
  d.innerHTML =
    '<h2><a href="' + esc(it.u) + '" target="_blank" rel="noopener">' + esc(it.t) + "</a></h2>" +
    '<div class="meta"><span class="pill">' + PILLARS[it.p] + "</span>" + hot +
    "<span>" + esc(it.s) + "</span><span>" + ago(it.d) + "</span>" +
    '<span class="actions">' +
    '<button class="nr-btn" title="Write a LinkedIn post from this story">in Write post</button>' +
    '<button class="pub-btn" title="Publish this as an article on your website">🌐</button>' +
    '<button class="x-btn" title="Optional: post this on X">🚀 X</button>' +
    '<button class="db">' + (doneSet.has(it.u) ? "undo" : "done ✓") + "</button>" +
    "</span></div>" + why + extra;
  d.querySelector(".db").onclick = () => {
    doneSet.has(it.u) ? doneSet.delete(it.u) : doneSet.add(it.u);
    localStorage.setItem("done", JSON.stringify([...doneSet]));
    pushDone(); render(); try { renderPopular(); } catch (e) {}
  };
  const xb = d.querySelector(".x-btn");
  if (xb) xb.onclick = () => openXModal(it);
  const pb2 = d.querySelector(".pub-btn");
  if (pb2) pb2.onclick = () => openPublishModal(it);
  const nb = d.querySelector(".nr-btn");
  if (nb) nb.onclick = () => openNewsroom(it);
  return d;
}
function render() {
  const items = filtered();
  document.getElementById("count").textContent =
    items.length + " stories" + (q ? ' for "' + q + '"' : "") +
    (pillar ? " in " + PILLARS[pillar] : "") + " · newest first";
  const list = document.getElementById("list");
  list.innerHTML = items.length ? "" : '<div class="empty">No stories found.</div>';
  items.slice(0, shown).forEach(it => list.appendChild(makeCard(it)));
  document.getElementById("more").style.display = items.length > shown ? "block" : "none";
}
/* Popular = what the world is paying attention to: most-covered first, then
   interest score, then recency. Skips done + research. */
function renderPopular() {
  const el = document.getElementById("poplist");
  if (!el) return;
  const pop = ITEMS.filter(it => it.p !== 9 && !doneSet.has(it.u))
    .map(it => ({ it, n: (it.l ? it.l.length : 0) }))
    .sort((a, b) => (b.n - a.n) || (worthyRank(b.it) - worthyRank(a.it)) ||
      ((b.it.d || b.it.f || "").localeCompare(a.it.d || a.it.f || "")))
    .slice(0, 40).map(x => x.it);
  el.innerHTML = pop.length ? "" : '<div class="empty">No popular stories yet — check back as coverage builds.</div>';
  pop.forEach(it => el.appendChild(makeCard(it)));
}
/* download the poster image (works cross-origin via blob; falls back to opening it) */
function downloadImage(url) {
  toast("Downloading image…");
  fetch(url).then(r => r.blob()).then(b => {
    const a = document.createElement("a"), u = URL.createObjectURL(b);
    a.href = u; a.download = "ai-radar-poster" + (b.type.includes("jpeg") ? ".jpg" : ".png");
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(u), 5000);
  }).catch(() => { window.open(url, "_blank", "noopener"); toast("Opened image — long-press / right-click to save"); });
}
/* ---------------- Post Repurpose Engine ---------------- */
function rpTypeLabel(t) {
  const m = { x_post: "𝕏 X post", linkedin_post: "in LinkedIn post", comment_reply: "💬 Comment / reply",
    question_post: "❓ Question post", hot_take: "🔥 Hot take", builder_angle: "🛠 Builder angle", skip: "⏭ Skip" };
  return m[t] || (t || "output").replace(/_/g, " ");
}
function rpPatch(key, obj) {
  return fetch(fbRoot() + "/social_captures/" + key + ".json", { method: "PATCH",
    headers: { "Content-Type": "application/json" }, body: JSON.stringify(obj) });
}
function rpCount() {
  if (!FBURL) return;
  fetch(fbRoot() + "/social_captures.json").then(r => r.json()).then(d => {
    const n = Object.values(d || {}).filter(v => v && v.status !== "skipped" && v.status !== "posted").length;
    const el = document.getElementById("nc-rp"); if (el) el.textContent = n || "";
  }).catch(() => {});
}
async function renderRepurpose() {
  const el = document.getElementById("rplist"); if (!el) return;
  const nc = document.getElementById("nc-rp");
  if (!FBURL) { el.innerHTML = '<div class="empty">Connect cloud sync to use the Repurpose Engine.</div>'; return; }
  el.innerHTML = '<div class="note">Loading…</div>';
  let data = {};
  try { data = (await (await fetch(fbRoot() + "/social_captures.json")).json()) || {}; } catch (e) {}
  const items = Object.entries(data || {}).filter(e => e[1] && e[1].status !== "skipped" && e[1].status !== "posted")
    .sort((a, b) => String(b[1].created_at || "").localeCompare(String(a[1].created_at || "")));
  if (nc) nc.textContent = items.length || "";
  if (!items.length) {
    el.innerHTML = '<div class="empty">No captured posts yet. Use the “Send to Radar Studio” extension on an X or LinkedIn post (on LinkedIn, select the post text first), then choose ♻️ Repurpose.</div>';
    return;
  }
  el.innerHTML = "";
  items.forEach(([key, c]) => {
    const d = document.createElement("div"); d.className = "card";
    const outs = c.outputs || [];
    const byType = t => outs.find(o => o.type === t);
    const imgHtml = c.image_url ? '<a class="rpimg" href="' + esc(c.image_url) + '" target="_blank" rel="noopener"><img src="' + esc(c.image_url) + '" loading="lazy" alt="post image"></a>' : "";
    const block = (label, o, badge, copyT) => {
      if (!o || !o.text) return "";
      const ptype = copyT === "__best__" ? (c.best_output_type || "x_post") : copyT;
      let postBtn = "";
      if (ptype === "x_post" || ptype === "hot_take" || ptype === "question_post")
        postBtn = '<button class="cp" data-act="postx" data-t="' + esc(copyT) + '">𝕏 Post on X</button>';
      else if (ptype === "linkedin_post")
        postBtn = '<button class="cp" data-act="postli" data-t="' + esc(copyT) + '">🔗 Post on LinkedIn</button>';
      else if (ptype === "comment_reply" && c.source_url)
        postBtn = '<button class="cp" data-act="opensrc">↗ Open post to comment</button>';
      return '<div class="xrep' + (badge ? " rec" : "") + '">' +
        '<div class="xrstyle">' + (badge ? '<span class="xrbadge">' + badge + '</span> ' : "") + esc(label) +
        (o.score ? ' · <span class="xrscore">' + o.score + '/10</span>' : "") + '</div>' +
        '<div class="xrtext">' + esc(o.text) + '</div>' +
        (o.reason ? '<div class="xreason">' + esc(o.reason) + '</div>' : "") +
        '<div class="xractions"><button class="cp" data-act="copyo" data-t="' + esc(copyT) + '">📋 Copy</button>' +
        postBtn +
        '<button class="cp" data-act="postout" data-t="' + esc(copyT) + '">✓ Posted</button></div></div>';
    };
    let body;
    if (outs.length) {
      const ana = '<div class="xranalysis">🤖 <b>AI read:</b> ' + esc(c.analysis || "") +
        (c.post_type ? ' <span class="xrtag">' + esc(c.post_type) + (c.best_action ? " → " + esc(c.best_action) : "") + '</span>' : "") +
        (c.recommend_why ? '<div class="xrrec">⭐ Best move: <b>' + esc(rpTypeLabel(c.best_output_type || c.best_action || "")) + '</b> — ' + esc(c.recommend_why) + '</div>' : "") + '</div>';
      const best = c.best_output ? { type: c.best_output_type || "best", text: c.best_output, score: "", reason: "" } : (byType(c.best_output_type) || outs[0]);
      const def =
        block("⭐ Best — " + rpTypeLabel((best && best.type) || ""), best, "Best", "__best__") +
        block("𝕏 X version", byType("x_post"), "", "x_post") +
        block("in LinkedIn version", byType("linkedin_post"), "", "linkedin_post") +
        block("💬 Comment / reply", byType("comment_reply"), "", "comment_reply");
      const shown = { x_post: 1, linkedin_post: 1, comment_reply: 1 };
      const rest = outs.filter(o => !shown[o.type]).map(o => block(rpTypeLabel(o.type), o, "", o.type)).join("");
      body = ana + '<div class="xreps">' + def + '</div>' +
        '<div class="actions" style="margin-left:0;margin-top:9px"><button class="cp" data-act="showall">👁 Show all outputs</button>' +
        '<button class="cp" data-act="regen">🔁 New</button>' +
        '<button class="cp" data-act="poster">🎨 Make image</button>' +
        (c.image_url ? '<button class="cp" data-act="dlimg">⬇ Original</button>' : "") +
        '<button class="cp" data-act="skip">Skip</button><button class="cp" data-act="del">🗑</button></div>' +
        '<div class="xrall" hidden><div class="sec-h" style="margin-top:8px">All outputs</div><div class="xreps">' + (rest || '<div class="note">no extra outputs</div>') + '</div></div>';
    } else {
      body = '<div class="actions" style="margin-left:0;margin-top:9px">' +
        '<button class="cp" data-act="gen" data-ai="claude">🤖 Open in Claude</button>' +
        '<button class="cp" data-act="gen" data-ai="gpt">⚡ Open in ChatGPT</button>' +
        '<button class="cp" data-act="pasteopen">📥 Paste outputs</button>' +
        '<button class="cp" data-act="poster">🎨 Make image</button>' +
        (c.image_url ? '<button class="cp" data-act="dlimg">⬇ Original</button>' : "") +
        '<button class="cp" data-act="skip">Skip</button><button class="cp" data-act="del">🗑</button></div>' +
        '<div class="xrpaste" hidden><textarea class="xrjson" placeholder="Paste Claude/ChatGPT\'s JSON object here, then Save"></textarea>' +
        '<div class="actions" style="margin-left:0;margin-top:6px"><button class="cp" data-act="saveouts">💾 Save outputs</button></div></div>';
    }
    d.innerHTML =
      '<div class="meta"><span class="pill">' + (c.platform === "linkedin" ? "in LinkedIn" : "𝕏 X") + '</span>' +
      '<span class="src">' + esc(c.author_name || "author") + '</span>' +
      (c.author_handle ? '<span>' + esc(c.author_handle.replace(/^https?:\/\/(www\.)?linkedin\.com/, "")) + '</span>' : "") +
      '<span class="pill">' + esc(c.status || "captured") + '</span>' +
      (c.source_url ? '<a class="cp" href="' + esc(c.source_url) + '" target="_blank" rel="noopener">↗ Open post</a>' : "") + '</div>' +
      '<div class="xrpost">' + esc(c.post_text || "") + '</div>' + imgHtml + body;
    d.querySelectorAll("[data-act]").forEach(b => b.onclick = () => rpAction(b.dataset.act, key, c, d, b));
    el.appendChild(d);
  });
}
async function rpAction(act, key, c, d, b) {
  if (act === "gen") {
    const ai = b.dataset.ai === "gpt" ? "ChatGPT" : "Claude";
    const url = b.dataset.ai === "gpt" ? "https://chatgpt.com/" : "https://claude.ai/new";
    navigator.clipboard.writeText(window.buildPostRepurposePrompt(c)).catch(() => {});
    window.open(url, "_blank", "noopener");
    const p = d.querySelector(".xrpaste"); if (p) p.hidden = false;
    toast("Prompt copied — paste it in " + ai + " ✓");
    return;
  }
  if (act === "showall") { const a = d.querySelector(".xrall"); if (a) { a.hidden = !a.hidden; b.textContent = a.hidden ? "👁 Show all outputs" : "🙈 Hide"; } return; }
  if (act === "pasteopen") { const p = d.querySelector(".xrpaste"); if (p) p.hidden = !p.hidden; return; }
  if (act === "saveouts") {
    const ta = d.querySelector(".xrjson"); let o;
    try { o = JSON.parse((ta.value || "").trim()); } catch (e) { toast("That isn't valid JSON — paste exactly what the AI returned"); return; }
    const outs = (o.outputs || []).map(x => ({ type: x.type || "x_post", text: String(x.text || "").trim(), score: (+x.score || 0), reason: String(x.reason || "") })).filter(x => x.text);
    if (!outs.length && !o.best_output) { toast("No outputs found in that JSON"); return; }
    await rpPatch(key, {
      outputs: outs, analysis: o.analysis || "", recommend_why: o.recommend_why || "",
      post_type: o.post_type || "", best_action: o.best_action || "",
      best_output_type: o.best_output_type || "", best_output: String(o.best_output || "").trim(),
      should_repurpose: o.should_repurpose !== false, status: "analyzed", updated_at: new Date().toISOString()
    });
    toast("Outputs saved ✓"); renderRepurpose(); return;
  }
  if (act === "copyo") {
    const t = b.dataset.t;
    const txt = t === "__best__" ? (c.best_output || "") : ((c.outputs || []).find(o => o.type === t) || {}).text || "";
    navigator.clipboard.writeText(txt).then(() => toast("Copied — paste & post ✓")); return;
  }
  if (act === "postx") {
    const t = b.dataset.t;
    const txt = t === "__best__" ? (c.best_output || "") : ((c.outputs || []).find(o => o.type === t) || {}).text || "";
    navigator.clipboard.writeText(txt).catch(() => {});
    window.open("https://twitter.com/intent/tweet?text=" + encodeURIComponent(txt), "_blank", "noopener");
    toast("Opening X (text prefilled & copied) — review, then post"); return;
  }
  if (act === "postli") {
    const t = b.dataset.t;
    const txt = t === "__best__" ? (c.best_output || "") : ((c.outputs || []).find(o => o.type === t) || {}).text || "";
    navigator.clipboard.writeText(txt).then(() => toast("Copied — paste (Ctrl+V) in the LinkedIn box ✓")).catch(() => toast("Opening LinkedIn — paste your post"));
    window.open("https://www.linkedin.com/feed/?shareActive=true", "_blank", "noopener"); return;
  }
  if (act === "opensrc") { if (c.source_url) window.open(c.source_url, "_blank", "noopener"); return; }
  if (act === "dlimg") { if (c.image_url) downloadImage(c.image_url); return; }
  if (act === "poster") { rpPosterPanel(d, c); return; }
  if (act === "postout") {
    const t = b.dataset.t;
    let outType, text;
    if (t === "__best__") { outType = c.best_output_type || "x_post"; text = c.best_output || ""; }
    else { outType = t; text = ((c.outputs || []).find(o => o.type === t) || {}).text || ""; }
    if (!text) { toast("Nothing to log"); return; }
    await rpPerfLog(c, outType, text);
    await rpPatch(key, { status: "posted", updated_at: new Date().toISOString() });
    toast("Logged to Performance — add metrics later ✓"); renderRepurpose(); return;
  }
  if (act === "regen") { await rpPatch(key, { outputs: [], status: "captured", updated_at: new Date().toISOString() }); renderRepurpose(); return; }
  if (act === "posted") { await rpPatch(key, { status: "posted", updated_at: new Date().toISOString() }); toast("Marked posted ✓"); renderRepurpose(); return; }
  if (act === "skip") { await rpPatch(key, { status: "skipped", updated_at: new Date().toISOString() }); toast("Skipped"); renderRepurpose(); return; }
  if (act === "del") { try { fetch(fbRoot() + "/social_captures/" + key + ".json", { method: "DELETE" }); } catch (e) {} d.remove(); toast("Removed"); return; }
}

/* ---- Repurpose performance: which of YOUR repurposed posts actually grow ---- */
let rpView = "inbox";
function renderRpTab() { return rpView === "perf" ? renderRpPerf() : renderRepurpose(); }
function rpSwitch(v) {
  rpView = v;
  const i = document.getElementById("rv-inbox"), p = document.getElementById("rv-perf");
  if (i) i.classList.toggle("active", v === "inbox"); if (p) p.classList.toggle("active", v === "perf");
  const list = document.getElementById("rplist"), perf = document.getElementById("rpperf");
  if (list) list.hidden = v !== "inbox"; if (perf) perf.hidden = v !== "perf";
  const add = document.getElementById("rp-add"); if (add) add.hidden = v !== "inbox";
  const note = document.getElementById("rp-note");
  if (note) note.textContent = v === "perf"
    ? "📊 Each repurposed post you publish. Add likes / replies / reposts ~24h later to learn which moves grow @aixahmad."
    : "♻️ Capture an X or LinkedIn post → the AI writes original versions for your brand. Hit “✓ Posted” on the one you publish to track it.";
  renderRpTab();
}
async function rpAddManual(platform) {
  if (!FBURL) { toast("Connect cloud sync first"); return; }
  const ta = document.getElementById("rp-addtext"), t = (ta.value || "").trim();
  if (!t) { toast("Paste the post text first"); return; }
  const id = String(Date.now()), now = new Date().toISOString();
  const rec = { id: id, platform: platform || "x", source_url: "", author_name: "", author_handle: "",
    post_text: t, screenshot_url: "", image_url: "", post_type: "", best_action: "", status: "captured",
    ai_analysis: "", recommended_output: "", outputs: [], created_at: now, updated_at: now };
  try { await fetch(fbRoot() + "/social_captures/" + id + ".json", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(rec) }); } catch (e) {}
  ta.value = "";
  toast("Added ✓ — now generate versions"); if (rpView !== "inbox") rpSwitch("inbox"); else renderRepurpose();
}
async function rpPerfLog(c, outType, text) {
  if (!FBURL) return;
  const id = String(Date.now()) + Math.floor((window.performance && performance.now ? performance.now() : 0));
  const now = new Date().toISOString();
  const platform = outType === "linkedin_post" ? "linkedin" : (outType === "comment_reply" ? (c.platform || "x") : "x");
  const rec = {
    id, output_type: outType, output_text: text, platform,
    post_type: c.post_type || "", best_action: c.best_action || "",
    source_author: c.author_handle || c.author_name || "", source_url: c.source_url || "",
    emoji_used: xrHasEmoji(text), character_count: (text || "").length, posted_at: now,
    likes_count: 0, replies_count: 0, reposts_count: 0, bookmarks_count: 0,
    impressions_count: 0, profile_clicks_count: 0, performance_score: 0, notes: "",
    created_at: now, updated_at: now
  };
  try { await fetch(fbRoot() + "/repurpose_performance/" + id + ".json", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(rec) }); } catch (e) {}
}
function rpPerfCard(r) {
  return '<div class="card" data-pk="' + esc(r._k) + '">' +
    '<div class="xrtext">' + esc(r.output_text || "") + '</div>' +
    '<div class="meta"><span class="pill">' + esc(rpTypeLabel(r.output_type)) + '</span>' +
    '<span class="pill">' + (r.platform === "linkedin" ? "in LinkedIn" : "𝕏 X") + '</span>' +
    (r.post_type ? '<span>' + esc(r.post_type) + '</span>' : "") +
    '<span>' + (r.character_count || 0) + ' chars' + (r.emoji_used ? " · emoji" : "") + '</span>' +
    '<span class="src">⭐ score ' + (+r.performance_score || 0) + '</span></div>' +
    '<div class="xpmetrics">' +
    xpNum("👍 Likes", "likes_count", r.likes_count) + xpNum("💬 Replies", "replies_count", r.replies_count) +
    xpNum("🔁 Reposts", "reposts_count", r.reposts_count) + xpNum("🔖 Bookmarks", "bookmarks_count", r.bookmarks_count) +
    xpNum("📈 Impressions", "impressions_count", r.impressions_count) + xpNum("👤 Profile clicks", "profile_clicks_count", r.profile_clicks_count) +
    '<label class="xpf xpnotes">Notes<input type="text" class="xpi" data-f="notes" value="' + esc(r.notes || "") + '"></label>' +
    '<button class="cp" data-rpx>💾 Save metrics</button><button class="cp" data-rpxdel>🗑</button>' +
    '</div></div>';
}
async function rpPerfSave(btn) {
  const card = btn.closest("[data-pk]"); if (!card) return;
  const key = card.getAttribute("data-pk");
  const m = {};
  card.querySelectorAll(".xpi").forEach(inp => { m[inp.dataset.f] = inp.type === "number" ? (+inp.value || 0) : inp.value; });
  m.performance_score = xpScore(m); m.updated_at = new Date().toISOString();
  try { await fetch(fbRoot() + "/repurpose_performance/" + key + ".json", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(m) }); } catch (e) {}
  toast("Saved · score " + m.performance_score + " ⭐"); renderRpPerf();
}
async function rpPerfDel(btn) {
  const card = btn.closest("[data-pk]"); if (!card) return;
  const key = card.getAttribute("data-pk");
  try { fetch(fbRoot() + "/repurpose_performance/" + key + ".json", { method: "DELETE" }); } catch (e) {}
  card.remove(); toast("Removed");
}
async function renderRpPerf() {
  const el = document.getElementById("rpperf"); if (!el) return;
  if (!FBURL) { el.innerHTML = '<div class="empty">Connect cloud sync to track performance.</div>'; return; }
  el.innerHTML = '<div class="note">Loading…</div>';
  let data = {};
  try { data = (await (await fetch(fbRoot() + "/repurpose_performance.json")).json()) || {}; } catch (e) {}
  const rows = Object.entries(data || {}).filter(e => e[1]).map(e => { const o = e[1]; o._k = e[0]; return o; });
  if (!rows.length) {
    el.innerHTML = '<div class="empty">Nothing tracked yet. Publish a repurposed version, hit “✓ Posted” on it, then come back ~24h later and add likes / replies / reposts.</div>';
    return;
  }
  const avgBy = (fn) => {
    const g = {};
    rows.forEach(r => { const k = fn(r); if (k == null || k === "") return; (g[k] = g[k] || []).push(+r.performance_score || 0); });
    return Object.entries(g).map(([k, a]) => [k, a.reduce((s, x) => s + x, 0) / a.length, a.length])
      .sort((x, y) => y[1] - x[1]);
  };
  const blk = (title, pairs, fmt) => '<div class="xpk"><div class="sec-h">' + title + '</div>' +
    (pairs.length ? pairs.map(([k, avg, n]) => '<div class="xprow"><span>' + esc(fmt ? fmt(k) : k) + '</span><b>' + avg.toFixed(1) + '</b><small>' + n + '</small></div>').join("") : '<div class="note">no data yet</div>') + '</div>';
  const top = rows.slice().sort((a, b) => (+b.performance_score || 0) - (+a.performance_score || 0)).slice(0, 10);
  const hist = rows.slice().sort((a, b) => String(b.posted_at || "").localeCompare(String(a.posted_at || "")));
  el.innerHTML =
    '<div class="xgrid">' +
    blk("Best output type", avgBy(r => r.output_type), rpTypeLabel) +
    blk("Best platform", avgBy(r => r.platform), k => k === "linkedin" ? "in LinkedIn" : "𝕏 X") +
    blk("From post type", avgBy(r => r.post_type)) +
    blk("Emoji vs none", avgBy(r => r.emoji_used ? "with emoji" : "no emoji")) +
    blk("Short vs long", avgBy(r => (+r.character_count || 0) <= 150 ? "short (≤150)" : "long (>150)")) +
    '</div>' +
    '<div class="sec-h xptop">🏆 Top performers</div>' +
    top.map(r => '<div class="xprow xptopr"><span>' + esc((r.output_text || "").slice(0, 90)) + '</span><b>' + (+r.performance_score || 0) + '</b><small>' + esc(rpTypeLabel(r.output_type)) + '</small></div>').join("") +
    '<div class="sec-h xptop">📊 All posts — add the numbers</div>' +
    hist.map(rpPerfCard).join("");
  el.querySelectorAll("[data-rpx]").forEach(b => b.onclick = () => rpPerfSave(b));
  el.querySelectorAll("[data-rpxdel]").forEach(b => b.onclick = () => rpPerfDel(b));
}

/* ---- Make your own branded image for a repurposed post ($0, on-canvas) ---- */
function rpPosterHeadline(c) {
  let s = (c.best_output && c.best_output.length <= 120 ? c.best_output : "") || c.post_text || "";
  s = s.replace(/https?:\/\/\S+/g, "").split(/\n|(?<=[.!?])\s/)[0].trim();
  return s.slice(0, 120);
}
function rpImagePrompt(c, headline) {
  const hi = (window.HUMAN_IMAGE || "Realistic photo-based editorial social graphic, vertical 4:5, top 70% photo / bottom 30% headline band, natural lighting, no AI/sci-fi look, no logos or watermark.");
  return hi + '\n' +
    'Scene relevant to this post: "' + (c.post_text || "").slice(0, 220) + '"\n' +
    'Headline to render in the bottom band, word for word: "' + headline + '"';
}
function rpDrawPoster(canvas, opts) {
  const W = 1080, H = 1350, x = canvas.getContext("2d");
  canvas.width = W; canvas.height = H;
  if (opts.img) {
    const im = opts.img, r = Math.max(W / im.width, H / im.height), w = im.width * r, h = im.height * r;
    x.drawImage(im, (W - w) / 2, (H - h) / 2, w, h);
    const g = x.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, "rgba(12,9,6,.25)"); g.addColorStop(.5, "rgba(12,9,6,.55)"); g.addColorStop(1, "rgba(12,9,6,.93)");
    x.fillStyle = g; x.fillRect(0, 0, W, H);
  } else {
    const g = x.createLinearGradient(0, 0, W, H);
    g.addColorStop(0, "#1a1410"); g.addColorStop(.55, "#3a2418"); g.addColorStop(1, "#b85735");
    x.fillStyle = g; x.fillRect(0, 0, W, H);
    const rg = x.createRadialGradient(W * .8, H * .2, 0, W * .8, H * .2, 640);
    rg.addColorStop(0, "rgba(240,168,104,.38)"); rg.addColorStop(1, "rgba(0,0,0,0)");
    x.fillStyle = rg; x.fillRect(0, 0, W, H);
  }
  x.textBaseline = "alphabetic";
  x.font = "800 34px Inter, Arial, sans-serif"; x.fillStyle = "#f0a868";
  x.fillText((opts.category || "AI").toUpperCase().slice(0, 28), 72, 132);
  const txt = opts.headline || "";
  const fs = txt.length > 120 ? 60 : txt.length > 80 ? 72 : txt.length > 46 ? 86 : 98;
  x.font = "900 " + fs + "px Inter, Arial, sans-serif"; x.fillStyle = "#ffffff";
  const lines = _wrapLines(x, txt, W - 144).slice(0, 6), lh = Math.round(fs * 1.16);
  let y = H - 230 - (lines.length - 1) * lh;
  lines.forEach(l => { x.fillText(l, 72, y); y += lh; });
  x.font = "800 42px Inter, Arial, sans-serif"; x.fillStyle = "#ffffff"; x.fillText("AI x Ahmad", 72, H - 116);
  x.font = "600 30px Inter, Arial, sans-serif"; x.fillStyle = "rgba(255,255,255,.82)"; x.fillText("@aixahmad", 72, H - 70);
}
function rpPosterPanel(d, c) {
  let panel = d.querySelector(".rppanel");
  if (panel) { panel.hidden = !panel.hidden; return; }
  panel = document.createElement("div"); panel.className = "rppanel";
  const suggest = rpPosterHeadline(c);
  panel.innerHTML =
    '<div class="sec-h" style="margin-top:4px">🎨 Make your own branded image</div>' +
    '<textarea class="rphead" rows="2" placeholder="Headline to put on the image (short & punchy)">' + esc(suggest) + '</textarea>' +
    '<div class="actions" style="margin-left:0;margin-top:6px">' +
    '<button class="cp" data-rp="gen">🖼 Branded poster</button>' +
    (c.image_url ? '<button class="cp" data-rp="genphoto">🖼 Over the photo</button>' : "") +
    '<button class="cp" data-rp="prompt">🤖 AI image prompt</button></div>' +
    '<canvas class="rpcanvas" style="display:none"></canvas>' +
    '<div class="actions" style="margin-left:0;margin-top:6px"><button class="cp rpdl" data-rp="dl" style="display:none">⬇ Download image</button></div>';
  d.querySelector(".xrpost").after(panel);
  const canvas = panel.querySelector(".rpcanvas");
  const head = () => ((panel.querySelector(".rphead").value || suggest).trim()) || suggest;
  const show = () => { canvas.style.display = "block"; panel.querySelector(".rpdl").style.display = ""; };
  panel.querySelectorAll("[data-rp]").forEach(b => b.onclick = () => {
    const a = b.dataset.rp;
    if (a === "gen") { rpDrawPoster(canvas, { headline: head(), category: c.post_type || "AI" }); show(); toast("Poster ready — ⬇ Download"); }
    else if (a === "genphoto") {
      const im = new Image(); im.crossOrigin = "anonymous";
      im.onload = () => { try { rpDrawPoster(canvas, { headline: head(), img: im, category: c.post_type || "AI" }); canvas.toDataURL(); show(); toast("Poster ready — ⬇ Download"); } catch (e) { rpDrawPoster(canvas, { headline: head(), category: c.post_type || "AI" }); show(); toast("Site blocked the photo — made a branded poster instead"); } };
      im.onerror = () => { rpDrawPoster(canvas, { headline: head(), category: c.post_type || "AI" }); show(); toast("Site blocked the photo — branded poster made instead"); };
      im.src = c.image_url;
    }
    else if (a === "prompt") { navigator.clipboard.writeText(rpImagePrompt(c, head())).catch(() => {}); window.open("https://chatgpt.com/", "_blank", "noopener"); toast("Image prompt copied — paste in ChatGPT/Gemini 🎨"); }
    else if (a === "dl") { const link = document.createElement("a"); link.href = canvas.toDataURL("image/jpeg", 0.9); link.download = "aixahmad-poster.jpg"; document.body.appendChild(link); link.click(); link.remove(); toast("Downloaded ✓ — attach it to your post"); }
  });
}

/* ===================== X Mini Post Engine ===================== */
let xmView = "make", xmPreset = "", xmStyle = null;
const XM_CATL = { question: "❓ Question", funny: "😅 Funny", fact: "📌 Fact", hot_take: "🔥 Hot take",
  builder: "🛠 Builder", relatable: "🤝 Relatable", shower_thought: "🚿 Shower thought", comparison: "⚔️ Comparison",
  community: "👋 Community", truth: "✨ Truth", debate: "⚖️ Debate", personal: "🌱 Personal",
  build_in_public: "🚧 Build in public", skeptical: "🧊 Skeptical" };
function xmCatLabel(c) { return XM_CATL[c] || (c || "post").replace(/_/g, " "); }
function xmFindPreset(slug) { return (window.XMINI_PRESETS || []).find(p => p[1] === slug) || null; }
function xmStyleChips() {
  const el = document.getElementById("xm-styles"); if (!el || !window.XMINI_STYLES) return;
  const cur = xmStyle ? xmStyle[0] : "";
  el.innerHTML = '<button class="chip' + (cur === "" ? " active" : "") + '" data-st="">✨ Auto</button>' +
    window.XMINI_STYLES.map(s => '<button class="chip' + (cur === s[0] ? " active" : "") + '" data-st="' + esc(s[0]) + '" title="' + esc(s[1]) + '">' + esc(s[0]) + '</button>').join("");
  el.querySelectorAll("[data-st]").forEach(b => b.onclick = () => { xmStyle = b.dataset.st ? (window.XMINI_STYLES.find(s => s[0] === b.dataset.st) || null) : null; xmStyleChips(); });
}
function xmScore(m) {
  return (+m.likes || 0) + (+m.replies || 0) * 3 + (+m.reposts || 0) * 4 + (+m.bookmarks || 0) * 5 +
    (+m.profile_clicks || 0) * 6 + (+m.follows || 0) * 10;
}
function xmPresetName(slug) { const p = (window.XMINI_PRESETS || []).find(x => x[1] === slug); return p ? p[2] : (slug || "—"); }
function xmSwitch(v) {
  xmView = v;
  const mk = document.getElementById("xm-make"), pf = document.getElementById("xm-perf-btn");
  if (mk) mk.classList.toggle("active", v === "make"); if (pf) pf.classList.toggle("active", v === "perf");
  const mm = document.getElementById("xmmake"), pp = document.getElementById("xmperf");
  if (mm) mm.hidden = v !== "make"; if (pp) pp.hidden = v !== "perf";
  v === "perf" ? renderXmPerf() : renderXMini();
}
function xmPresetChips() {
  const el = document.getElementById("xm-presets"); if (!el || !window.XMINI_PRESETS) return;
  el.innerHTML = '<button class="chip' + (xmPreset === "" ? " active" : "") + '" data-ps="">✨ Auto</button>' +
    window.XMINI_PRESETS.map(p => '<button class="chip' + (xmPreset === p[1] ? " active" : "") + '" data-ps="' + p[1] + '" title="' + esc(p[3]) + '">' + esc(p[2]) + '</button>').join("");
  el.querySelectorAll("[data-ps]").forEach(b => b.onclick = () => { xmPreset = b.dataset.ps; xmPresetChips(); });
}
function xmGen(ai) {
  const seed = (document.getElementById("xm-seed").value || "").trim();
  const prompt = window.buildAnthropicWritePrompt({ seed: seed, preset: xmPreset ? xmFindPreset(xmPreset) : null, style: xmStyle });
  navigator.clipboard.writeText(prompt).catch(() => {});
  window.open(ai === "gpt" ? "https://chatgpt.com/" : "https://claude.ai/new", "_blank", "noopener");
  const p = document.getElementById("xm-paste"); if (p) p.hidden = false;
  toast("Prompt copied — paste in " + (ai === "gpt" ? "ChatGPT" : "Claude") + ", then paste its JSON back ✓");
}
function xmPasteToggle() { const p = document.getElementById("xm-paste"); if (p) p.hidden = !p.hidden; }
function xmIdeasToggle() {
  const el = document.getElementById("xm-ideas"); if (!el) return;
  el.hidden = !el.hidden;
  if (!el.hidden && !el.innerHTML) {
    const I = window.XMINI_IDEAS || {};
    el.innerHTML = Object.keys(I).map(cat => '<div class="xmig"><div class="sec-h">' + xmCatLabel(cat) + '</div>' +
      I[cat].map(t => '<button class="xmidea" data-seed="' + esc(t) + '">' + esc(t) + '</button>').join("") + '</div>').join("");
    el.querySelectorAll("[data-seed]").forEach(b => b.onclick = () => {
      document.getElementById("xm-seed").value = b.getAttribute("data-seed");
      toast("Idea loaded — pick a style & generate"); window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }
}
function xmPostBlock(text, category, badge) {
  const len = (text || "").length;
  return '<div class="xrep' + (badge ? " rec" : "") + '" data-cat="' + esc(category || "") + '">' +
    '<div class="xrstyle">' + (badge ? '<span class="xrbadge">' + badge + '</span> ' : "") + xmCatLabel(category || "") +
    ' · <span class="xrscore' + (len > 280 ? " over" : "") + '">' + len + '/280</span></div>' +
    '<div class="xrtext">' + esc(text) + '</div>' +
    '<div class="xractions"><button class="cp" data-xm="copy">📋 Copy</button>' +
    '<button class="cp" data-xm="postx">𝕏 Post on X</button>' +
    '<button class="cp" data-xm="posted">✓ Posted</button></div></div>';
}
function xmWireBlocks(scope, draft) {
  const extra = draft ? { preset: draft.preset, style: draft.style_profile } : {};
  const did = draft ? (draft.id || draft._k) : "";
  scope.querySelectorAll(".xrep").forEach(rep => {
    rep.querySelectorAll("[data-xm]").forEach(b => b.onclick = () => {
      const text = rep.querySelector(".xrtext").textContent, cat = rep.getAttribute("data-cat") || "", act = b.dataset.xm;
      if (act === "copy") navigator.clipboard.writeText(text).then(() => toast("Copied — paste & post ✓"));
      else if (act === "postx") { navigator.clipboard.writeText(text).catch(() => {}); window.open("https://twitter.com/intent/tweet?text=" + encodeURIComponent(text), "_blank", "noopener"); toast("Opening X (prefilled & copied) — review, then post"); }
      else if (act === "posted") xmPosted(did, text, cat, extra);
    });
  });
}
function xmRiskPill(lbl, v) { return v ? '<span class="xpill ' + (v === "high" ? "r-high" : v === "medium" ? "r-med" : "r-low") + '">' + lbl + ': ' + esc(v) + '</span>' : ""; }
function xmRenderResult(draft) {
  const el = document.getElementById("xm-result"); if (!el) return;
  if (!draft || (!draft.best_post && !(draft.all_options || []).length)) { el.innerHTML = ""; return; }
  const opts = draft.all_options || [];
  const rest = opts.filter(o => o.text && o.text !== draft.best_post).map(o => xmPostBlock(o.text, o.category)).join("");
  const badges = '<div class="xbadges">' +
    '<span class="xpill">' + xmCatLabel(draft.best_category) + '</span>' +
    (draft.style_profile ? '<span class="xpill">🎭 ' + esc(draft.style_profile) + '</span>' : "") +
    xmRiskPill("copy", draft.copy_risk) + xmRiskPill("facts", draft.factuality_risk) +
    (draft.post_quality_score ? '<span class="xpill">⭐ ' + draft.post_quality_score + '/10</span>' : "") + '</div>';
  const refine = '<div class="actions" style="margin-left:0;margin-top:8px">' +
    '<button class="cp" data-rf="__regen">🔁 Regenerate</button>' +
    '<button class="cp" data-rf="make it funnier while keeping it true">😅 Funnier</button>' +
    '<button class="cp" data-rf="make it sharper and more punchy">🔪 Sharper</button>' +
    '<button class="cp" data-rf="make it simpler and shorter">🧹 Simpler</button>' +
    '<button class="cp" data-rf="turn it into a real question that invites replies">❓ To question</button>' +
    '<button class="cp" data-rf="turn it into a bold but defensible hot take">🔥 To hot take</button></div>';
  el.innerHTML = '<div class="card">' + badges +
    (draft.analysis ? '<div class="xranalysis">🤖 ' + esc(draft.analysis) + '</div>' : "") +
    (draft.best_post ? xmPostBlock(draft.best_post, draft.best_category, "Best") : "") +
    (draft.backup_posts || []).map(t => xmPostBlock(t, draft.best_category)).join("") +
    (draft.improvement_tip ? '<div class="xreason">💡 ' + esc(draft.improvement_tip) + '</div>' : "") +
    refine +
    (rest ? '<div class="actions" style="margin-left:0;margin-top:8px"><button class="cp" id="xm-showall">👁 Show all options</button></div>' +
      '<div class="xrall" hidden><div class="xreps">' + rest + '</div></div>' : "") + '</div>';
  const sa = el.querySelector("#xm-showall"), all = el.querySelector(".xrall");
  if (sa && all) sa.onclick = () => { all.hidden = !all.hidden; sa.textContent = all.hidden ? "👁 Show all options" : "🙈 Hide"; if (!all.hidden) xmWireBlocks(all, draft); };
  el.querySelectorAll("[data-rf]").forEach(b => b.onclick = () => { const v = b.dataset.rf; v === "__regen" ? xmApiGenerate() : xmRefine(v, draft); });
  xmWireBlocks(el, draft);
}
async function xmStoreDraft(o, source) {
  const opts = (o.all_options || []).map(x => ({ category: x.category || "", text: String(x.text || "").trim(), score: +x.score || 0, why: String(x.why || "") })).filter(x => x.text);
  const best = String(o.best_output || o.best_post || "").trim();
  const backups = (o.backup_outputs || o.backup_posts || []).map(s => String(s || "").trim()).filter(Boolean);
  if (!best && !opts.length) return null;
  const id = String(Date.now());
  const draft = {
    id: id, seed: (document.getElementById("xm-seed").value || "").trim(), preset: xmPreset || "",
    style_profile: o.style_profile || (xmStyle ? xmStyle[0] : ""),
    analysis: o.analysis || "", input_type: o.input_type || "",
    best_category: o.best_category || (opts[0] && opts[0].category) || "",
    copy_risk: o.copy_risk || "", factuality_risk: o.factuality_risk || "",
    post_quality_score: +o.post_quality_score || 0, improvement_tip: o.improvement_tip || "",
    best_post: best || (opts[0] && opts[0].text) || "", backup_posts: backups,
    all_options: opts, status: "generated", source: source || "paste",
    created_at: new Date().toISOString(), updated_at: new Date().toISOString()
  };
  if (FBURL) { try { await fetch(fbRoot() + "/x_mini_drafts/" + id + ".json", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(draft) }); } catch (e) {} }
  return draft;
}
async function xmSave() {
  const ta = document.getElementById("xm-savejson"); let o;
  try { o = JSON.parse((ta.value || "").trim()); } catch (e) { toast("That isn't valid JSON — paste exactly what the AI returned"); return; }
  const draft = await xmStoreDraft(o, "paste");
  if (!draft) { toast("No posts found in that JSON"); return; }
  ta.value = ""; const p = document.getElementById("xm-paste"); if (p) p.hidden = true;
  xmRenderResult(draft); renderXMini(); toast("Saved ✓ — review & post below");
}
/* ---- one-click generation via a user-configured proxy (key stays server-side) ---- */
function xmApiUrl() { return (localStorage.getItem("xm_api_url") || "").trim(); }
function xmApiSave() {
  let v = (document.getElementById("xm-apiurl").value || "").trim().replace(/\/+$/, "");
  if (v && !/^https?:\/\//i.test(v)) v = "https://" + v;   // accept a bare domain
  localStorage.setItem("xm_api_url", v);
  const i = document.getElementById("xm-apiurl"); if (i) i.value = v;
  xmApiStatus();
  toast(v ? "API endpoint saved ⚡ — press Generate (API)" : "API endpoint cleared");
}
function xmApiStatus() {
  const el = document.getElementById("xm-apistat"); if (!el) return;
  const u = xmApiUrl();
  el.textContent = u ? "⚡ Connected: " + u.replace(/^https?:\/\//, "").slice(0, 44) : "Not connected — buttons use free copy-paste";
  el.className = "note" + (u ? " ok" : "");
}
function xmApiToggle() { const b = document.getElementById("xm-apibox"); if (b) { b.hidden = !b.hidden; if (!b.hidden) { const i = document.getElementById("xm-apiurl"); if (i) i.value = xmApiUrl(); xmApiStatus(); } } }
function xmExtractJson(t) { t = String(t || "").trim(); const a = t.indexOf("{"), b = t.lastIndexOf("}"); if (a >= 0 && b > a) t = t.slice(a, b + 1); return JSON.parse(t); }
async function xmApiCall(prompt) {
  const url = xmApiUrl(); if (!url) throw new Error("no endpoint");
  const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt: prompt, model: "claude-sonnet-4-6", max_tokens: 1000, temperature: 0.7 }) });
  const data = await r.json();
  const text = data.text || (data.content && data.content[0] && data.content[0].text) || "";
  if (!text) throw new Error(data.error || "empty response");
  return xmExtractJson(text);
}
async function xmApiGenerate() {
  const url = xmApiUrl();
  if (!url) { toast("First set your free API endpoint (one-time) — opening setup"); const b = document.getElementById("xm-apibox"); if (b) b.hidden = false; xmApiStatus(); return; }
  const btn = document.getElementById("xm-apigen"); if (btn) { btn.disabled = true; btn.textContent = "⚡ Generating…"; }
  const seed = (document.getElementById("xm-seed").value || "").trim();
  try {
    const o = await xmApiCall(window.buildAnthropicWritePrompt({ seed: seed, preset: xmPreset ? xmFindPreset(xmPreset) : null, style: xmStyle }));
    const draft = await xmStoreDraft(o, "api");
    if (!draft) throw new Error("no posts in response");
    xmRenderResult(draft); renderXMini(); toast("⚡ Generated ✓ — review & post");
  } catch (e) { toast("API failed: " + (e.message || e) + " — check your Worker URL / key"); }
  if (btn) { btn.disabled = false; btn.textContent = "⚡ Generate (API)"; }
}
async function xmRefine(instr, draft) {
  if (!xmApiUrl()) { toast("Refine uses the API — set it in ⚙️ API setup"); return; }
  if (!draft || !draft.best_post) { toast("Nothing to refine"); return; }
  toast("⚡ " + instr + "…");
  try {
    const o = await xmApiCall(window.buildAnthropicWritePrompt({ seed: draft.best_post, refine: instr, style: xmStyle }));
    const nd = await xmStoreDraft(o, "api");
    if (!nd) throw new Error("no output");
    xmRenderResult(nd); renderXMini(); toast("Done ✓ — review & post");
  } catch (e) { toast("Refine failed: " + (e.message || e)); }
}
/* ---- "Post on X today": 3 ready X-native lines, rotated daily ---- */
let dailyShuffle = 0;
function dayKey() { try { return Math.floor(new Date().getTime() / 86400000); } catch (e) { return 0; } }
function pickDaily() {
  const I = window.XMINI_IDEAS || {}, cats = Object.keys(I).sort();
  if (!cats.length) return [];
  const base = dayKey() + dailyShuffle * 5;
  const mod = (n, m) => ((n % m) + m) % m;
  return [0, 3, 6].map(o => { const cat = cats[mod(base + o, cats.length)], arr = I[cat] || []; return arr.length ? { cat: cat, text: arr[mod(base + o, arr.length)] } : null; }).filter(Boolean);
}
function renderDailyX() {
  const el = document.getElementById("dailyx"); if (!el) return;
  const picks = pickDaily();
  el.innerHTML = picks.length ? picks.map(p => {
    const len = p.text.length;
    return '<div class="xrep" data-cat="' + esc(p.cat) + '"><div class="xrstyle">' + xmCatLabel(p.cat) +
      ' · <span class="xrscore' + (len > 280 ? " over" : "") + '">' + len + '/280</span></div>' +
      '<div class="xrtext">' + esc(p.text) + '</div>' +
      '<div class="xractions"><button class="cp" data-dx="copy">📋 Copy</button>' +
      '<button class="cp" data-dx="postx">𝕏 Post on X</button>' +
      '<button class="cp" data-dx="posted">✓ Posted</button>' +
      '<button class="cp" data-dx="improve">✍️ Improve</button></div></div>';
  }).join("") : '<div class="note">Idea bank not loaded.</div>';
  el.querySelectorAll(".xrep").forEach(rep => rep.querySelectorAll("[data-dx]").forEach(b => b.onclick = () => {
    const text = rep.querySelector(".xrtext").textContent, cat = rep.getAttribute("data-cat") || "", act = b.dataset.dx;
    if (act === "copy") navigator.clipboard.writeText(text).then(() => toast("Copied — paste & post ✓"));
    else if (act === "postx") { navigator.clipboard.writeText(text).catch(() => {}); window.open("https://twitter.com/intent/tweet?text=" + encodeURIComponent(text), "_blank", "noopener"); toast("Opening X (prefilled & copied)"); }
    else if (act === "posted") xmPosted("", text, cat);
    else if (act === "improve") { switchTab("xmini"); setTimeout(() => { const s = document.getElementById("xm-seed"); if (s) s.value = text; window.scrollTo({ top: 0, behavior: "smooth" }); toast("Loaded into X Mini — pick a style & generate"); }, 60); }
  }));
}
async function xmPosted(draftId, text, cat, extra) {
  extra = extra || {};
  if (FBURL) {
    const id = String(Date.now()) + Math.floor((window.performance && performance.now ? performance.now() : 0));
    const now = new Date().toISOString();
    const rec = { id: id, output_text: text, category: cat || "", preset_slug: extra.preset || "", style_profile: extra.style || "",
      char_count: (text || "").length, emoji_used: xrHasEmoji(text), posted_at: now,
      likes: 0, replies: 0, reposts: 0, bookmarks: 0, impressions: 0, profile_clicks: 0, follows: 0,
      performance_score: 0, notes: "", created_at: now, updated_at: now };
    try { await fetch(fbRoot() + "/x_mini_performance/" + id + ".json", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(rec) }); } catch (e) {}
    if (draftId) { try { fetch(fbRoot() + "/x_mini_drafts/" + draftId + ".json", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: "posted", updated_at: now }) }); } catch (e) {} }
  }
  toast("Logged to Performance — add metrics later ✓"); renderXMini();
}
function xmCount(n) { const el = document.getElementById("nc-xm"); if (el) el.textContent = n || ""; }
async function renderXMini() {
  if (!document.getElementById("tab-xmini")) return;
  xmPresetChips(); xmStyleChips(); xmApiStatus();
  const draftsEl = document.getElementById("xm-drafts"), capEl = document.getElementById("xm-captured");
  if (!FBURL) { if (draftsEl) draftsEl.innerHTML = '<div class="empty">Connect cloud sync to save drafts across devices.</div>'; xmCount(); return; }
  let data = {};
  try { data = (await (await fetch(fbRoot() + "/x_mini_drafts.json")).json()) || {}; } catch (e) {}
  const all = Object.entries(data || {}).filter(e => e[1]).map(e => { const o = e[1]; o._k = e[0]; return o; });
  const byNew = (a, b) => String(b.created_at || "").localeCompare(String(a.created_at || ""));
  const captured = all.filter(d => d.status === "captured").sort(byNew);
  const drafts = all.filter(d => d.status === "generated" || d.status === "saved").sort(byNew);
  if (capEl) {
    capEl.innerHTML = captured.length ? '<div class="sec-h" style="margin-top:10px">📥 From the extension — tap to use as your idea</div>' +
      captured.map(d => '<button class="xmidea" data-cap="' + esc(d._k) + '">' + esc((d.seed || "").slice(0, 100)) + '</button>').join("") +
      '<div class="actions" style="margin-left:0"><button class="cp" data-capclr>Clear captured</button></div>' : "";
    capEl.querySelectorAll("[data-cap]").forEach(b => b.onclick = () => {
      const d = captured.find(x => x._k === b.dataset.cap); if (!d) return;
      document.getElementById("xm-seed").value = d.seed || "";
      try { fetch(fbRoot() + "/x_mini_drafts/" + d._k + ".json", { method: "DELETE" }); } catch (e) {}
      toast("Loaded — pick a style & generate"); window.scrollTo({ top: 0, behavior: "smooth" });
    });
    const clr = capEl.querySelector("[data-capclr]");
    if (clr) clr.onclick = () => { captured.forEach(d => { try { fetch(fbRoot() + "/x_mini_drafts/" + d._k + ".json", { method: "DELETE" }); } catch (e) {} }); renderXMini(); };
  }
  if (draftsEl) {
    draftsEl.innerHTML = drafts.length ? drafts.map(d => '<div class="card" data-dk="' + esc(d._k) + '">' +
      '<div class="xrtext">' + esc(d.best_post || "") + '</div>' +
      '<div class="meta"><span class="pill">' + xmCatLabel(d.best_category || "") + '</span><span>' + (d.best_post || "").length + '/280</span></div>' +
      '<div class="actions" style="margin-left:0;margin-top:6px"><button class="cp" data-dr="open">↩ Re-open</button>' +
      '<button class="cp" data-dr="postx">𝕏 Post on X</button><button class="cp" data-dr="posted">✓ Posted</button><button class="cp" data-dr="del">🗑</button></div></div>').join("")
      : '<div class="empty">No drafts yet — generate above.</div>';
    draftsEl.querySelectorAll("[data-dk]").forEach(card => {
      const d = drafts.find(x => x._k === card.dataset.dk);
      card.querySelectorAll("[data-dr]").forEach(b => b.onclick = () => xmDraftAction(b.dataset.dr, d, card));
    });
  }
  xmCount(captured.length + drafts.length);
}
function xmDraftAction(act, d, card) {
  if (!d) return;
  if (act === "open") { xmRenderResult(d); document.getElementById("xm-seed").value = d.seed || ""; window.scrollTo({ top: 0, behavior: "smooth" }); return; }
  if (act === "postx") { navigator.clipboard.writeText(d.best_post || "").catch(() => {}); window.open("https://twitter.com/intent/tweet?text=" + encodeURIComponent(d.best_post || ""), "_blank", "noopener"); toast("Opening X (prefilled & copied)"); return; }
  if (act === "posted") { xmPosted(d._k, d.best_post || "", d.best_category || "", { preset: d.preset, style: d.style_profile }); return; }
  if (act === "del") { try { fetch(fbRoot() + "/x_mini_drafts/" + d._k + ".json", { method: "DELETE" }); } catch (e) {} card.remove(); toast("Removed"); return; }
}
function xmPerfCard(r) {
  return '<div class="card" data-xk="' + esc(r._k) + '">' +
    '<div class="xrtext">' + esc(r.output_text || "") + '</div>' +
    '<div class="meta"><span class="pill">' + xmCatLabel(r.category || "") + '</span>' +
    (r.preset_slug ? '<span>' + esc(xmPresetName(r.preset_slug)) + '</span>' : "") +
    (r.style_profile ? '<span>🎭 ' + esc(r.style_profile) + '</span>' : "") +
    '<span>' + (r.char_count || 0) + ' chars' + (r.emoji_used ? " · emoji" : "") + '</span>' +
    '<span class="src">⭐ score ' + (+r.performance_score || 0) + '</span></div>' +
    '<div class="xpmetrics">' +
    xpNum("👍 Likes", "likes", r.likes) + xpNum("💬 Replies", "replies", r.replies) +
    xpNum("🔁 Reposts", "reposts", r.reposts) + xpNum("🔖 Bookmarks", "bookmarks", r.bookmarks) +
    xpNum("👤 Profile clicks", "profile_clicks", r.profile_clicks) + xpNum("➕ Follows", "follows", r.follows) +
    xpNum("📈 Impressions", "impressions", r.impressions) +
    '<label class="xpf xpnotes">Notes<input type="text" class="xpi" data-f="notes" value="' + esc(r.notes || "") + '"></label>' +
    '<button class="cp" data-xmx>💾 Save metrics</button><button class="cp" data-xmxdel>🗑</button>' +
    '</div></div>';
}
async function xmPerfSave(btn) {
  const card = btn.closest("[data-xk]"); if (!card) return;
  const key = card.getAttribute("data-xk"), m = {};
  card.querySelectorAll(".xpi").forEach(inp => { m[inp.dataset.f] = inp.type === "number" ? (+inp.value || 0) : inp.value; });
  m.performance_score = xmScore(m); m.updated_at = new Date().toISOString();
  try { await fetch(fbRoot() + "/x_mini_performance/" + key + ".json", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(m) }); } catch (e) {}
  toast("Saved · score " + m.performance_score + " ⭐"); renderXmPerf();
}
async function xmPerfDel(btn) {
  const card = btn.closest("[data-xk]"); if (!card) return;
  try { fetch(fbRoot() + "/x_mini_performance/" + card.getAttribute("data-xk") + ".json", { method: "DELETE" }); } catch (e) {}
  card.remove(); toast("Removed");
}
async function renderXmPerf() {
  const el = document.getElementById("xmperf"); if (!el) return;
  if (!FBURL) { el.innerHTML = '<div class="empty">Connect cloud sync to track performance.</div>'; return; }
  el.innerHTML = '<div class="note">Loading…</div>';
  let data = {};
  try { data = (await (await fetch(fbRoot() + "/x_mini_performance.json")).json()) || {}; } catch (e) {}
  const rows = Object.entries(data || {}).filter(e => e[1]).map(e => { const o = e[1]; o._k = e[0]; return o; });
  if (!rows.length) { el.innerHTML = '<div class="empty">Nothing tracked yet. Post a mini, hit “✓ Posted”, then add likes / replies / reposts ~24h later to learn which styles grow @aixahmad.</div>'; return; }
  const avgBy = fn => {
    const g = {};
    rows.forEach(r => { const k = fn(r); if (k == null || k === "") return; (g[k] = g[k] || []).push(+r.performance_score || 0); });
    return Object.entries(g).map(([k, a]) => [k, a.reduce((s, x) => s + x, 0) / a.length, a.length]).sort((x, y) => y[1] - x[1]);
  };
  const blk = (title, pairs, fmt) => '<div class="xpk"><div class="sec-h">' + title + '</div>' +
    (pairs.length ? pairs.map(([k, avg, n]) => '<div class="xprow"><span>' + esc(fmt ? fmt(k) : k) + '</span><b>' + avg.toFixed(1) + '</b><small>' + n + '</small></div>').join("") : '<div class="note">no data yet</div>') + '</div>';
  const scored = rows.filter(r => (+r.performance_score || 0) > 0);
  const cats = avgBy(r => r.category), styles = avgBy(r => r.style_profile), presets = avgBy(r => r.preset_slug);
  const emoji = avgBy(r => r.emoji_used ? "with emoji" : "no emoji");
  const hourLabel = h => { h = +h; const ap = h < 12 ? "am" : "pm"; let hh = h % 12; if (!hh) hh = 12; return hh + ap; };
  const times = avgBy(r => { try { return String(new Date(r.posted_at).getHours()); } catch (e) { return ""; } });
  const top = rows.slice().sort((a, b) => (+b.performance_score || 0) - (+a.performance_score || 0)).slice(0, 20);
  const hist = rows.slice().sort((a, b) => String(b.posted_at || "").localeCompare(String(a.posted_at || "")));
  // suggestions (only once we have a few scored posts)
  const sugg = [];
  if (scored.length >= 3) {
    if (cats[0]) sugg.push("Post more <b>" + xmCatLabel(cats[0][0]) + "</b> — your strongest category (avg " + cats[0][1].toFixed(1) + ").");
    if (styles[0] && styles[0][0]) sugg.push("Best style this week: <b>🎭 " + esc(styles[0][0]) + "</b>.");
    if (presets[0] && presets[0][0]) sugg.push("Best preset: <b>" + esc(xmPresetName(presets[0][0])) + "</b>. " + (presets.length > 1 && presets[presets.length - 1][0] ? "Ease off <b>" + esc(xmPresetName(presets[presets.length - 1][0])) + "</b>." : ""));
    if (emoji.length === 2) sugg.push(emoji[0][0] === "with emoji" ? "Emojis are <b>helping</b> — keep using 1 where natural." : "Emojis aren't helping much — keep them rare.");
    const q = cats.find(c => c[0] === "question"), h = cats.find(c => c[0] === "hot_take");
    if (q && h) sugg.push(q[1] >= h[1] ? "<b>Questions</b> beat hot takes for you — lean into replies." : "<b>Hot takes</b> beat questions for you — be a bit bolder.");
    if (times[0]) sugg.push("Posts around <b>" + hourLabel(times[0][0]) + "</b> do best so far.");
  }
  el.innerHTML =
    (sugg.length ? '<div class="card xsugg"><div class="sec-h">🧭 What to post next</div><ul>' + sugg.map(s => '<li>' + s + '</li>').join("") + '</ul></div>' : '<div class="note">Tip: post a few, hit “✓ Posted”, add the numbers ~24h later — suggestions appear once you have 3+ scored posts.</div>') +
    '<div class="xgrid">' +
    blk("Best category", cats, xmCatLabel) +
    blk("Best style profile", styles) +
    blk("Best preset", presets, xmPresetName) +
    blk("Emoji vs none", emoji) +
    blk("Short vs long", avgBy(r => (+r.char_count || 0) <= 120 ? "short (≤120)" : "long (>120)")) +
    blk("Best posting time", times, hourLabel) +
    '</div>' +
    '<div class="sec-h xptop">🏆 Top ' + Math.min(20, top.length) + ' posts</div>' +
    top.map(r => '<div class="xprow xptopr"><span>' + esc((r.output_text || "").slice(0, 90)) + '</span><b>' + (+r.performance_score || 0) + '</b><small>' + xmCatLabel(r.category || "") + '</small></div>').join("") +
    '<div class="sec-h xptop">📊 All posts — add the numbers</div>' +
    hist.map(xmPerfCard).join("");
  el.querySelectorAll("[data-xmx]").forEach(b => b.onclick = () => xmPerfSave(b));
  el.querySelectorAll("[data-xmxdel]").forEach(b => b.onclick = () => xmPerfDel(b));
}
/* ===================== 💡 Inspire: useful content-idea bank ===================== */
const INSP_CATL = { interactive: "🎯 Interactive", list: "📑 Lists & carousels", update: "🗞 News angles",
  prompts: "⌨️ Prompts", tools: "🧰 Tools", money: "💰 Money", education: "🎓 Explainers", personal: "🌱 Personal" };
function inspUse(seed) {
  switchTab("xmini");
  setTimeout(() => { const s = document.getElementById("xm-seed"); if (s) { s.value = seed; }
    window.scrollTo({ top: 0, behavior: "smooth" }); toast("Loaded into Write — pick a style & generate ✍️"); }, 60);
}
function inspValue(title, source) {
  navigator.clipboard.writeText(window.buildLinkedInPrompt({
    mode: "practical", title: title, source: source || "",
    audience: settings.liAudience || "", note: settings.liNote || "",
  })).then(() => toast("🛠️ Practical prompt copied — for source facts, open the story in LinkedIn draft instead"));
}
function inspNewsAngle(t) {
  const s = t.toLowerCase();
  if (/(launch|release|announc|unveil|introduc|drops|new model|gpt-|gemini|claude|llama|grok)/.test(s))
    return ["🚀 New release", '"' + t + '" — skip the specs: 5 things you can ACTUALLY do with it today, with the simplest steps'];
  if (/(free|scholarship|student|credit|offer|giveaway|discount)/.test(s))
    return ["🎁 Free alert", '"' + t + '" — who can get it and how, step by step, before the deadline'];
  if (/(raise|funding|million|billion|valuation|acqui|invest)/.test(s))
    return ["💰 Money move", '"' + t + '" — what this money move means for normal people and builders (jobs, tools, prices)'];
  if (/(ban|law|rule|regulat|policy|court|sue|lawsuit)/.test(s))
    return ["⚖️ New rule", '"' + t + '" — the new AI rule explained simply: who is affected and what changes'];
  if (/(leak|hack|breach|scandal|fired|drama|accus)/.test(s))
    return ["🔥 Big story", '"' + t + '" — what actually happened, in plain words, and the part everyone is missing'];
  return ["🗞 Explain it", '"' + t + '" — explained so simply your parents would get it, plus what it means for you'];
}
function renderInspire() {
  const q = (document.getElementById("insp-q").value || "").toLowerCase().trim();
  /* --- ideas made from YOUR live news feed (fresh, high-score, not covered) --- */
  const newsEl = document.getElementById("insp-news");
  try {
    const cut = Date.now() - 2 * 86400000;
    const top = ITEMS.filter(it => it.p !== 9 && !doneSet.has(it.u) && new Date(it.d || it.f).getTime() > cut)
      .sort((a, b) => b.sc - a.sc).slice(0, 6);
    newsEl.innerHTML = top.length ? '<div class="sec-h" style="margin-top:10px">🗞 From today\'s news — turned into useful angles</div>' +
      top.map((it, i) => {
        const [tag, angle] = inspNewsAngle(it.t);
        return '<div class="card"><div class="meta"><span class="pill">' + tag + '</span><span class="src">score ' + it.sc + '</span></div>' +
          '<div class="xrtext">' + esc(angle) + '</div>' +
          '<div class="actions" style="margin-left:0;margin-top:6px">' +
          '<button class="cp" data-iw="' + esc(angle) + '">✍️ Write</button>' +
          '<button class="cp" data-iv="' + esc(it.t) + '" data-iu="' + esc(it.u) + '">💎 Value pack</button>' +
          '<button class="cp" data-inr="' + i + '">📰 Newsroom</button>' +
          '<a class="cp" href="' + esc(it.u) + '" target="_blank" rel="noopener">↗ Story</a>' +
          '<button class="cp" data-imd="' + i + '">✓ Done</button></div></div>';
      }).join("") : "";
    newsEl.querySelectorAll("[data-inr]").forEach(b => b.onclick = () => openNewsroom(top[+b.dataset.inr]));
    newsEl.querySelectorAll("[data-imd]").forEach(b => b.onclick = () => { markStoryDone(top[+b.dataset.imd]); toast("Done ✓ — removed (synced everywhere)"); renderInspire(); });
  } catch (e) { newsEl.innerHTML = ""; }
  /* --- curated idea bank --- */
  const listEl = document.getElementById("insp-list");
  const ideas = (window.INSPIRE_IDEAS || []).filter(i => !q || (i[0] + " " + i[1] + " " + i[2] + " " + i[3]).toLowerCase().includes(q));
  const byCat = {};
  ideas.forEach(i => (byCat[i[0]] = byCat[i[0]] || []).push(i));
  listEl.innerHTML = Object.keys(INSP_CATL).filter(c => byCat[c]).map(c =>
    '<div class="sec-h" style="margin-top:12px">' + INSP_CATL[c] + '</div>' +
    byCat[c].map(i =>
      '<div class="card"><b>' + esc(i[1]) + '</b>' +
      '<div class="xreason">' + esc(i[2]) + '</div>' +
      '<div class="xrtext" style="margin-top:5px">' + esc(i[3]) + '</div>' +
      '<div class="actions" style="margin-left:0;margin-top:6px">' +
      '<button class="cp" data-iw="' + esc(i[3]) + '">✍️ Write</button>' +
      '<button class="cp" data-iv="' + esc(i[1] + " — " + i[3]) + '" data-iu="">💎 Value pack</button>' +
      '<button class="cp" data-inrt="' + esc(i[1] + " — " + i[3]) + '">📰 Newsroom</button></div></div>').join("")
  ).join("") || '<div class="empty">No ideas match that search.</div>';
  listEl.querySelectorAll("[data-inrt]").forEach(b => b.onclick = () => openNewsroom({ t: b.getAttribute("data-inrt"), u: "" }));
  document.querySelectorAll("#tab-inspire [data-iw]").forEach(b => b.onclick = () => inspUse(b.getAttribute("data-iw")));
  document.querySelectorAll("#tab-inspire [data-iv]").forEach(b => b.onclick = () => inspValue(b.getAttribute("data-iv"), b.getAttribute("data-iu")));
}
document.getElementById("insp-q").addEventListener("input", () => renderInspire());

/* ===================== ⭐ Me: Ahmad presents the news ===================== */
function meCopyPoster(headline, story) {
  navigator.clipboard.writeText(window.buildMePosterPrompt({ headline: headline, story: story }))
    .catch(() => {});
  window.open("https://chatgpt.com/", "_blank", "noopener");
  toast("🎨 Me-poster prompt copied — paste in your photo chat & attach your pic");
}
function mePosterOwn() {
  const t = (document.getElementById("me-own").value || "").trim();
  if (!t) { toast("Type your announcement first"); return; }
  meCopyPoster(t, "Ahmad's own announcement: " + t);
}
function meCaptionOwn() {
  const t = (document.getElementById("me-own").value || "").trim();
  if (!t) { toast("Type your announcement first"); return; }
  inspUse("Announce this in my own voice (build-in-public, human, simple): " + t);
}
function renderMeTab() {
  const el = document.getElementById("me-news"); if (!el) return;
  try {
    const cut = Date.now() - 2 * 86400000;
    const top = ITEMS.filter(it => it.p !== 9 && !doneSet.has(it.u) && new Date(it.d || it.f).getTime() > cut)
      .sort((a, b) => b.sc - a.sc).slice(0, 10);
    el.innerHTML = top.length ? '<div class="sec-h" style="margin-top:10px">🗞 Today\'s news — with YOU presenting</div>' +
      top.map((it, i) => '<div class="card"><div class="meta"><span class="src">score ' + it.sc + '</span></div>' +
        '<div class="xrtext">' + esc(it.t) + '</div>' +
        '<div class="actions" style="margin-left:0;margin-top:6px">' +
        '<button class="cp" data-mp="' + i + '">🎨 Poster with me</button>' +
        '<button class="cp" data-mc="' + i + '">✍️ Caption</button>' +
        '<button class="cp" data-mn="' + i + '">📰 Newsroom</button>' +
        '<a class="cp" href="' + esc(it.u) + '" target="_blank" rel="noopener">↗ Story</a>' +
        '<button class="cp" data-md="' + i + '">✓ Done</button></div></div>').join("")
      : '<div class="empty">No fresh stories right now — check back after the next fetch.</div>';
    el.querySelectorAll("[data-mp]").forEach(b => b.onclick = () => { const it = top[+b.dataset.mp]; meCopyPoster(it.t, it.t); });
    el.querySelectorAll("[data-mc]").forEach(b => b.onclick = () => { const it = top[+b.dataset.mc]; inspUse('Announce this news in my own voice, like I\'m telling my followers (simple, human, my take included): "' + it.t + '"'); });
    el.querySelectorAll("[data-mn]").forEach(b => b.onclick = () => openNewsroom(top[+b.dataset.mn]));
    el.querySelectorAll("[data-md]").forEach(b => b.onclick = () => { markStoryDone(top[+b.dataset.md]); toast("Done ✓ — removed (synced everywhere)"); renderMeTab(); });
  } catch (e) { el.innerHTML = ""; }
}

function bar() {
  const el = document.getElementById("pillars");
  el.innerHTML = "";
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

/* ---------------- Pulse (usage / search / problems signal) ---------------- */
let PULSE = null, pulseSeq = 0, pulseById = {};
let pulseFilter = { platform: "", pillar: "", format: "", local: false };
const PLAT_LABEL = { google:"Google", youtube:"YouTube", reddit:"Reddit", hackernews:"HN",
  instagram_inferred:"Instagram", facebook_inferred:"Facebook", linkedin_inferred:"LinkedIn" };

async function renderPulse() {
  if (!PULSE) {
    try { const r = await fetch("pulse.json?v=" + Date.now()); PULSE = r.ok ? await r.json() : { error: 1 }; }
    catch (e) { PULSE = { error: 1 }; }
  }
  drawPulse();
}
function pmFmt(s) { return (s || "").replace(/_/g, " "); }
function isLLM() { return !!(PULSE && PULSE.meta && PULSE.meta.mode === "llm"); }

function buildPulseFilters() {
  const plats = new Set(), pillars = new Set(), formats = new Set();
  (PULSE.trends || []).forEach(t => { (t.platforms || []).forEach(p => plats.add(p));
    if (t.pillar) pillars.add(t.pillar); if (t.best_format) formats.add(t.best_format); });
  const chip = (label, active, on) =>
    '<span class="chip' + (active ? ' active' : '') + '" onclick="' + on + '">' + label + '</span>';
  let h = chip("All", !pulseFilter.platform && !pulseFilter.pillar && !pulseFilter.format && !pulseFilter.local, "pulseClear()");
  [...plats].forEach(p => { const lbl = (p.endsWith("_inferred") ? "~" : "") + (PLAT_LABEL[p] || p);
    h += chip(lbl, pulseFilter.platform === p, "pulseSet('platform','" + p + "')"); });
  [...pillars].forEach(p => h += chip(pmFmt(p), pulseFilter.pillar === p, "pulseSet('pillar','" + p + "')"));
  [...formats].forEach(p => h += chip(pmFmt(p), pulseFilter.format === p, "pulseSet('format','" + p + "')"));
  h += chip("📍 Local", pulseFilter.local, "pulseToggleLocal()");
  document.getElementById("pulse-fil").innerHTML = h;
}
function pulseClear() { pulseFilter = { platform: "", pillar: "", format: "", local: false }; drawPulse(); }
function pulseSet(k, v) { pulseFilter[k] = pulseFilter[k] === v ? "" : v; drawPulse(); }
function pulseToggleLocal() { pulseFilter.local = !pulseFilter.local; drawPulse(); }
function pulsePass(t) {
  if (pulseFilter.platform && !(t.platforms || []).includes(pulseFilter.platform)) return false;
  if (pulseFilter.pillar && t.pillar !== pulseFilter.pillar) return false;
  if (pulseFilter.format && t.best_format !== pulseFilter.format) return false;
  if (pulseFilter.local && (t.local_relevance || 0) < 4) return false;
  return true;
}

function drawPulse() {
  const wrap = document.getElementById("pulse-body");
  const meta = document.getElementById("pulse-meta");
  pulseSeq = 0; pulseById = {};
  if (!PULSE || PULSE.error || (!(PULSE.trends || []).length && !(PULSE.pain_points || []).length)) {
    meta.textContent = ""; document.getElementById("pulse-fil").innerHTML = "";
    wrap.innerHTML = '<p class="note">No Pulse data yet — it builds every 6 hours once the Pulse action runs '
      + '(or run <code>python generate_pulse.py</code> locally).</p>';
    return;
  }
  const m = PULSE.meta || {};
  meta.innerHTML = (m.mode === "raw"
      ? '<span class="pbadge">⚙️ Raw signals · LLM off</span> '
      : '<span class="pbadge" style="color:var(--gold);border-color:var(--gold)">✨ LLM enriched</span> ')
    + "Updated " + (PULSE.generated_at ? ago(PULSE.generated_at) : "")
    + " · sources: " + ((m.sources_used || []).join(", ") || "none");
  buildPulseFilters();
  const trends = (PULSE.trends || []).filter(pulsePass);
  const tools = (PULSE.rising_tools || []).filter(pulsePass);
  const pains = PULSE.pain_points || [];
  let h = "";
  if (PULSE.tool_of_week_candidate)
    h += '<div class="pulse-tow">⭐ <b>Tool of the week:</b> ' + esc(PULSE.tool_of_week_candidate) + '</div>';
  h += '<div class="pulse-h">🔥 Hot Right Now</div>' + (trends.map(t => pulseCard(t, false)).join("") || pulseEmpty());
  h += '<div class="pulse-h">📈 Rising Tools</div>' + (tools.map(t => pulseCard(t, true)).join("") || pulseEmpty());
  h += '<div class="pulse-h">🛠️ Problems People Face <span style="font-weight:400;color:var(--faint)">— content goldmine</span></div>'
     + (pains.map(painCard).join("") || pulseEmpty());
  wrap.innerHTML = h;
}
function pulseEmpty() { return '<p class="note" style="opacity:.7">Nothing here with the current filters.</p>'; }

function pulseCard(t, isTool) {
  const id = "p" + (pulseSeq++); pulseById[id] = t;
  const mom = t.momentum || "hot";
  let h = '<div class="pcard"><h4>' + esc(t.name) + '</h4>';
  h += '<div class="row"><span class="pmom ' + mom + '">' + mom + '</span>';
  if (t.category) h += '<span class="pbadge">' + pmFmt(t.category) + '</span>';
  (t.platforms || []).forEach(p => { const inf = p.endsWith("_inferred");
    h += '<span class="pbadge' + (inf ? ' inf' : '') + '">' + (inf ? "~ " : "") + (PLAT_LABEL[p] || p) + (inf ? " (inferred)" : "") + '</span>'; });
  if ((t.local_relevance || 0) >= 4) h += '<span class="pbadge" style="color:var(--green)">📍 Local ' + t.local_relevance + '/10</span>';
  h += '</div>';
  if (isLLM() && t.what_it_is) h += '<div class="pangle">' + esc(t.what_it_is) + '</div>';
  if (isLLM() && t.audience_angle) h += '<div class="pangle">🎯 <b>For your audience:</b> ' + esc(t.audience_angle) + '</div>';
  if (isLLM() && t.linkedin_angle) h += '<div class="pangle">💼 <b>LinkedIn:</b> ' + esc(t.linkedin_angle) + '</div>';
  h += '<div class="row"><span class="pbadge">' + pmFmt(t.pillar || "") + '</span><span class="pbadge">' + pmFmt(t.best_format || "") + '</span>';
  if (t.monetization && t.monetization.affiliate_likely) h += '<span class="pbadge" style="color:var(--gold)">💰 affiliate</span>';
  h += '</div>';
  if (isLLM() && (t.content_ideas || []).length) {
    h += '<div style="margin:7px 0 2px;font-size:12.5px;color:var(--dim)">💡 Content ideas:</div>';
    t.content_ideas.forEach(i => h += '<div class="pidea">• ' + esc(i) + '</div>');
  }
  if ((t.sources || []).length) {
    h += '<div class="row" style="margin-top:8px">';
    t.sources.slice(0, 4).forEach(s => h += '<a class="plink" href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.platform || "source") + ' ↗</a>');
    h += '</div>';
  }
  h += '<div class="pact">'
    + '<button class="ghost" onclick="pulseNewsroom(\'' + id + '\')">📰 Newsroom</button>'
    + '<button class="ghost" onclick="pulseCopyPrompt(\'' + id + '\')">📋 Script prompt</button>'
    + '<button class="ghost" onclick="pulseToX(\'' + id + '\')">𝕏 X post</button>'
    + '</div></div>';
  return h;
}
function painCard(p) {
  const id = "p" + (pulseSeq++);
  pulseById[id] = { name: p.problem, u: (p.sources && p.sources[0] && p.sources[0].url) || "",
    _pain: true, content_opportunity: p.content_opportunity, sources: p.sources };
  let h = '<div class="pcard"><h4>' + esc(p.problem) + '</h4>';
  h += '<div class="row"><span class="pbadge">' + esc(p.who_affected || "") + '</span>'
     + '<span class="pbadge" style="color:var(--orange)">🔥 ' + (p.signal_strength || 0) + '/10</span></div>';
  if (isLLM() && p.content_opportunity) h += '<div class="pangle">🎯 <b>Content angle:</b> ' + esc(p.content_opportunity) + '</div>';
  if ((p.sources || []).length) {
    h += '<div class="row" style="margin-top:6px">';
    p.sources.slice(0, 4).forEach(s => h += '<a class="plink" href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.platform || "source") + ' ↗</a>');
    h += '</div>';
  }
  h += '<div class="pact">'
    + '<button class="ghost" onclick="pulseCopyPrompt(\'' + id + '\')">📋 Script prompt</button>'
    + '</div></div>';
  return h;
}
function pulseTitle(t) { return t.name || t.problem || ""; }
function pulseUrl(t) { return t.u || (t.sources && t.sources[0] && t.sources[0].url) || ""; }
function pulseCopyPrompt(id) {
  const t = pulseById[id]; if (!t) return;
  const isPain = !!t._pain, ctx = pulseTitle(t), src = pulseUrl(t);
  let p = 'You are a scriptwriter for "AI x Ahmad" (@aixahmad), a global AI-news channel.\n'
    + 'Write in clear, simple English for a worldwide audience.\n\n';
  if (isPain) {
    p += 'TOPIC (a problem people are facing): ' + ctx + '\n'
      + (t.content_opportunity ? ('ANGLE: ' + t.content_opportunity + '\n') : '')
      + '\nMake a helpful video that explains the problem simply and gives a clear workaround/solution.\n';
  } else {
    p += 'TOPIC (a rising AI trend): ' + ctx + '\n'
      + (t.audience_angle ? ('WHY IT MATTERS: ' + t.audience_angle + '\n') : '')
      + (t.what_it_is ? ('WHAT IT IS: ' + t.what_it_is + '\n') : '')
      + '\nFormat: ' + pmFmt(t.best_format || 'short') + '. Pillar: ' + pmFmt(t.pillar || 'discovery') + '.\n';
  }
  if (src) p += 'SOURCE: ' + src + '\n';
  p += '\nWrite:\n1) A scroll-stopping hook (1 line)\n2) A tight spoken script (45-90 sec) in clear English\n'
    + '3) A strong CTA to follow @aixahmad\n4) 5 viral title options\n'
    + 'Base everything ONLY on the topic above — do not invent fake numbers or features.';
  navigator.clipboard.writeText(p).then(() => toast("Script prompt copied — paste in Claude 🤖"));
}
function pulseToX(id) {
  const t = pulseById[id]; if (!t) return;
  openXModal({ t: pulseTitle(t), u: pulseUrl(t) });
}
function pulseNewsroom(id) {
  const t = pulseById[id]; if (!t) return;
  openNewsroom({ t: pulseTitle(t), u: pulseUrl(t), p: 0 });
}

/* ---- X auto-post (owner only; calls the Cloudflare Worker) ---- */
let xUrl = localStorage.getItem("x_url") || "";
let xToken = localStorage.getItem("x_token") || "";
let xStory = null;
function xConfigured() { return xUrl && xToken; }
function xSetup() {
  const u = (prompt("Cloudflare Worker URL (https://aix-x...workers.dev):", xUrl) || "").trim();
  if (!u) return false;
  const t = (prompt("APP_TOKEN (the password you set in the Worker):", xToken) || "").trim();
  if (!t) return false;
  xUrl = u.replace(/\/+$/, ""); xToken = t;
  localStorage.setItem("x_url", xUrl); localStorage.setItem("x_token", xToken);
  toast("X pipeline connected ✓");
  return true;
}
function xQuotaGet() {
  const month = new Date().toISOString().slice(0, 7);
  let q = {};
  try { q = JSON.parse(localStorage.getItem("x_quota") || "{}"); } catch (e) {}
  if (q.month !== month) q = { month: month, count: 0 };
  return q;
}
function xQuotaAdd(n) {
  const q = xQuotaGet();
  q.count += n;
  localStorage.setItem("x_quota", JSON.stringify(q));
}
function xShowQuota() {
  const q = xQuotaGet();
  document.getElementById("x-quota").textContent = q.count + " posts this month";
}
async function xCall(payload) {
  const r = await fetch(xUrl, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(Object.assign({ token: xToken }, payload)) });
  const d = await r.json();
  if (!r.ok || d.error) throw new Error(d.error || ("HTTP " + r.status));
  return d;
}
function tweetsToText(tweets) { return tweets.join("\n\n"); }
function textToTweets(t) { return t.split(/\n\s*\n/).map(s => s.trim()).filter(Boolean); }

function xFillSelect(id, group, def) {
  const sel = document.getElementById(id);
  if (!sel || !window.XLIB) return;
  sel.innerHTML = Object.entries(window.XLIB[group])
    .map(([k, v]) => '<option value="' + k + '"' + (k === def ? " selected" : "") + ">" + esc(v.name) + "</option>").join("");
}
function openXModal(story) {
  xStory = story;
  // recommended default combo: single post + breaking-news wire + breaking hook
  xFillSelect("x-format", "formats", "single");
  xFillSelect("x-voice", "voices", "breaking");
  xFillSelect("x-hook", "hooks", "breaking");
  document.getElementById("x-story").textContent = "📰 " + story.t;
  document.getElementById("x-out").hidden = true;
  document.getElementById("x-tweets").value = "";
  document.getElementById("x-result").textContent = "";
  document.getElementById("x-auto").checked = false;
  xShowQuota();
  document.getElementById("xmodal").hidden = false;
}
function closeXModal() { document.getElementById("xmodal").hidden = true; xStory = null; }
function xPayload() {
  const prompt = window.buildXPrompt({
    title: xStory.t, url: xStory.u, summary: "",
    format: document.getElementById("x-format").value,
    voice: document.getElementById("x-voice").value,
    hook: document.getElementById("x-hook").value,
    lang: document.getElementById("x-lang").value });
  return { prompt: prompt, title: xStory.t, url: xStory.u };
}
document.getElementById("x-copyprompt").onclick = () => {
  if (!xStory) return;
  const p = xPayload().prompt;
  navigator.clipboard.writeText(p).then(() => {
    document.getElementById("x-out").hidden = false;
    document.getElementById("x-tweets").value = "";
    document.getElementById("x-result").textContent = "Prompt copied — paste in Claude, then paste the thread back here";
    toast("Prompt copied for Claude 🤖");
  });
};
document.getElementById("x-write").onclick = async () => {
  if (!xStory) return;
  if (!xConfigured() && !xSetup()) return;   // auto-write needs the Worker; the Claude button doesn't
  const auto = document.getElementById("x-auto").checked;
  const btn = document.getElementById("x-write");
  btn.disabled = true; btn.textContent = auto ? "Writing & posting…" : "Writing…";
  try {
    if (auto) {
      const d = await xCall(Object.assign({ action: "writepost" }, xPayload()));
      xQuotaAdd((d.tweets || []).length || 1);
      toast("Posted to X 🚀");
      document.getElementById("x-out").hidden = false;
      document.getElementById("x-tweets").value = tweetsToText(d.tweets || []);
      showXResult(d.url);
      xShowQuota();
    } else {
      const d = await xCall(Object.assign({ action: "write" }, xPayload()));
      document.getElementById("x-out").hidden = false;
      document.getElementById("x-tweets").value = tweetsToText(d.tweets || []);
      document.getElementById("x-result").textContent = "Review, then Approve & Post";
    }
  } catch (e) { toast("X error: " + e.message); }
  btn.disabled = false; btn.textContent = "✍️ Write";
};
document.getElementById("x-rewrite").onclick = () => document.getElementById("x-write").click();
document.getElementById("x-copy").onclick = () => {
  const txt = document.getElementById("x-tweets").value.trim();
  if (!txt) { toast("Nothing to copy"); return; }
  navigator.clipboard.writeText(txt).then(() => {
    document.getElementById("x-result").textContent = "✓ Copied — paste into X";
    toast("Thread copied — paste it into X 📋");
  });
};
// One-tap assisted post: open X with tweet 1 pre-filled (official share intent,
// zero ban risk). For a thread, copy the remaining tweets so they're ready to
// paste as replies. Uses whatever X account is logged in on this browser.
document.getElementById("x-tweet").onclick = () => {
  const tweets = textToTweets(document.getElementById("x-tweets").value);
  if (!tweets.length) { toast("Nothing to post"); return; }
  const rest = tweets.slice(1).join("\n\n");
  if (rest) { navigator.clipboard.writeText(rest).catch(() => {}); }
  window.open("https://x.com/intent/tweet?text=" + encodeURIComponent(tweets[0]), "_blank", "noopener");
  document.getElementById("x-result").textContent = tweets.length > 1
    ? "Tweet 1 opened in X · replies copied — paste them under it"
    : "Opened in X — just tap Post";
  toast("X opened with your post ready 🚀");
};
document.getElementById("x-post").onclick = async () => {
  const tweets = textToTweets(document.getElementById("x-tweets").value);
  if (!tweets.length) { toast("Nothing to post"); return; }
  const btn = document.getElementById("x-post");
  btn.disabled = true; btn.textContent = "Posting…";
  try {
    const d = await xCall({ action: "post", tweets: tweets });
    xQuotaAdd(tweets.length);
    toast("Posted to X 🚀");
    showXResult(d.url);
    xShowQuota();
  } catch (e) { toast("X error: " + e.message); }
  btn.disabled = false; btn.textContent = "🚀 Approve & Post";
};
function showXResult(url) {
  const el = document.getElementById("x-result");
  el.innerHTML = url ? '✅ <a href="' + esc(url) + '" target="_blank">View on X</a>' : "Posted ✅";
}

/* ---- Publish to the public website (owner only; writes to Firebase /published) ---- */
let pubStory = null, pubImageData = "", lastPubArt = null;
const PUBLIC_SITE = "https://ahmad19sep.github.io/ai-news-updater";
function pubBase() { return FBURL ? FBURL.replace(/\/+$/, "") + "/published" : ""; }
/* Resize an uploaded picture in-browser to a small JPEG data URL (no image host needed). */
document.getElementById("pub-file").onchange = (e) => {
  const f = e.target.files[0]; if (!f) return;
  const img = new Image();
  img.onload = () => {
    const max = 900; let w = img.width, h = img.height;
    if (w > max) { h = Math.round(h * max / w); w = max; }
    const c = document.createElement("canvas"); c.width = w; c.height = h;
    c.getContext("2d").drawImage(img, 0, 0, w, h);
    pubImageData = c.toDataURL("image/jpeg", 0.65);
    const pv = document.getElementById("pub-preview"); pv.src = pubImageData; pv.style.display = "";
    document.getElementById("pub-imgnote").textContent = "✓ uploaded (" + Math.round(pubImageData.length / 1365) + " KB)";
  };
  img.src = URL.createObjectURL(f);
};
/* 🖼️ Make poster — a branded 16:9 news poster from the headline (over the
   uploaded photo if there is one, else a blue AI Radar gradient). $0, instant. */
function _wrapLines(x, text, maxW) {
  const words = text.split(/\s+/); const lines = []; let line = "";
  for (const w of words) { const t = line ? line + " " + w : w;
    if (x.measureText(t).width > maxW && line) { lines.push(line); line = w; } else line = t; }
  if (line) lines.push(line); return lines;
}
function _gradBg(x, W, H) {
  const g = x.createLinearGradient(0, 0, W, H);
  g.addColorStop(0, "#0a1330"); g.addColorStop(.5, "#16275a"); g.addColorStop(1, "#1e3a8a");
  x.fillStyle = g; x.fillRect(0, 0, W, H);
  const rg = x.createRadialGradient(W * .82, H * .18, 0, W * .82, H * .18, 460);
  rg.addColorStop(0, "rgba(56,189,248,.45)"); rg.addColorStop(1, "rgba(56,189,248,0)");
  x.fillStyle = rg; x.fillRect(0, 0, W, H);
}
function makePoster() {
  const title = document.getElementById("pub-title").value.trim();
  if (!title) { toast("Add a headline first"); return; }
  const cat = document.getElementById("pub-cat").value || "AI NEWS";
  const W = 1200, H = 675, c = document.createElement("canvas"); c.width = W; c.height = H;
  const x = c.getContext("2d");
  const finish = () => {
    x.textBaseline = "alphabetic";
    x.font = "700 26px Inter, Arial, sans-serif"; x.fillStyle = "#38bdf8";
    x.fillText(cat.toUpperCase(), 60, 92);
    x.font = "800 62px Inter, Arial, sans-serif"; x.fillStyle = "#ffffff";
    const lines = _wrapLines(x, title, W - 120).slice(0, 4);
    const lh = 74; let y = H - 150 - (lines.length - 1) * lh;
    lines.forEach(l => { x.fillText(l, 60, y); y += lh; });
    x.font = "700 30px Inter, Arial, sans-serif"; x.fillStyle = "#e8edfb"; x.fillText("📡 AI Radar", 60, H - 58);
    x.font = "500 22px Inter, Arial, sans-serif"; x.fillStyle = "#9fb0d6"; x.fillText("@aixahmad", 60, H - 26);
    pubImageData = c.toDataURL("image/jpeg", 0.85);
    const pv = document.getElementById("pub-preview"); pv.src = pubImageData; pv.style.display = "";
    document.getElementById("pub-imgnote").textContent = "🖼️ poster ready";
    toast("Poster made — set as the article image 🖼️");
  };
  if (pubImageData && pubImageData.indexOf("data:image") === 0) {
    const im = new Image();
    im.onload = () => {
      const r = Math.max(W / im.width, H / im.height), w = im.width * r, h = im.height * r;
      x.drawImage(im, (W - w) / 2, (H - h) / 2, w, h);
      const g = x.createLinearGradient(0, 0, 0, H);
      g.addColorStop(0, "rgba(7,11,24,.30)"); g.addColorStop(.55, "rgba(7,11,24,.55)"); g.addColorStop(1, "rgba(7,11,24,.94)");
      x.fillStyle = g; x.fillRect(0, 0, W, H); finish();
    };
    im.onerror = () => { _gradBg(x, W, H); finish(); };
    im.src = pubImageData;
  } else { _gradBg(x, W, H); finish(); }
}
document.getElementById("pub-poster").onclick = makePoster;
function openPublishModal(story) {
  pubStory = story;
  document.getElementById("pub-title").value = story.t || "";
  document.getElementById("pub-url").value = story.u || "";
  document.getElementById("pub-img").value = "";
  document.getElementById("pub-body").value = "";
  document.getElementById("pub-result").textContent = "";
  pubImageData = ""; lastPubArt = null;
  document.getElementById("pub-file").value = "";
  document.getElementById("pub-preview").style.display = "none";
  document.getElementById("pub-imgnote").textContent = "";
  document.getElementById("pub-cat").innerHTML = Object.entries(PILLARS)
    .map(([k, v]) => "<option" + (+k === story.p ? " selected" : "") + ">" + v + "</option>").join("");
  document.getElementById("pubmodal").hidden = false;
  loadPubList();
}
function closePub() { document.getElementById("pubmodal").hidden = true; pubStory = null; }
document.getElementById("pubmodal").addEventListener("click", e => { if (e.target.id === "pubmodal") closePub(); });
document.getElementById("pub-draft").onclick = () => {
  const t = document.getElementById("pub-title").value.trim();
  const u = document.getElementById("pub-url").value.trim();
  const p = 'You are a senior journalist writing for a top news publication (think The New York Times, Reuters, or The Verge). Write a polished, professional news article in clear, simple English for a global audience about:\n"' + t + '"\n' +
    (u ? "Source: " + u + "\nFIRST open and read the source carefully before writing.\n" : "") +
    "\nWrite the ARTICLE BODY only (400-600 words) — do NOT repeat the headline:\n" +
    "- Open with a strong lede sentence that captures the single most important point.\n" +
    "- Use inverted-pyramid structure: key facts first, then context, background, and what it means.\n" +
    "- Short paragraphs of 2-3 sentences, each separated by a blank line.\n" +
    "- Authoritative, neutral, engaging tone — no hype, no clickbait.\n" +
    "- Include concrete specifics from the source (who, what, when, numbers, quotes) and attribute them (\"according to ...\").\n" +
    "- End with a forward-looking closing line.\n" +
    "Rules: use ONLY facts from the source — never invent quotes, numbers, names, or events. Plain text only: no markdown, no bullet characters, no headings.\n\n" +
    "THEN create a matching POSTER IMAGE for this story. Follow these art-director rules exactly:\n" +
    (window.HUMAN_IMAGE || "") + "\n" +
    'HEADLINE TO RENDER on the poster, word for word: "' + t + '"\n' +
    "- If you can generate images, generate the poster now following the chosen format.\n" +
    "- If you cannot generate images, instead end your reply with a line starting exactly \"IMAGE PROMPT:\" followed by the full detailed prompt for the chosen format.\n" +
    "Keep the article and the image clearly separated, so I can copy the article text on its own.";
  navigator.clipboard.writeText(p).then(() => toast("Article + image prompt copied — paste into ChatGPT/Gemini (makes both); paste the article into the body, use/upload the image 🤖🎨"));
};
/* When a story is published, tick it AND every related/duplicate copy as done,
   so the same news (from other sources) can't be confused with a fresh story.
   Matches on shared URL, shared related-link, or identical normalised headline. */
function markStoryDone(story) {
  if (!story) return 0;
  const norm = s => (s || "").toLowerCase().replace(/[^a-z0-9 ]+/g, "").replace(/\s+/g, " ").trim();
  const keys = new Set([story.u, ...(story.l || [])].filter(Boolean));
  const t0 = norm(story.t || story.title);
  const hit = it => keys.has(it.u) || (it.l || []).some(u => keys.has(u)) || (t0 && norm(it.t) === t0);
  // pass 1: pull every matching item's links into the key set (transitive)
  ITEMS.forEach(it => { if (hit(it)) { if (it.u) keys.add(it.u); (it.l || []).forEach(u => keys.add(u)); } });
  // pass 2: tick every item that now overlaps the expanded key set
  let n = 0;
  ITEMS.forEach(it => { if (hit(it) && it.u && !doneSet.has(it.u)) { doneSet.add(it.u); n++; } });
  localStorage.setItem("done", JSON.stringify([...doneSet]));
  // remember this story so future duplicates (any device) auto-tick too
  const sig = { u: story.u || "", t: story.t || story.title || "", l: (story.l || []) };
  POSTED.push(sig);
  pushPosted(sig); pushDone();
  try { render(); } catch (e) {}
  try { renderPopular(); } catch (e) {}
  try { renderHome(); } catch (e) {}
  try { if (!document.getElementById("tab-me").hidden) renderMeTab(); } catch (e) {}
  try { if (!document.getElementById("tab-inspire").hidden) renderInspire(); } catch (e) {}
  return n;
}
document.getElementById("pub-go").onclick = async () => {
  if (!FBURL) { toast("Firebase not connected"); return; }
  const title = document.getElementById("pub-title").value.trim();
  const body = document.getElementById("pub-body").value.trim();
  if (!title || !body) { toast("Need a headline and article body"); return; }
  const id = String(Date.now());
  const art = { id, title, body, url: document.getElementById("pub-url").value.trim(),
    image: pubImageData || document.getElementById("pub-img").value.trim(),
    cat: document.getElementById("pub-cat").value, ts: Date.now() };
  try {
    const r = await fetch(pubBase() + "/" + id + ".json", {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(art) });
    if (!r.ok) { toast("Publish blocked — add a /published rule in Firebase"); return; }
    lastPubArt = art;
    toast("Published to your website 🌐");
    document.getElementById("pub-result").innerHTML = '✅ Live — <a href="index.html" target="_blank">view</a> · now tap 𝕏 to tweet it';
    loadPubList();
    const nd = markStoryDone(pubStory);
    if (nd > 1) toast("✓ Ticked this + " + (nd - 1) + " related stor" + (nd - 1 === 1 ? "y" : "ies"));
  } catch (e) { toast("Publish failed: " + e.message); }
};
/* Share the published article to X / WhatsApp / Facebook, ending with a link to
   the full story on your site (each platform's own one-tap share — no ban risk). */
function pubLink(art) { return PUBLIC_SITE + "/#a=" + art.id; }
function pubBlurb(art, max) {
  const first = (art.body || "").split(/\n\s*\n/)[0].replace(/\s+/g, " ").trim();
  return first ? first.slice(0, max) : "";
}
function needPub() {
  if (!lastPubArt) { toast("Publish the article first, then share it"); return null; }
  return lastPubArt;
}
document.getElementById("pub-tweet").onclick = () => {
  const art = needPub(); if (!art) return;
  let text = art.title + "\n\n" + pubBlurb(art, 120) + "\n\n🔗 Full story: " + pubLink(art);
  if (text.length > 275) text = art.title + "\n\n🔗 Full story: " + pubLink(art);
  window.open("https://x.com/intent/tweet?text=" + encodeURIComponent(text), "_blank", "noopener");
  toast("X opened with your article link — tap Post 🚀");
};
document.getElementById("pub-li").onclick = () => {
  const art = needPub(); if (!art) return;
  window.open("https://www.linkedin.com/sharing/share-offsite/?url=" + encodeURIComponent(pubLink(art)), "_blank", "noopener");
  toast("LinkedIn opened with your article link — add your own words before posting");
};

/* ---- LinkedIn draft: one selected story -> one useful post.
   Two modes of the same writer (insight / practical), same [[MARKER]] flow as before.
   Nothing here publishes, and nothing here marks a story handled except the
   explicit ✓ button — parsing a draft is not the same as having posted it. ---- */
let nrStory = { title: "", source: "", p: 0 }, nrParsed = {};
function nrCopy(t) { navigator.clipboard.writeText(t).catch(() => {}); }
function nrOpen(u) { window.open(u, "_blank", "noopener"); }
function nrField(id) { const el = document.getElementById(id); return el ? el.value.trim() : ""; }
/* audience + personal note are the same every time, so they ride along in synced settings */
function nrSaveProfile() {
  const a = nrField("nr-aud"), n = nrField("nr-note");
  if (a !== (settings.liAudience || "") || n !== (settings.liNote || "")) {
    settings.liAudience = a; settings.liNote = n; saveSettings();
  }
}
function openNewsroom(story) {
  nrStory = { title: story.t || story.name || "", source: story.u || story.source || "", p: story.p || 0 };
  nrParsed = {};
  document.getElementById("nr-story").textContent = "📰 " + (nrStory.title || "(no title)");
  document.getElementById("nr-in").value = "";
  document.getElementById("nr-excerpt").value = "";
  document.getElementById("nr-post").value = "";
  document.getElementById("nr-aud").value = settings.liAudience || "";
  document.getElementById("nr-note").value = settings.liNote || "";
  document.getElementById("nr-parsed").hidden = true;
  document.getElementById("nrmodal").hidden = false;
}
function closeNewsroom() { document.getElementById("nrmodal").hidden = true; }
document.getElementById("nrmodal").addEventListener("click", e => { if (e.target.id === "nrmodal") closeNewsroom(); });
function nrPrompt(mode, label) {
  nrSaveProfile();
  const excerpt = nrField("nr-excerpt");
  const p = window.buildLinkedInPrompt({
    mode: mode, title: nrStory.title, source: nrStory.source,
    excerpt: excerpt, audience: nrField("nr-aud"), note: nrField("nr-note"),
  });
  navigator.clipboard.writeText(p).then(
    () => toast(excerpt
      ? label + " copied — paste it in any AI, then bring the output back here"
      : label + " copied — but with no source facts pasted it will ask you for them first"),
    () => toast("Clipboard blocked — allow clipboard access for this page"));
}
document.getElementById("nr-copy").onclick = () => nrPrompt("insight", "🧠 Insight prompt");
document.getElementById("nr-value").onclick = () => nrPrompt("practical", "🛠️ Practical prompt");
function nrParse(text) {
  const out = {}, re = /\[\[(\w+)\]\]/g, parts = []; let m;
  while ((m = re.exec(text))) parts.push({ key: m[1].toLowerCase(), start: m.index, end: re.lastIndex });
  for (let i = 0; i < parts.length; i++) {
    if (parts[i].key === "end") continue;
    const s = parts[i].end, e = (i + 1 < parts.length) ? parts[i + 1].start : text.length;
    out[parts[i].key] = text.slice(s, e).replace(/^\s*\([^)]*\)\s*$/, "").trim();
  }
  return out;
}
document.getElementById("nr-parse").onclick = () => {
  const raw = document.getElementById("nr-in").value;
  if (!raw.trim()) { toast("Paste the AI output first"); return; }
  const p = nrParse(raw);
  const status = (p.status || "").toLowerCase().replace(/[^a-z_]/g, "");
  if (!p.post && !status) { toast("Couldn't find the [[MARKERS]] — paste the whole output"); return; }
  nrParsed = p;
  nrRenderDraft(status);
};
function nrRenderDraft(status) {
  const st = document.getElementById("nr-status");
  const ready = status !== "needs_input" && status !== "skip";
  if (status === "needs_input") {
    st.textContent = "⚠️ Not enough to write from — " + (nrParsed.missing
      || "paste a few sentences from the source above, then copy the prompt again.");
  } else if (status === "skip") {
    st.textContent = "⏭️ It suggests skipping this one — " + (nrParsed.review || "no useful angle for your audience.");
  } else {
    st.textContent = "✅ Draft ready — read it against the sources below before you post it.";
  }
  document.getElementById("nr-post").value = nrParsed.post || "";
  document.getElementById("nr-sources").textContent = nrParsed.sources
    ? "Sources: " + nrParsed.sources
    : (nrStory.source ? "Source: " + nrStory.source : "");
  document.getElementById("nr-review").textContent = nrParsed.review || "(the AI returned no review notes)";
  ["nr-copypost", "nr-open", "nr-posted", "nr-info", "nr-poster", "nr-xver", "nr-reddit"].forEach(id => {
    const b = document.getElementById(id); b.disabled = !ready;
    b.title = ready ? "" : "No draft to post yet";
  });
  document.getElementById("nr-parsed").hidden = false;
  toast(ready ? "Validated ✓ — review it, then copy" : "Nothing to post from this one");
}
document.getElementById("nr-copypost").onclick = () => {
  const box = document.getElementById("nr-post"), t = box.value.trim();
  if (!t) { toast("Nothing to copy yet"); return; }
  navigator.clipboard.writeText(t).then(
    () => toast("Post copied — paste it into LinkedIn"),
    () => { box.focus(); box.select(); toast("Clipboard blocked — the text is selected, press Ctrl+C"); });
};
document.getElementById("nr-open").onclick = () => {
  nrOpen("https://www.linkedin.com/feed/?shareActive=true");
  toast("LinkedIn opened — paste your post there (it does not prefill)");
};
/* optional extras — all read the post as EDITED in the box, never the raw AI output,
   so what you approved is what gets turned into a visual or another version */
function nrExtra(build, msg) {
  const post = document.getElementById("nr-post").value.trim();
  if (!post) { toast("Write or validate a post first"); return; }
  navigator.clipboard.writeText(build(post)).then(
    () => toast(msg),
    () => toast("Clipboard blocked — allow clipboard access for this page"));
}
document.getElementById("nr-info").onclick = () => nrExtra(
  post => window.buildVisualPrompt({ kind: "infographic", post: post, title: nrStory.title }),
  "🎨 Infographic prompt copied — paste into ChatGPT/Gemini, then generate the image");
document.getElementById("nr-poster").onclick = () => nrExtra(
  post => window.buildVisualPrompt({ kind: "poster", post: post, title: nrStory.title }),
  "🖼️ Poster prompt copied — paste into an image AI");
document.getElementById("nr-xver").onclick = () => nrExtra(
  post => window.buildAdaptPrompt({ platform: "x", post: post, source: nrStory.source }),
  "𝕏 X adaptation prompt copied — it may answer skip, which is a fine result");
document.getElementById("nr-reddit").onclick = () => {
  const community = prompt("Which subreddit, and what are its current rules?\n(Paste the rules — without them it will tell you to go read them first.)", "");
  if (community === null) return;
  nrExtra(post => window.buildAdaptPrompt({ platform: "reddit", post: post, community: community.trim() }),
    "🟠 Reddit check copied — it answers draft, review_rules or skip");
};
document.getElementById("nr-posted").onclick = () => {
  if (!nrStory.source) { toast("This story has no link to tick off"); return; }
  const nd = markStoryDone({ u: nrStory.source, t: nrStory.title });
  toast("Marked posted ✓" + (nd > 1 ? " · also ticked " + nd + " related" : ""));
  closeNewsroom();
};
async function loadPubList() {
  const el = document.getElementById("pub-list");
  if (!FBURL) { el.innerHTML = ""; return; }
  try {
    const data = (await (await fetch(pubBase() + ".json")).json()) || {};
    const arr = Object.values(data).filter(Boolean).sort((a, b) => (b.ts || 0) - (a.ts || 0));
    el.innerHTML = arr.length ? '<div class="note" style="margin:8px 2px 6px">Published on your site (' + arr.length + "):</div>" : "";
    arr.forEach(p => {
      const row = document.createElement("div");
      row.className = "qrow";
      row.innerHTML = '<span class="qtext">' + esc(p.title.slice(0, 60)) + '</span><button class="ghost del">✕</button>';
      row.querySelector(".del").onclick = () => { if (confirm("Remove from website?")) delPub(p.id); };
      el.appendChild(row);
    });
  } catch (e) {}
}
async function delPub(id) {
  try { await fetch(pubBase() + "/" + id + ".json", { method: "DELETE" }); toast("Removed from site"); loadPubList(); }
  catch (e) {}
}

/* ---------------- Home dashboard ---------------- */
const UPDATED = "__UPDATED__";
function renderHome() {
  document.getElementById("homedatetxt").textContent =
    new Date().toLocaleDateString("en-GB",
      { weekday: "long", day: "numeric", month: "long" }) +
    " · radar updated " + UPDATED;
  renderDailyX();
  const sh = document.getElementById("dailyx-shuffle");
  if (sh) sh.onclick = () => { dailyShuffle++; renderDailyX(); };

  const pool = ITEMS.filter(it => it.p !== 9 && !doneSet.has(it.u));
  // "Aaj ka top pick" should be a FRESH high-scoring story (last 2 days),
  // falling back to the overall best only if nothing recent exists.
  const recentCut = Date.now() - 2 * 86400000;
  const recent = pool.filter(it => new Date(it.d || it.f).getTime() > recentCut);
  const candidates = (recent.length ? recent : pool).slice().sort((a, b) => b.sc - a.sc);
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
      '</div>';
  } else {
    tp.innerHTML = '<span class="picktag">✨ Aaj ka top pick</span><p>No stories yet today.</p>';
  }

  const day = Date.now() - 86400000;
  const today = ITEMS.filter(it => it.p !== 9 && new Date(it.d).getTime() > day);
  const hot = today.filter(it => it.l && it.l.length).length;
  const covered = today.filter(it => it.l && it.l.length >= 2).length;
  const sg = document.getElementById("statgrid");
  sg.innerHTML =
    '<div class="scard click" data-act="today"><div class="l">Stories today</div><div class="n">' + today.length + "</div></div>" +
    '<div class="scard click" data-act="hot"><div class="l">Hot</div><div class="n orange">' + hot + "</div></div>" +
    '<div class="scard click" data-act="popular"><div class="l">Most covered</div><div class="n green">' + covered + "</div></div>";
  sg.querySelectorAll(".scard").forEach(card => {
    card.onclick = () => {
      const act = card.dataset.act;
      if (act === "popular") { switchTab("popular"); return; }
      hotOnly = act === "hot";
      if (act === "today") mode = "latest";
      shown = PAGE;
      switchTab("news");
      bar(); render();
    };
  });
}
function qaNews() {
  switchTab("news");
  bar(); render();
}

document.getElementById("q").addEventListener("input", e => {
  q = e.target.value.trim(); shown = PAGE; render();
});
document.getElementById("more").onclick = () => { shown += PAGE; render(); };
function navCounts() {
  try {
    const a = document.getElementById("nc-news");
    if (a) a.textContent = ITEMS.filter(it => it.p !== 9).length;
  } catch (e) {}
}
trendsBar(); bar(); renderHome(); render(); navCounts();
syncPull();   /* pull cross-device done + published, then auto-tick matches */
rpCount();
renderXMini();
ROLE = "owner"; localStorage.setItem("role", "owner");   /* owner-only studio (editors/chat removed) */
setCloudIcon(true);
if (SYNCCFG) {
  pollBoard().then(() => { syncReady = true; });   /* pull latest before pushing */
  startStream();
} else if (FBURL && BOARDKEY && ROLE === "owner") {
  autoConnect();   /* already-unlocked owner device, fresh storage: reconnect automatically */
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


def _load_fburl():
    """Firebase Realtime Database URL: GitHub secret on the cloud, local file
    on the PC. Baked into the page so any device auto-connects after unlock.
    The URL is not secret on its own — the board path needs the access code."""
    url = os.environ.get("FIREBASE_URL", "").strip()
    if not url:
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "firebase_url.txt")) as f:
                url = f.read().strip()
        except FileNotFoundError:
            pass
    return url


def generate():
    conn = database.connect()
    # Order by DISCOVERY time (fetched) so the page matches the phone: a story
    # found today but published days ago still shows as freshly arrived, and the
    # MAX_STORIES cap keeps the most recently discovered (never drops what the
    # phone just alerted). Published date is the tiebreaker within a fetch batch.
    rows = conn.execute(
        "SELECT id, title, url, links, source, pillar, published, fetched FROM items "
        "ORDER BY fetched DESC, COALESCE(published, fetched) DESC LIMIT ?", (MAX_STORIES,)
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
            "d": when, "f": r["fetched"], "l": links,
            "sc": score, "r": reasons, "lo": local,
        })

    code = _load_passcode()
    lock_hash = hashlib.sha256(code.encode()).hexdigest() if code else ""
    fb_url = _load_fburl()

    updated = now.strftime("%d %b %Y, %H:%M UTC")
    html = (PAGE
            .replace("__PILLARS__", json.dumps(config.CATEGORIES))
            .replace("__ITEMS__", json.dumps(items, ensure_ascii=False))
            .replace("__TRENDS__", json.dumps(chips, ensure_ascii=False))
            .replace("__LOCKHASH__", lock_hash)
            .replace("__FBURL__", fb_url)
            .replace("__CACHE__", now.strftime("%Y%m%d%H%M"))
            .replace("__UPDATED__", updated))

    os.makedirs(OUT_DIR, exist_ok=True)
    # The private studio now lives at /studio.html; the public AI Radar news
    # site (generate_public.py) takes the root /index.html.
    with open(os.path.join(OUT_DIR, "studio.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"docs/studio.html written with {len(items)} stories.")


if __name__ == "__main__":
    generate()
