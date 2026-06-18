"""
AI Radar - PUBLIC news website generator (modern publication design).

Reads news.db and writes docs/index.html = an open, SEO-friendly AI-news site
styled like a modern publication (breaking ticker, radar masthead, hero lead +
side stack, two-column feed + sidebar, research grid, full footer, article
reader). Editor-published articles (from Firebase /published) become the hero +
related stories. The private studio is generated separately to docs/studio.html.

Run:  python generate_public.py
"""

import html as _h
import json
import os
from datetime import datetime, timezone

import config
import database
import scoring


def _load_fburl():
    url = os.environ.get("FIREBASE_URL", "").strip()
    if not url:
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "firebase_url.txt")) as f:
                url = f.read().strip()
        except FileNotFoundError:
            pass
    return url


OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
MAX_STORIES = 600
SITE_NAME = "AI Radar"
# The address where the site is actually served. Canonical/OG/sitemap all use
# this — it MUST match the live URL or Google won't index correctly.
SITE_URL = "https://radar.hafizahmad.com/"
# Paste the Google Search Console "HTML tag" verification code here, then re-run.
GSC_VERIFY = ""
SITE_DESC = ("Breaking artificial-intelligence news, every day: new models and tools, "
             "AI in science, business, and research — updated every 30 minutes, with links "
             "to the original sources.")
CONTACT_EMAIL = "get.shahzadsaddique@gmail.com"

# section colours, keyed by category id (match the publication design palette)
CATCOLORS = {1: "#22D3EE", 2: "#8B7CFF", 3: "#5B9DFF", 4: "#38BDF8", 5: "#F8A93B",
             6: "#7C8BFF", 7: "#34D399", 8: "#FF5A8A", 9: "#A78BFA", 10: "#9AA7BE"}

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#070A11">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link rel="apple-touch-icon" href="favicon.svg">
<title>__SITE__ — Latest AI News, updated all day</title>
<meta name="description" content="__DESC__">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="keywords" content="AI news, artificial intelligence news, AI models, AI tools, machine learning news, LLM, ChatGPT, generative AI, AI research">
<meta name="author" content="AI Radar">
<link rel="canonical" href="__URL__">
__GSC__
<meta property="og:site_name" content="__SITE__">
<meta property="og:title" content="__SITE__ — Latest AI News">
<meta property="og:description" content="__DESC__">
<meta property="og:type" content="website">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="__URL__">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@aixahmad">
<meta name="twitter:title" content="__SITE__ — Latest AI News">
<meta name="twitter:description" content="__DESC__">
<script type="application/ld+json">__JSONLD__</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Newsreader:ital,opsz,wght@0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,500&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#070A11;--surface:#0E1420;--surface2:#141C2B;--surface3:#1A2335;
    --line:#222C3F;--line2:#2C3850;
    --hi:#EEF2F8;--mid:#9AA7BE;--dim:#62708A;
    --accent:#4D8BFF;--accent2:#38BDF8;--hot:#FF5436;--amber:#F8A93B;
  }
  *{box-sizing:border-box;}
  html,body{margin:0;padding:0;}
  body{background:var(--bg);color:var(--hi);font-family:'Space Grotesk',system-ui,sans-serif;-webkit-font-smoothing:antialiased;}
  a{color:inherit;text-decoration:none;}
  button{font-family:inherit;color:inherit;}
  input{font-family:inherit;}
  .serif{font-family:'Newsreader',Georgia,serif;}
  .mono{font-family:'JetBrains Mono',monospace;}
  ::-webkit-scrollbar{width:12px;height:12px;}
  ::-webkit-scrollbar-thumb{background:#1E2738;border-radius:9px;border:3px solid transparent;background-clip:content-box;}
  @keyframes radarPulse{0%{transform:scale(.6);opacity:.85}100%{transform:scale(2.4);opacity:0}}
  @keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}
  .wrap{max-width:1240px;margin:0 auto;padding:26px 22px 20px;width:100%;}

  /* breaking ticker */
  .ticker{display:flex;align-items:center;gap:14px;background:#0A0E16;border-bottom:1px solid var(--line);padding:7px 22px;overflow:hidden;}
  .ticker .bk{display:inline-flex;align-items:center;gap:7px;flex:none;background:var(--hot);color:#fff;font-size:10.5px;font-weight:700;letter-spacing:.08em;padding:3px 9px;border-radius:5px;}
  .ticker .bk .d{width:6px;height:6px;border-radius:50%;background:#fff;animation:blink 1.1s infinite;}
  .tkrow{display:flex;align-items:center;gap:26px;overflow:hidden;flex:1;min-width:0;}
  .tk{display:inline-flex;align-items:center;gap:9px;font-size:12.5px;color:var(--mid);white-space:nowrap;}
  .tk .dot{width:3px;height:3px;border-radius:50%;background:var(--hot);}
  .tklive{flex:none;font-size:11px;color:var(--dim);}
  @media(max-width:760px){.ticker .tklive{display:none}}

  /* masthead */
  header.mast{position:sticky;top:0;z-index:50;background:rgba(7,10,17,.86);backdrop-filter:blur(14px);border-bottom:1px solid var(--line);}
  .mastrow{display:flex;align-items:center;gap:18px;padding:13px 22px;max-width:1240px;margin:0 auto;}
  .brand{display:inline-flex;align-items:center;gap:10px;flex:none;}
  .orb{position:relative;width:32px;height:32px;border-radius:9px;background:radial-gradient(120% 120% at 30% 25%,#5B9DFF,#2D5Cff);display:flex;align-items:center;justify-content:center;overflow:hidden;}
  .orb .ring{position:absolute;width:30px;height:30px;border-radius:50%;border:1.5px solid rgba(255,255,255,.55);animation:radarPulse 2.6s ease-out infinite;}
  .brand .nm{font-size:18px;font-weight:700;letter-spacing:-.02em;}
  .brand .nm b{color:var(--accent);font-weight:700;}
  nav.cats{flex:1;min-width:0;display:flex;align-items:center;gap:3px;overflow-x:auto;padding:0 4px;scrollbar-width:none;}
  nav.cats::-webkit-scrollbar{display:none;}
  nav.cats button{flex:none;border:none;background:transparent;color:var(--mid);font-size:13px;font-weight:500;padding:8px 13px;border-radius:8px;cursor:pointer;white-space:nowrap;}
  nav.cats button:hover{color:var(--hi);background:var(--surface2);}
  nav.cats button.active{color:var(--hi);font-weight:600;background:var(--surface2);box-shadow:inset 0 -2px 0 var(--accent);}
  .mright{flex:none;display:flex;align-items:center;gap:9px;}
  .mright a{display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border:1px solid var(--line);border-radius:9px;color:var(--mid);font-size:14px;}
  .mright a:hover{border-color:var(--accent);color:var(--hi);}
  @media(max-width:900px){nav.cats{order:3;flex-basis:100%;}}

  /* hero */
  .herogrid{display:grid;grid-template-columns:1.7fr 1fr;gap:16px;}
  @media(max-width:900px){.herogrid{grid-template-columns:1fr;}}
  .lead{position:relative;border:1px solid var(--line);border-radius:18px;overflow:hidden;cursor:pointer;text-align:left;padding:0;background:var(--surface);min-height:420px;display:flex;flex-direction:column;justify-content:flex-end;color:var(--hi);}
  .lead:hover{border-color:var(--accent);}
  .limg{position:absolute;inset:0;background-size:cover;background-position:center;}
  .lover{position:absolute;inset:0;background:linear-gradient(to top,rgba(5,8,14,.96) 12%,rgba(5,8,14,.55) 48%,rgba(5,8,14,.12) 100%);}
  .lbody{position:relative;padding:26px 28px 28px;}
  .lbadges{display:flex;align-items:center;gap:10px;margin-bottom:13px;flex-wrap:wrap;}
  .leadbadge{display:inline-flex;align-items:center;gap:6px;background:rgba(255,84,54,.16);border:1px solid rgba(255,84,54,.4);color:#FF8A73;font-size:10.5px;font-weight:700;letter-spacing:.06em;padding:3px 9px;border-radius:6px;}
  .leadbadge .dot{width:5px;height:5px;border-radius:50%;background:var(--hot);animation:blink 1.1s infinite;}
  .lead h1{font-size:clamp(24px,3vw,36px);line-height:1.1;font-weight:600;letter-spacing:-.015em;margin:0 0 12px;max-width:660px;}
  .ldek{font-size:14.5px;line-height:1.55;color:var(--mid);margin:0 0 14px;max-width:600px;}
  .lmeta{display:flex;align-items:center;gap:11px;font-size:12px;color:var(--dim);}
  .src{color:var(--mid);font-weight:600;}
  .sidestack{display:flex;flex-direction:column;gap:14px;}
  .scardx{display:flex;gap:13px;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--surface);cursor:pointer;text-align:left;padding:11px;flex:1;color:var(--hi);}
  .scardx:hover{border-color:var(--accent);background:var(--surface2);}
  .sthumb{width:92px;flex:none;border-radius:9px;align-self:stretch;min-height:84px;background-size:cover;background-position:center;}
  .sbody{min-width:0;display:flex;flex-direction:column;justify-content:center;}
  .stitle{font-size:16px;line-height:1.22;font-weight:600;letter-spacing:-.01em;margin-top:7px;}
  .smeta{font-size:11.5px;color:var(--dim);margin-top:7px;}

  .cat{display:inline-flex;align-items:center;width:fit-content;white-space:nowrap;font-size:10.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;border:1px solid;padding:3px 9px;border-radius:6px;}

  /* status + chips */
  .statusrow{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:22px 0 6px;padding-bottom:18px;border-bottom:1px solid var(--line);}
  .statusrow .live{display:inline-flex;align-items:center;gap:8px;font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.03em;color:var(--mid);}
  .statusrow .live .d{width:7px;height:7px;border-radius:50%;background:#34D399;box-shadow:0 0 0 3px rgba(52,211,153,.18);}
  .chips{margin-left:auto;display:flex;gap:7px;flex-wrap:wrap;}
  .chip{border:1px solid var(--line);background:var(--surface);color:var(--mid);font-size:11.5px;font-weight:500;padding:5px 11px;border-radius:20px;cursor:pointer;}
  .chip:hover{border-color:var(--accent);color:var(--hi);}

  /* search */
  .searchrow{display:flex;gap:10px;margin:18px 0 26px;}
  .searchbox{flex:1;display:flex;align-items:center;gap:11px;border:1px solid var(--line);background:var(--surface);border-radius:12px;padding:0 15px;}
  .searchbox:focus-within{border-color:var(--accent);}
  .searchbox svg{flex:none;}
  .searchbox input{flex:1;border:none;background:transparent;outline:none;color:var(--hi);font-size:14px;padding:14px 0;}
  .searchbtn{border:none;background:linear-gradient(135deg,#4D8BFF,#38BDF8);color:#fff;font-size:13px;font-weight:600;padding:0 18px;border-radius:12px;cursor:pointer;flex:none;}
  .hotbtn{border:1px solid var(--line);background:var(--surface);color:var(--mid);font-size:13px;font-weight:600;padding:0 16px;border-radius:12px;cursor:pointer;flex:none;}
  .hotbtn.on{border-color:var(--hot);color:var(--hot);background:rgba(255,84,54,.1);}

  /* two columns */
  .cols{display:grid;grid-template-columns:minmax(0,1fr) 332px;gap:30px;align-items:start;}
  @media(max-width:980px){.cols{grid-template-columns:1fr;}}
  .sec-h{display:flex;align-items:center;gap:9px;font-size:13px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--hi);margin:0 0 16px;}
  .sec-h .bar{width:14px;height:2px;background:var(--accent);}
  .feedtop{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;}
  .feedtop .fb{display:flex;gap:6px;}
  .feedtop .fb button{border:1px solid var(--line);background:transparent;color:var(--mid);font-size:11.5px;font-weight:600;padding:5px 12px;border-radius:8px;cursor:pointer;}
  .feedtop .fb button.on{border-color:var(--accent);background:rgba(77,139,255,.12);color:var(--accent);}
  .count{font-size:12px;color:var(--dim);margin:0 2px 6px;}

  .feed{display:flex;flex-direction:column;}
  .vrow{display:flex;gap:16px;padding:18px 0;border-bottom:1px solid var(--line);}
  .vthumb{width:148px;height:104px;flex:none;border-radius:11px;border:none;cursor:pointer;padding:0;background-size:cover;background-position:center;}
  .vthumb:hover{opacity:.92;}
  .vmain{min-width:0;flex:1;}
  .vtop{display:flex;align-items:center;gap:9px;margin-bottom:8px;}
  .hotsrc{display:inline-flex;align-items:center;gap:4px;font-size:10.5px;font-weight:600;color:var(--amber);}
  .vtitle{display:block;font-size:19px;line-height:1.24;font-weight:600;letter-spacing:-.01em;color:var(--hi);}
  .vtitle:hover{color:var(--accent);}
  .vmeta{display:flex;align-items:center;gap:11px;margin-top:11px;font-size:11.5px;color:var(--dim);}
  .savebtn{display:inline-flex;align-items:center;gap:5px;margin-left:auto;border:none;background:transparent;color:var(--dim);font-size:11.5px;font-weight:500;cursor:pointer;}
  .savebtn:hover{color:var(--accent);}
  .savebtn.on{color:var(--accent);}
  @media(max-width:560px){.vthumb{width:104px;height:78px;}.vtitle{font-size:16px;}}
  .more{display:block;margin:28px auto 0;border:1px solid var(--line);background:var(--surface2);color:var(--hi);font-size:13px;font-weight:600;padding:11px 26px;border-radius:11px;cursor:pointer;}
  .more:hover{border-color:var(--accent);}
  .empty{color:var(--dim);text-align:center;padding:48px 0;}

  /* research grid */
  .rgrid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
  @media(max-width:560px){.rgrid{grid-template-columns:1fr;}}
  .rcard{text-align:left;border:1px solid var(--line);background:var(--surface);border-radius:12px;padding:15px 16px;cursor:pointer;color:var(--hi);}
  .rcard:hover{border-color:#A78BFA;background:var(--surface2);}
  .rlabel{font-size:10.5px;font-weight:700;letter-spacing:.06em;color:#A78BFA;}
  .rtitle{font-size:15.5px;line-height:1.25;font-weight:600;margin:8px 0 10px;}
  .rmeta{font-size:11px;color:var(--dim);}

  /* sidebar */
  .aside{display:flex;flex-direction:column;gap:16px;position:sticky;top:78px;}
  @media(max-width:980px){.aside{position:static;}}
  .sblock{border:1px solid var(--line);background:var(--surface);border-radius:14px;padding:17px 18px;}
  .shead{display:flex;align-items:center;gap:8px;font-size:12.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--hi);margin-bottom:8px;}
  .trow{display:flex;gap:12px;width:100%;border:none;background:transparent;text-align:left;cursor:pointer;padding:10px 0;border-top:1px solid var(--line);color:var(--hi);}
  .trow:hover{opacity:.78;}
  .trank{font-size:18px;font-weight:500;flex:none;width:22px;line-height:1.1;}
  .ttitle{font-size:14px;line-height:1.26;font-weight:600;}
  .tmeta{font-size:10.5px;color:var(--dim);margin-top:5px;}
  .toolrow2{display:flex;align-items:center;gap:12px;width:100%;border:none;background:transparent;text-align:left;cursor:pointer;padding:11px 0;border-top:1px solid var(--line);color:var(--hi);}
  .toolrow2:hover{opacity:.8;}
  .ticon{width:38px;height:38px;border-radius:10px;flex:none;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;color:#fff;}
  .tname{font-size:13.5px;font-weight:600;line-height:1.25;}
  .ttag{font-size:11.5px;color:var(--mid);margin-top:3px;}
  .briefcard{border:1px solid rgba(77,139,255,.45);background:linear-gradient(160deg,rgba(77,139,255,.16),rgba(56,189,248,.05));border-radius:14px;padding:20px 18px;}
  .briefh{font-size:19px;font-weight:600;line-height:1.2;margin-bottom:7px;}
  .briefcard p{font-size:12.5px;line-height:1.5;color:var(--mid);margin:0 0 14px;}
  .bbtn,.bbtn2{display:block;text-align:center;font-size:13px;font-weight:600;padding:10px;border-radius:9px;margin-bottom:8px;}
  .bbtn{background:linear-gradient(135deg,#4D8BFF,#38BDF8);color:#fff;}
  .bbtn2{border:1px solid var(--line2);color:var(--hi);}
  .bbtn:hover,.bbtn2:hover{opacity:.92;}
  .bfoot{font-size:10.5px;color:var(--dim);margin-top:4px;}

  /* footer */
  footer{border-top:1px solid var(--line);background:#0A0E16;margin-top:42px;}
  .ftop{display:flex;flex-wrap:wrap;gap:32px;max-width:1240px;margin:0 auto;padding:40px 22px 20px;}
  .fbrand{flex:1 1 280px;min-width:240px;}
  .fbrand .brand{margin-bottom:13px;}
  .fbrand p{font-size:12.5px;line-height:1.6;color:var(--mid);max-width:300px;margin:0 0 14px;}
  .fsoc{display:flex;gap:8px;}
  .fsoc a{width:34px;height:34px;border:1px solid var(--line);border-radius:8px;display:flex;align-items:center;justify-content:center;color:var(--mid);font-size:14px;}
  .fsoc a:hover{border-color:var(--accent);color:var(--accent);}
  .fcol{flex:1 1 150px;}
  .fcol h4{font-size:11px;font-weight:700;letter-spacing:.08em;color:var(--dim);margin:0 0 13px;}
  .fcol a,.fcol .lk{display:block;font-size:13px;color:var(--mid);padding:5px 0;cursor:pointer;background:none;border:none;text-align:left;font-family:inherit;}
  .fcol a:hover,.fcol .lk:hover{color:var(--accent);}
  .fbot{display:flex;flex-wrap:wrap;gap:10px;justify-content:space-between;align-items:center;border-top:1px solid var(--line);max-width:1240px;margin:0 auto;padding:18px 22px 30px;font-size:11.5px;color:var(--dim);}
  .fbot .legal{display:flex;gap:14px;}
  .fbot .legal button{background:none;border:none;color:var(--dim);cursor:pointer;font:inherit;}
  .fbot .legal button:hover{color:var(--accent);}

  /* reader */
  #reader{position:fixed;inset:0;z-index:80;background:rgba(4,7,14,.82);overflow-y:auto;}
  .rbox{max-width:760px;margin:36px auto;background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:0 0 32px;}
  .rclose{position:sticky;top:14px;float:right;margin:14px 14px 0 0;background:var(--surface3);border:1px solid var(--line);color:var(--hi);border-radius:50%;width:38px;height:38px;font-size:15px;cursor:pointer;z-index:2;}
  .rinner{padding:10px 30px 0;}
  .rbox h1{font-size:clamp(26px,4vw,40px);line-height:1.1;font-weight:600;letter-spacing:-.02em;margin:14px 0 18px;}
  .rmeta{display:flex;align-items:center;gap:10px;padding-bottom:20px;border-bottom:1px solid var(--line);}
  .ravatar{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#4D8BFF,#38BDF8);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;color:#fff;flex:none;}
  .rauthor{font-size:13.5px;font-weight:600;}
  .rsub{font-size:11.5px;color:var(--dim);}
  .rimg{height:330px;border-radius:16px;margin:22px 0;border:1px solid var(--line);background-size:cover;background-position:center;}
  .rbody{font-size:18.5px;line-height:1.72;color:#D4DBE8;}
  .rbody p{margin:0 0 22px;}
  .srclink{color:var(--accent);font-family:'Space Grotesk',sans-serif;font-size:14px;font-weight:600;}
  .relgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;}
  .relcard{text-align:left;border:1px solid var(--line);background:var(--surface2);border-radius:13px;overflow:hidden;cursor:pointer;padding:0;color:var(--hi);}
  .relcard:hover{border-color:var(--accent);}
  .relimg{height:104px;background-size:cover;background-position:center;}
  .relb{padding:13px 14px;}
  .reltitle{font-size:15px;line-height:1.25;font-weight:600;margin-top:8px;}
</style>
</head>
<body>

<div class="ticker">
  <span class="bk"><span class="d"></span>BREAKING</span>
  <div class="tkrow" id="ticker"></div>
  <span class="tklive mono">LIVE · __UPDATED__</span>
</div>

<header class="mast">
  <div class="mastrow">
    <a class="brand" href="/"><span class="orb"><span class="ring"></span>
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"></circle><path d="M12 12L19 8"></path><circle cx="12" cy="12" r="2" fill="#fff" stroke="none"></circle></svg>
    </span><span class="nm">AI<b>Radar</b></span></a>
    <nav class="cats" id="nav"></nav>
    <div class="mright">
      <a href="https://x.com/aixahmad" target="_blank" rel="noopener" title="X / Twitter">𝕏</a>
      <a href="https://youtube.com/@aixahmad" target="_blank" rel="noopener" title="YouTube">▶</a>
    </div>
  </div>
</header>

<main class="wrap">
  <section id="hero"></section>

  <div class="statusrow">
    <span class="live"><span class="d"></span><span id="updlabel"></span></span>
    <div class="chips" id="trends"></div>
  </div>

  <div class="searchrow">
    <div class="searchbox">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#62708A" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"></circle><path d="M21 21l-4-4"></path></svg>
      <input id="q" placeholder="Search AI news — models, tools, companies, people…">
    </div>
    <button class="searchbtn" id="searchgo">Search</button>
  </div>

  <div class="cols">
    <div class="main">
      <div class="feedtop">
        <h2 class="sec-h" style="margin:0"><span class="bar"></span>Latest from AI Radar</h2>
        <div class="fb">
          <button id="fLatest" class="on">Latest</button>
          <button id="fHot">🔥 Hot</button>
        </div>
      </div>
      <div class="count" id="count"></div>
      <div class="feed" id="list"></div>
      <button class="more" id="more" style="display:none">Show more stories</button>
      <div id="researchwrap"></div>
    </div>

    <aside class="aside">
      <section class="sblock" id="trending"></section>
      <section class="sblock" id="tools"></section>
      <section class="briefcard">
        <div class="briefh serif">The AI Radar Brief</div>
        <p>The AI stories that matter — in simple Urdu, every day. Follow AI x Ahmad.</p>
        <a class="bbtn" href="https://youtube.com/@aixahmad" target="_blank" rel="noopener">▶ Subscribe on YouTube</a>
        <a class="bbtn2" href="https://x.com/aixahmad" target="_blank" rel="noopener">𝕏 Follow on X</a>
        <div class="bfoot">Join the AI x Ahmad community · No spam.</div>
      </section>
    </aside>
  </div>
</main>

<footer>
  <div class="ftop">
    <div class="fbrand">
      <a class="brand" href="/"><span class="orb"><span class="ring"></span>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"></circle><path d="M12 12L19 8"></path></svg>
      </span><span class="nm">AI<b>Radar</b></span></a>
      <p>The fastest way to follow artificial intelligence. We scan hundreds of sources and surface what matters — refreshed every 30 minutes.</p>
      <div class="fsoc">
        <a href="https://x.com/aixahmad" target="_blank" rel="noopener" title="X / Twitter">𝕏</a>
        <a href="https://youtube.com/@aixahmad" target="_blank" rel="noopener" title="YouTube">▶</a>
        <a href="mailto:__EMAIL__" title="Email">✉</a>
      </div>
    </div>
    <div class="fcol"><h4>SECTIONS</h4><div id="fsections"></div></div>
    <div class="fcol"><h4>AI RADAR</h4>
      <button class="lk" onclick="openPage('about')">About us</button>
      <button class="lk" onclick="openPage('how')">How it works</button>
      <button class="lk" onclick="openPage('editorial')">Editorial standards</button>
      <a href="/studio.html">Newsroom (staff)</a>
    </div>
    <div class="fcol"><h4>CONTACT</h4>
      <a href="mailto:__EMAIL__">__EMAIL__</a>
      <a href="https://x.com/aixahmad" target="_blank" rel="noopener">DM @aixahmad on X</a>
      <button class="lk" onclick="openPage('advertise')">Advertise / partner</button>
      <button class="lk" onclick="openPage('contact')">Send a tip</button>
    </div>
  </div>
  <div class="fbot">
    <span>© <span id="yr"></span> AI Radar · An independent AI-news aggregator. Headlines link back to the source.</span>
    <span class="legal">
      <button onclick="openPage('privacy')">Privacy</button>
      <button onclick="openPage('terms')">Terms</button>
      <button onclick="openPage('disclaimer')">Disclaimer</button>
    </span>
  </div>
</footer>

<div id="reader" hidden></div>

<script>
const PILLARS = __PILLARS__, ITEMS = __ITEMS__, TRENDS = __TRENDS__, COLORS = __COLORS__, PAGE = 18;
const PUBURL = "__FBURL__", CONTACT = "__EMAIL__";
let pillar = 0, hotOnly = false, q = "", shown = PAGE, PUBS = [];
let SAVED = new Set(JSON.parse(localStorage.getItem("air_saved") || "[]"));

document.getElementById("yr").textContent = new Date().getFullYear();
document.getElementById("updlabel").textContent = "UPDATED __UPDATED__ · REFRESHES EVERY 30 MIN · " + ITEMS.length + " STORIES";

function ago(iso){ if(!iso) return ""; const s=(Date.now()-new Date(iso).getTime())/1000;
  if(s<3600) return Math.max(1,s/60|0)+" min ago"; if(s<86400) return (s/3600|0)+"h ago"; return (s/86400|0)+"d ago"; }
function esc(t){ const d=document.createElement("div"); d.textContent=t==null?"":t; return d.innerHTML; }
function fmtDate(ts){ try{ return new Date(ts).toLocaleDateString("en-GB",{day:"numeric",month:"short"}); }catch(e){ return ""; } }
function col(p){ return COLORS[p] || (p===0?"#4D8BFF":"#9AA7BE"); }
function colByName(nm){ for(const k in PILLARS){ if(PILLARS[k]===nm) return col(+k); } return "#4D8BFF"; }
function catTag(t,c){ return '<span class="cat" style="color:'+c+';background:'+c+'1F;border-color:'+c+'3D">'+esc(t)+'</span>'; }
function thumbCSS(seed,hex){ const pos=['85% 12%','15% 18%','78% 82%','22% 78%','50% 0%','90% 50%','10% 50%'][((seed%7)+7)%7];
  return "background:radial-gradient(120% 110% at "+pos+","+hex+"5C,rgba(8,11,18,0) 58%),linear-gradient(155deg,#15203A 0%,#0B1322 100%);"; }
function bmIcon(on){ return '<svg width="13" height="13" viewBox="0 0 24 24" fill="'+(on?"currentColor":"none")+'" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>'; }

function filtered(){ const n=q.toLowerCase(); return ITEMS.filter(it =>
  (!pillar||it.p===pillar) && (!hotOnly||(it.l&&it.l.length)) && (!n||it.t.toLowerCase().includes(n))); }

/* ---- breaking ticker ---- */
function renderTicker(){
  document.getElementById("ticker").innerHTML = ITEMS.slice(0,4)
    .map(it=>'<span class="tk"><span class="dot"></span>'+esc(it.t.slice(0,82))+'</span>').join("");
}

/* ---- category nav ---- */
function navBar(){
  const el=document.getElementById("nav"); el.innerHTML="";
  const mk=(id,label)=>{ const b=document.createElement("button"); b.textContent=label; b.className=id===pillar?"active":"";
    b.onclick=()=>{ pillar=id; shown=PAGE; navBar(); render(); window.scrollTo({top:0,behavior:"smooth"}); }; el.appendChild(b); };
  mk(0,"Top"); Object.entries(PILLARS).forEach(([k,v])=>mk(+k,v));
}

/* ---- trend chips ---- */
function trendsBar(){ const el=document.getElementById("trends"); el.innerHTML="";
  TRENDS.forEach(t=>{ const c=document.createElement("button"); c.className="chip";
    c.textContent="# "+t.display;
    c.onclick=()=>{ q=t.display; document.getElementById("q").value=t.display; shown=PAGE; render(); window.scrollTo({top:document.querySelector(".cols").offsetTop-70,behavior:"smooth"}); };
    el.appendChild(c); }); }

/* ---- hero (editor articles, else top news) ---- */
function heroEntries(){
  const out=[];
  PUBS.slice(0,4).forEach((p,i)=>out.push({ title:p.title, catName:(p.cat||"Featured"), color:colByName(p.cat),
    source:"AI Radar", time:fmtDate(p.ts), dek:(p.body||"").replace(/\s+/g," ").trim().slice(0,170),
    img:p.image||"", seed:i, open:()=>openArticle(i) }));
  let i=0;
  while(out.length<4 && i<ITEMS.length){ const it=ITEMS[i];
    out.push({ title:it.t, catName:PILLARS[it.p], color:col(it.p), source:it.s, time:ago(it.d), dek:"",
      img:"", seed:i+3, open:()=>window.open(it.u,"_blank","noopener") }); i++; }
  return out;
}
function renderHero(){
  const e=heroEntries(); const el=document.getElementById("hero");
  if(!e.length){ el.innerHTML=""; return; }
  const lead=e[0], side=e.slice(1,4);
  el.innerHTML="";
  const L=document.createElement("button"); L.className="lead"; L.onclick=lead.open;
  L.innerHTML='<div class="limg" style="'+(lead.img?("background-image:url('"+esc(lead.img)+"')"):thumbCSS(lead.seed,lead.color))+'"></div><div class="lover"></div>'+
    '<div class="lbody"><div class="lbadges">'+catTag(lead.catName,lead.color)+'<span class="leadbadge"><span class="dot"></span>LEAD STORY</span></div>'+
    '<h1 class="serif">'+esc(lead.title)+'</h1>'+(lead.dek?'<p class="ldek">'+esc(lead.dek)+'…</p>':'')+
    '<div class="lmeta"><span class="src">'+esc(lead.source)+'</span><span>·</span><span>'+esc(lead.time)+'</span></div></div>';
  const S=document.createElement("div"); S.className="sidestack";
  side.forEach(s=>{ const b=document.createElement("button"); b.className="scardx"; b.onclick=s.open;
    b.innerHTML='<div class="sthumb" style="'+(s.img?("background-image:url('"+esc(s.img)+"')"):thumbCSS(s.seed,s.color))+'"></div>'+
      '<div class="sbody">'+catTag(s.catName,s.color)+'<div class="stitle serif">'+esc(s.title)+'</div>'+
      '<div class="smeta"><span class="src">'+esc(s.source)+'</span> · '+esc(s.time)+'</div></div>';
    S.appendChild(b); });
  const grid=document.createElement("div"); grid.className="herogrid"; grid.appendChild(L); grid.appendChild(S);
  el.appendChild(grid);
}

/* ---- feed ---- */
function render(){
  const items=filtered();
  document.getElementById("count").textContent=items.length+" stories"+(q?' for "'+q+'"':"")+(pillar?" · "+PILLARS[pillar]:"")+(hotOnly?" · hot":" · newest first");
  const list=document.getElementById("list");
  list.innerHTML=items.length?"":'<div class="empty">No stories found.</div>';
  items.slice(0,shown).forEach((it,idx)=>{
    const a=document.createElement("article"); a.className="vrow";
    const hot=(it.l&&it.l.length)?'<span class="hotsrc">🔥 '+(it.l.length+1)+' sources</span>':'';
    const on=SAVED.has(it.u);
    a.innerHTML='<button class="vthumb" style="'+thumbCSS(idx,col(it.p))+'"></button>'+
      '<div class="vmain"><div class="vtop">'+catTag(PILLARS[it.p],col(it.p))+hot+'</div>'+
      '<a class="vtitle serif" href="'+esc(it.u)+'" target="_blank" rel="noopener">'+esc(it.t)+'</a>'+
      '<div class="vmeta"><span class="src">'+esc(it.s)+'</span><span>·</span><span>'+ago(it.d)+'</span>'+
      '<button class="savebtn'+(on?" on":"")+'">'+bmIcon(on)+(on?"Saved":"Save")+'</button></div></div>';
    a.querySelector(".vthumb").onclick=()=>window.open(it.u,"_blank","noopener");
    a.querySelector(".savebtn").onclick=(e)=>{ e.stopPropagation(); toggleSave(it.u); };
    list.appendChild(a);
  });
  document.getElementById("more").style.display=items.length>shown?"block":"none";
}
function toggleSave(u){ if(SAVED.has(u)) SAVED.delete(u); else SAVED.add(u);
  localStorage.setItem("air_saved", JSON.stringify([...SAVED])); render(); }

/* ---- research grid ---- */
function renderResearch(){
  const rs=ITEMS.filter(it=>it.p===9).slice(0,4);
  const w=document.getElementById("researchwrap");
  if(!rs.length){ w.innerHTML=""; return; }
  let h='<div class="sec-h" style="margin-top:30px"><span class="bar" style="background:#A78BFA"></span>Research Papers</div><div class="rgrid">';
  rs.forEach(it=>{ h+='<button class="rcard" data-u="'+esc(it.u)+'"><span class="rlabel">RESEARCH PAPERS</span>'+
    '<div class="rtitle serif">'+esc(it.t)+'</div><div class="rmeta"><span class="src">'+esc(it.s)+'</span> · '+ago(it.d)+'</div></button>'; });
  w.innerHTML=h+"</div>";
  w.querySelectorAll(".rcard").forEach(b=>b.onclick=()=>window.open(b.dataset.u,"_blank","noopener"));
}

/* ---- sidebar: trending ---- */
function renderTrending(){
  const top=ITEMS.slice().sort((a,b)=>((b.l?b.l.length:0)-(a.l?a.l.length:0))).slice(0,5);
  let h='<div class="shead"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#FF5436" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L4.5 12.5h6L9 22l9-12h-6z"></path></svg>Trending Now</div>';
  top.forEach((it,i)=>{ const rc=['#FF5436','#F8A93B','#4D8BFF','#9AA7BE','#9AA7BE'][i];
    h+='<button class="trow" data-u="'+esc(it.u)+'"><span class="trank mono" style="color:'+rc+'">'+String(i+1).padStart(2,"0")+'</span>'+
      '<div class="tbody"><div class="ttitle serif">'+esc(it.t)+'</div><div class="tmeta">'+esc(it.s)+' · '+ago(it.d)+'</div></div></button>'; });
  const el=document.getElementById("trending"); el.innerHTML=h;
  el.querySelectorAll(".trow").forEach(b=>b.onclick=()=>window.open(b.dataset.u,"_blank","noopener"));
}

/* ---- sidebar: new tools & models (category 1) ---- */
function renderTools(){
  const ts=ITEMS.filter(it=>it.p===1).slice(0,4);
  const el=document.getElementById("tools");
  if(!ts.length){ el.innerHTML=""; return; }
  const c=col(1);
  let h='<div class="shead"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l-1.5 5 5-1.5L18 8a3 3 0 0 0-4-4z"></path><path d="M14 5l4 4"></path></svg>New Tools & Models</div>';
  ts.forEach(it=>{ const ini=((it.t||"A").trim()[0]||"A").toUpperCase();
    h+='<button class="toolrow2" data-u="'+esc(it.u)+'"><div class="ticon" style="background:linear-gradient(135deg,'+c+','+c+'99)">'+esc(ini)+'</div>'+
      '<div style="min-width:0;flex:1"><div class="tname">'+esc(it.t.slice(0,64))+'</div><div class="ttag">'+esc(it.s)+' · '+ago(it.d)+'</div></div></button>'; });
  el.innerHTML=h;
  el.querySelectorAll(".toolrow2").forEach(b=>b.onclick=()=>window.open(b.dataset.u,"_blank","noopener"));
}

/* ---- editor-published articles from Firebase ---- */
async function loadFeatured(){
  if(!PUBURL) return;
  try{
    const r=await fetch(PUBURL.replace(/\/+$/,"")+"/published.json"); if(!r.ok) return;
    const data=await r.json()||{}; PUBS=Object.values(data).filter(Boolean).sort((a,b)=>(b.ts||0)-(a.ts||0));
    if(PUBS.length){ renderHero(); openArticleFromHash(); }
  }catch(e){}
}
function openArticle(i){
  const p=PUBS[i]; if(!p) return;
  const color=colByName(p.cat);
  const paras=(p.body||"").split(/\n\s*\n/).map(t=>"<p>"+esc(t).replace(/\n/g,"<br>")+"</p>").join("");
  const src=p.url?'<p style="margin-top:8px"><a class="srclink" href="'+esc(p.url)+'" target="_blank" rel="noopener">Read the original source ↗</a></p>':"";
  const rel=PUBS.map((x,j)=>({x,j})).filter(o=>o.j!==i).slice(0,3).map(o=>
    '<button class="relcard" onclick="openArticle('+o.j+')"><div class="relimg" style="'+(o.x.image?("background-image:url('"+esc(o.x.image)+"')"):thumbCSS(o.j,colByName(o.x.cat)))+'"></div>'+
    '<div class="relb">'+catTag(o.x.cat||"Featured",colByName(o.x.cat))+'<div class="reltitle serif">'+esc(o.x.title)+'</div></div></button>').join("");
  document.getElementById("reader").innerHTML='<div class="rbox"><button class="rclose" onclick="closeArticle()">✕</button><div class="rinner">'+
    catTag(p.cat||"Featured",color)+'<h1 class="serif">'+esc(p.title)+'</h1>'+
    '<div class="rmeta"><span class="ravatar">A</span><div><div class="rauthor">AI Radar Desk</div><div class="rsub">AI Radar · '+fmtDate(p.ts)+'</div></div></div>'+
    '<div class="rimg" style="'+(p.image?("background-image:url('"+esc(p.image)+"')"):thumbCSS(i,color))+'"></div>'+
    '<div class="rbody serif">'+paras+src+'</div>'+
    (rel?'<div class="sec-h" style="margin-top:30px">Related Stories</div><div class="relgrid">'+rel+'</div>':'')+
    '</div></div>';
  const rd=document.getElementById("reader"); rd.hidden=false; rd.scrollTop=0; document.body.style.overflow="hidden";
  try{ history.replaceState(null,"","#a="+(p.id||"")); }catch(e){}
}
function closeArticle(){ document.getElementById("reader").hidden=true; document.body.style.overflow="";
  try{ history.replaceState(null,"",location.pathname+location.search); }catch(e){} }
document.getElementById("reader").addEventListener("click",e=>{ if(e.target.id==="reader") closeArticle(); });
/* deep link: radar.hafizahmad.com/#a=<id> opens that article (used by shares) */
function openArticleFromHash(){
  const m=(location.hash||"").match(/a=([^&]+)/); if(!m) return;
  const idx=PUBS.findIndex(p=>String(p.id)===m[1]); if(idx>=0) openArticle(idx);
}

/* ---- footer section links ---- */
function footerSections(){
  const el=document.getElementById("fsections");
  Object.entries(PILLARS).slice(0,8).forEach(([k,v])=>{ const b=document.createElement("button"); b.className="lk"; b.textContent=v;
    b.onclick=()=>{ pillar=+k; shown=PAGE; navBar(); render(); window.scrollTo({top:0,behavior:"smooth"}); }; el.appendChild(b); });
}

/* ---- static pages (About / Privacy / ...) in the reader ---- */
const PAGES={
  about:["About AI Radar",
    "<p>AI Radar is an independent publication that tracks the fast-moving world of artificial intelligence. Every 30 minutes we scan hundreds of trusted sources — company blogs, research labs, news outlets and developer communities — and surface the stories that matter, with a direct link to every original source.</p><p>Our goal is simple: help you stay first. AI Radar is created and edited by <a class='srclink' href='https://x.com/aixahmad' target='_blank' rel='noopener'>@aixahmad</a>.</p>"],
  how:["How AI Radar works",
    "<p><b>1. We collect.</b> Our system continuously pulls headlines from a wide list of AI sources around the clock.</p><p><b>2. We organise.</b> Stories are sorted into sections and de-duplicated, so a story covered by many outlets shows its source count.</p><p><b>3. We surface.</b> Trending topics and the most-covered stories rise to the top. Editor-picked features appear under the lead story.</p><p><b>4. You read.</b> Click any headline to go straight to the original publisher. The feed refreshes every 30 minutes, automatically.</p>"],
  editorial:["Editorial standards",
    "<p>AI Radar aggregates and curates; it does not alter the words of the original publishers. Headlines and short excerpts are shown for identification and always link back to the source.</p><p>Featured articles written by our team are based only on the underlying reporting — we do not fabricate facts, numbers or quotes. Corrections are made promptly; if you spot an error, please contact us.</p>"],
  advertise:["Advertise & partner",
    "<p>Interested in reaching an audience that lives and breathes AI? AI Radar offers sponsorships, newsletter placements and content partnerships.</p><p>Reach out at <a class='srclink' href='mailto:"+CONTACT+"'>"+CONTACT+"</a> or DM <a class='srclink' href='https://x.com/aixahmad' target='_blank' rel='noopener'>@aixahmad</a> on X.</p>"],
  contact:["Send a tip",
    "<p>Got a scoop, a launch, or a story we should be covering? We'd love to hear it.</p><p>Email <a class='srclink' href='mailto:"+CONTACT+"'>"+CONTACT+"</a> or message <a class='srclink' href='https://x.com/aixahmad' target='_blank' rel='noopener'>@aixahmad</a> on X. Tips can be sent confidentially.</p>"],
  privacy:["Privacy policy",
    "<p>AI Radar is built to respect your privacy. We do not require an account, we do not sell data, and we do not run invasive advertising trackers.</p><p>The site is served as static pages. Standard web-server logs may be collected by our hosting provider for security and aggregate analytics. External links take you to third-party sites with their own privacy policies. Questions? Email <a class='srclink' href='mailto:"+CONTACT+"'>"+CONTACT+"</a>.</p>"],
  terms:["Terms of use",
    "<p>AI Radar is provided \"as is\", for informational purposes only. While we work to keep the feed accurate and current, we make no warranty as to completeness or accuracy and accept no liability for decisions made based on its content.</p><p>Headlines, excerpts and trademarks belong to their respective owners. If you are a rights holder and would like a link or excerpt amended, contact <a class='srclink' href='mailto:"+CONTACT+"'>"+CONTACT+"</a>.</p>"],
  disclaimer:["Disclaimer",
    "<p>AI Radar is an independent news aggregator and is not affiliated with, endorsed by, or sponsored by any of the companies or publications whose stories it links to.</p><p>All product names, logos and brands are property of their respective owners. Content is aggregated automatically; the appearance of a source does not imply endorsement either way.</p>"],
};
function openPage(key){
  const p=PAGES[key]; if(!p) return;
  document.getElementById("reader").innerHTML='<div class="rbox"><button class="rclose" onclick="closeArticle()">✕</button>'+
    '<div class="rinner"><h1 class="serif">'+p[0]+'</h1><div class="rbody serif">'+p[1]+'</div></div></div>';
  const rd=document.getElementById("reader"); rd.hidden=false; rd.scrollTop=0; document.body.style.overflow="hidden";
}

/* ---- events + init ---- */
document.getElementById("q").addEventListener("input",e=>{ q=e.target.value.trim(); shown=PAGE; render(); });
document.getElementById("searchgo").onclick=()=>window.scrollTo({top:document.querySelector(".cols").offsetTop-70,behavior:"smooth"});
document.getElementById("more").onclick=()=>{ shown+=PAGE; render(); };
document.getElementById("fHot").onclick=()=>{ hotOnly=true; shown=PAGE;
  document.getElementById("fHot").classList.add("on"); document.getElementById("fLatest").classList.remove("on"); render(); };
document.getElementById("fLatest").onclick=()=>{ hotOnly=false; shown=PAGE;
  document.getElementById("fLatest").classList.add("on"); document.getElementById("fHot").classList.remove("on"); render(); };

const _qp=new URLSearchParams(location.search).get("q");
if(_qp){ q=_qp.trim(); document.getElementById("q").value=q; }
renderTicker(); navBar(); trendsBar(); renderHero(); render(); renderResearch(); renderTrending(); renderTools(); footerSections(); loadFeatured();
</script>
</body>
</html>
"""


def generate():
    conn = database.connect()
    rows = conn.execute(
        "SELECT id, title, url, links, source, pillar, published, fetched FROM items "
        "ORDER BY fetched DESC, COALESCE(published, fetched) DESC LIMIT ?", (MAX_STORIES,)
    ).fetchall()
    trends = scoring.compute_trends(conn)
    chips = [t for t in trends if t["status"] in ("new", "rising")][:8]
    conn.close()

    items = [{
        "t": r["title"], "u": r["url"], "s": r["source"], "p": r["pillar"],
        "d": r["published"] or r["fetched"], "l": json.loads(r["links"] or "[]"),
    } for r in rows]

    updated = datetime.now(timezone.utc).strftime("%d %b, %H:%M UTC")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # --- structured data (helps Google understand the site) ---
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "name": SITE_NAME, "url": SITE_URL, "description": SITE_DESC,
         "inLanguage": "en",
         "potentialAction": {"@type": "SearchAction",
                             "target": {"@type": "EntryPoint",
                                        "urlTemplate": SITE_URL + "?q={search_term_string}"},
                             "query-input": "required name=search_term_string"}},
        {"@type": "NewsMediaOrganization", "name": SITE_NAME, "url": SITE_URL,
         "logo": {"@type": "ImageObject", "url": SITE_URL + "favicon.svg"},
         "email": CONTACT_EMAIL,
         "sameAs": ["https://x.com/aixahmad", "https://youtube.com/@aixahmad"]},
    ]}
    gsc = (f'<meta name="google-site-verification" content="{GSC_VERIFY}">'
           if GSC_VERIFY else "")

    html = (PAGE
            .replace("__SITE__", SITE_NAME)
            .replace("__URL__", SITE_URL)
            .replace("__DESC__", _h.escape(SITE_DESC, quote=True))
            .replace("__GSC__", gsc)
            .replace("__JSONLD__", json.dumps(jsonld, ensure_ascii=False))
            .replace("__PILLARS__", json.dumps(config.CATEGORIES))
            .replace("__ITEMS__", json.dumps(items, ensure_ascii=False))
            .replace("__TRENDS__", json.dumps(chips, ensure_ascii=False))
            .replace("__COLORS__", json.dumps(CATCOLORS))
            .replace("__FBURL__", _load_fburl())
            .replace("__EMAIL__", CONTACT_EMAIL)
            .replace("__UPDATED__", updated))

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # robots.txt — let crawlers in, keep the private studio out, point to sitemap
    with open(os.path.join(OUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\nDisallow: /studio.html\n\n"
                f"Sitemap: {SITE_URL}sitemap.xml\n")

    # sitemap.xml — tells Google the homepage exists and changes often
    with open(os.path.join(OUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                f'  <url><loc>{SITE_URL}</loc><lastmod>{today}</lastmod>'
                '<changefreq>hourly</changefreq><priority>1.0</priority></url>\n'
                '</urlset>\n')

    print(f"Public site written: docs/index.html ({len(items)} stories) + robots.txt + sitemap.xml")


if __name__ == "__main__":
    generate()
