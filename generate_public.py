"""
AI Radar - PUBLIC news website generator (warm editorial design).

Reads news.db and writes docs/index.html: a paper-and-ink AI news edition with
a radar illustration, source-first headlines, collection freshness, topic and
publisher search, coverage ranking, a browser-local reading list and an
accessible article reader. Editor-published articles (from Firebase /published)
become the hero and related stories. The private studio is generated separately
to docs/studio.html.

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


def _script_json(value):
    """Keep feed text inside its JSON script context, even with HTML-like titles."""
    return (json.dumps(value, ensure_ascii=False)
            .replace("<", "\\u003c").replace(">", "\\u003e")
            .replace("&", "\\u0026").replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029"))


OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
MAX_STORIES = 600
SITE_NAME = "AI Radar"
# The address where the site is actually served. Canonical/OG/sitemap all use
# this — it MUST match the live URL or Google won't index correctly.
SITE_URL = "https://ahmad19sep.github.io/ai-news-updater/"
# Paste the Google Search Console "HTML tag" verification code here, then re-run.
GSC_VERIFY = ""
SITE_DESC = ("Explore artificial-intelligence news, models, tools and research. "
             "Browse by topic, compare source coverage and save stories for later, "
             "with direct links to the original publishers.")
CONTACT_EMAIL = "get.shahzadsaddique@gmail.com"

# section kicker colours, keyed by category id — chosen for strong contrast on
# a white background (used as small uppercase labels, like a newspaper kicker).
CATCOLORS = {1: "#245485", 2: "#655084", 3: "#315f8c", 4: "#32637b", 5: "#806424",
             6: "#4f5883", 7: "#416440", 8: "#974761", 9: "#655484", 10: "#526053"}

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#ffffff">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link rel="apple-touch-icon" href="favicon.svg">
<title>__SITE__ — AI news, tools and research</title>
<meta name="description" content="__DESC__">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="keywords" content="AI news, artificial intelligence news, AI models, AI tools, machine learning news, LLM, ChatGPT, generative AI, AI research">
<meta name="author" content="AI Radar">
<link rel="canonical" href="__URL__">
__GSC__
<meta property="og:site_name" content="__SITE__">
<meta property="og:title" content="__SITE__ — AI news, tools and research">
<meta property="og:description" content="__DESC__">
<meta property="og:type" content="website">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="__URL__">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@aixahmad">
<meta name="twitter:title" content="__SITE__ — AI news, tools and research">
<meta name="twitter:description" content="__DESC__">
<script type="application/ld+json">__JSONLD__</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,500&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#ffffff;--bg2:#f7f7f4;--paper:#fbfbf9;
    --ink:#11151a;--ink2:#2a2f36;--mid:#56606b;--dim:#8b939d;
    --line:#e4e3df;--line2:#d4d3ce;
    --red:#c8102e;--green:#1a7f37;
    --serif:'Newsreader',Georgia,'Times New Roman',serif;
    --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
    --mono:ui-monospace,'SF Mono',Menlo,Consolas,monospace;
  }
  *{box-sizing:border-box;}
  html,body{margin:0;padding:0;}
  body{background:var(--bg);color:var(--ink);font-family:var(--sans);-webkit-font-smoothing:antialiased;}
  a{color:inherit;text-decoration:none;}
  button{font-family:inherit;color:inherit;}
  input{font-family:inherit;}
  .serif{font-family:var(--serif);}
  .mono{font-family:var(--mono);}
  ::selection{background:#ffe58a;}
  @keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
  .wrap{max-width:1200px;margin:0 auto;padding:22px 22px 20px;width:100%;}

  /* breaking strip */
  .ticker{display:flex;align-items:center;gap:14px;background:#fff;border-bottom:1px solid var(--line);padding:8px 22px;overflow:hidden;}
  .ticker .bk{display:inline-flex;align-items:center;gap:7px;flex:none;background:var(--red);color:#fff;font-size:10.5px;font-weight:800;letter-spacing:.09em;padding:3px 9px;border-radius:3px;}
  .ticker .bk .d{width:6px;height:6px;border-radius:50%;background:#fff;animation:blink 1.1s infinite;}
  .tkrow{display:flex;align-items:center;gap:24px;overflow:hidden;flex:1;min-width:0;}
  .tk{display:inline-flex;align-items:center;gap:9px;font-size:12.5px;color:var(--ink2);white-space:nowrap;}
  .tk .dot{width:3px;height:3px;border-radius:50%;background:var(--red);}
  .tklive{flex:none;font-size:11px;color:var(--dim);letter-spacing:.04em;}
  @media(max-width:760px){.ticker .tklive{display:none}}

  /* masthead */
  header.mast{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.94);backdrop-filter:blur(10px);border-bottom:1px solid var(--line2);}
  .mastrow{display:flex;align-items:center;gap:18px;padding:14px 22px;max-width:1200px;margin:0 auto;}
  .brand{display:inline-flex;align-items:center;gap:10px;flex:none;}
  .orb{position:relative;width:30px;height:30px;border-radius:7px;background:#11151a;display:flex;align-items:center;justify-content:center;}
  .brand .nm{font-family:var(--serif);font-size:24px;font-weight:700;letter-spacing:-.01em;color:var(--ink);}
  .brand .nm b{font-weight:700;color:var(--ink);}
  nav.cats{flex:1;min-width:0;display:flex;align-items:center;gap:2px;overflow-x:auto;padding:0 4px;scrollbar-width:none;}
  nav.cats::-webkit-scrollbar{display:none;}
  nav.cats button{flex:none;border:none;background:transparent;color:var(--ink2);font-size:13.5px;font-weight:500;padding:8px 11px;border-radius:6px;cursor:pointer;white-space:nowrap;}
  nav.cats button:hover{color:#000;background:var(--bg2);}
  nav.cats button.active{color:#000;font-weight:700;box-shadow:inset 0 -2px 0 var(--red);}
  .mright{flex:none;display:flex;align-items:center;gap:8px;}
  .mright a{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border:1px solid var(--line2);border-radius:7px;color:var(--ink2);font-size:14px;}
  .mright a:hover{border-color:var(--ink);color:#000;}
  @media(max-width:900px){nav.cats{order:3;flex-basis:100%;border-top:1px solid var(--line);padding-top:6px;}}

  /* hero */
  .herogrid{display:grid;grid-template-columns:1.62fr 1fr;gap:34px;align-items:start;padding-top:6px;}
  @media(max-width:900px){.herogrid{grid-template-columns:1fr;gap:6px;}}
  .lead{display:block;width:100%;text-align:left;border:none;background:none;padding:0 0 6px;cursor:pointer;color:var(--ink);}
  .limg{position:relative;width:100%;aspect-ratio:16/9;border-radius:3px;background-size:cover;background-position:center;border:1px solid var(--line);}
  .lbody{padding-top:14px;}
  .lbadges{display:flex;align-items:center;gap:12px;margin-bottom:9px;flex-wrap:wrap;}
  .leadbadge{display:inline-flex;align-items:center;gap:6px;color:var(--red);font-size:10.5px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;}
  .leadbadge .dot{width:6px;height:6px;border-radius:50%;background:var(--red);animation:blink 1.1s infinite;}
  .lead h1{font-family:var(--serif);font-size:clamp(26px,3.1vw,40px);line-height:1.07;font-weight:700;letter-spacing:-.012em;margin:0 0 11px;color:var(--ink);}
  .lead:hover h1{text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:1px;}
  .ldek{font-size:15.5px;line-height:1.55;color:var(--mid);margin:0 0 13px;max-width:620px;}
  .lmeta{display:flex;align-items:center;gap:9px;font-size:12.5px;color:var(--dim);}
  .src{color:var(--ink2);font-weight:600;}

  .sidestack{display:flex;flex-direction:column;}
  .scardx{display:block;width:100%;text-align:left;border:none;background:none;cursor:pointer;color:var(--ink);padding:16px 0;border-top:1px solid var(--line);}
  .sidestack .scardx:first-child{border-top:none;padding-top:2px;}
  .stitle{font-family:var(--serif);font-size:18.5px;line-height:1.2;font-weight:600;color:var(--ink);margin:7px 0 7px;}
  .scardx:hover .stitle{text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:1px;}
  .smeta{font-size:12px;color:var(--dim);}

  .cat{display:inline-block;font-family:var(--sans);font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;}

  /* status + chips */
  .statusrow{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:26px 0 0;padding:14px 0;border-top:1px solid var(--line2);border-bottom:1px solid var(--line);}
  .statusrow .live{display:inline-flex;align-items:center;gap:8px;font-family:var(--mono);font-size:11px;letter-spacing:.03em;color:var(--mid);}
  .statusrow .live .d{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 0 3px rgba(26,127,55,.16);}
  .chips{margin-left:auto;display:flex;gap:7px;flex-wrap:wrap;}
  .chip{border:1px solid var(--line2);background:#fff;color:var(--ink2);font-size:11.5px;font-weight:500;padding:5px 11px;border-radius:18px;cursor:pointer;}
  .chip:hover{border-color:var(--ink);color:#000;}

  /* search */
  .searchrow{display:flex;gap:10px;margin:18px 0 30px;}
  .searchbox{flex:1;display:flex;align-items:center;gap:11px;border:1px solid var(--line2);background:#fff;border-radius:8px;padding:0 14px;}
  .searchbox:focus-within{border-color:var(--ink);}
  .searchbox svg{flex:none;}
  .searchbox input{flex:1;border:none;background:transparent;outline:none;color:var(--ink);font-size:14px;padding:13px 0;}
  .searchbtn{border:none;background:#11151a;color:#fff;font-size:13px;font-weight:600;padding:0 20px;border-radius:8px;cursor:pointer;flex:none;}
  .searchbtn:hover{background:#000;}

  /* two columns */
  .cols{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:42px;align-items:start;}
  @media(max-width:980px){.cols{grid-template-columns:1fr;gap:30px;}}
  .sec-h{display:flex;align-items:center;gap:10px;font-family:var(--sans);font-size:13px;font-weight:800;letter-spacing:.07em;text-transform:uppercase;color:var(--ink);margin:0 0 6px;padding-top:11px;border-top:2px solid var(--ink);}
  .sec-h .bar{display:none;}
  .feedtop{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:4px;}
  .feedtop .fb{display:flex;gap:6px;}
  .feedtop .fb button{border:1px solid var(--line2);background:#fff;color:var(--mid);font-size:11.5px;font-weight:600;padding:5px 12px;border-radius:6px;cursor:pointer;}
  .feedtop .fb button.on{border-color:var(--ink);background:var(--ink);color:#fff;}
  .count{font-size:12px;color:var(--dim);margin:10px 0 0;}

  .feed{display:flex;flex-direction:column;margin-top:4px;}
  .vrow{padding:19px 0;border-bottom:1px solid var(--line);}
  .vmain{min-width:0;}
  .vtop{display:flex;align-items:center;gap:11px;margin-bottom:8px;}
  .hotsrc{display:inline-flex;align-items:center;gap:5px;font-size:10.5px;font-weight:700;color:var(--red);text-transform:uppercase;letter-spacing:.04em;}
  .hotsrc .pip{width:5px;height:5px;border-radius:50%;background:var(--red);}
  .vtitle{display:block;font-family:var(--serif);font-size:21px;line-height:1.22;font-weight:600;letter-spacing:-.01em;color:var(--ink);}
  .vtitle:hover{text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:1px;}
  .vmeta{display:flex;align-items:center;gap:9px;margin-top:10px;font-size:12px;color:var(--dim);}
  .savebtn{display:inline-flex;align-items:center;gap:5px;margin-left:auto;border:none;background:transparent;color:var(--dim);font-size:11.5px;font-weight:600;cursor:pointer;}
  .savebtn:hover{color:var(--ink);}
  .savebtn.on{color:var(--red);}
  @media(max-width:560px){.vtitle{font-size:18px;}}
  .more{display:block;margin:28px auto 0;border:1px solid var(--ink);background:#fff;color:var(--ink);font-size:13px;font-weight:700;padding:11px 26px;border-radius:8px;cursor:pointer;}
  .more:hover{background:var(--ink);color:#fff;}
  .empty{color:var(--dim);text-align:center;padding:48px 0;}

  /* research grid */
  .rgrid{display:grid;grid-template-columns:1fr 1fr;gap:0 28px;}
  @media(max-width:560px){.rgrid{grid-template-columns:1fr;}}
  .rcard{text-align:left;border:none;border-top:1px solid var(--line);background:none;padding:16px 0;cursor:pointer;color:var(--ink);}
  .rlabel{font-size:10.5px;font-weight:800;letter-spacing:.06em;color:#8A3FFC;text-transform:uppercase;}
  .rtitle{font-family:var(--serif);font-size:16.5px;line-height:1.25;font-weight:600;margin:8px 0 9px;}
  .rcard:hover .rtitle{text-decoration:underline;text-underline-offset:3px;}
  .rmeta{font-size:11.5px;color:var(--dim);}

  /* sidebar */
  .aside{display:flex;flex-direction:column;gap:30px;position:sticky;top:84px;}
  @media(max-width:980px){.aside{position:static;}}
  .sblock{}
  .shead{display:flex;align-items:center;gap:8px;font-family:var(--sans);font-size:13px;font-weight:800;letter-spacing:.07em;text-transform:uppercase;color:var(--ink);margin-bottom:4px;padding-top:11px;border-top:2px solid var(--ink);}
  .trow{display:flex;gap:13px;width:100%;border:none;background:transparent;text-align:left;cursor:pointer;padding:13px 0;border-top:1px solid var(--line);color:var(--ink);}
  .trow:hover .ttitle{text-decoration:underline;text-underline-offset:3px;}
  .trank{font-family:var(--serif);font-size:22px;font-weight:700;flex:none;width:24px;line-height:1;}
  .ttitle{font-family:var(--serif);font-size:15px;line-height:1.26;font-weight:600;}
  .tmeta{font-size:11px;color:var(--dim);margin-top:5px;}
  .toolrow2{display:flex;align-items:center;gap:12px;width:100%;border:none;background:transparent;text-align:left;cursor:pointer;padding:12px 0;border-top:1px solid var(--line);color:var(--ink);}
  .toolrow2:hover .tname{text-decoration:underline;text-underline-offset:3px;}
  .ticon{width:36px;height:36px;border-radius:8px;flex:none;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;color:#fff;}
  .tname{font-size:13.5px;font-weight:600;line-height:1.25;color:var(--ink);}
  .ttag{font-size:11.5px;color:var(--dim);margin-top:3px;}
  .briefcard{border:1px solid var(--line2);background:var(--bg2);border-radius:10px;padding:20px 18px;}
  .briefh{font-family:var(--serif);font-size:20px;font-weight:700;line-height:1.18;margin-bottom:7px;}
  .briefcard p{font-size:13px;line-height:1.5;color:var(--mid);margin:0 0 14px;}
  .bbtn,.bbtn2{display:block;text-align:center;font-size:13px;font-weight:600;padding:11px;border-radius:7px;margin-bottom:8px;}
  .bbtn{background:#11151a;color:#fff;}
  .bbtn:hover{background:#000;}
  .bbtn2{border:1px solid var(--line2);color:var(--ink);}
  .bbtn2:hover{border-color:var(--ink);}
  .bfoot{font-size:11px;color:var(--dim);margin-top:4px;}

  /* footer */
  footer{border-top:3px solid var(--ink);background:var(--bg2);margin-top:54px;}
  .ftop{display:flex;flex-wrap:wrap;gap:32px;max-width:1200px;margin:0 auto;padding:40px 22px 20px;}
  .fbrand{flex:1 1 280px;min-width:240px;}
  .fbrand .brand{margin-bottom:13px;}
  .fbrand p{font-size:13px;line-height:1.6;color:var(--mid);max-width:320px;margin:0 0 14px;}
  .fsoc{display:flex;gap:8px;}
  .fsoc a{width:34px;height:34px;border:1px solid var(--line2);border-radius:7px;display:flex;align-items:center;justify-content:center;color:var(--ink2);font-size:14px;background:#fff;}
  .fsoc a:hover{border-color:var(--ink);color:#000;}
  .fcol{flex:1 1 150px;}
  .fcol h4{font-size:11px;font-weight:800;letter-spacing:.07em;color:var(--dim);margin:0 0 13px;text-transform:uppercase;}
  .fcol a,.fcol .lk{display:block;font-size:13px;color:var(--ink2);padding:5px 0;cursor:pointer;background:none;border:none;text-align:left;font-family:inherit;}
  .fcol a:hover,.fcol .lk:hover{color:var(--red);}
  .fbot{display:flex;flex-wrap:wrap;gap:10px;justify-content:space-between;align-items:center;border-top:1px solid var(--line2);max-width:1200px;margin:0 auto;padding:18px 22px 30px;font-size:11.5px;color:var(--dim);}
  .fbot .legal{display:flex;gap:14px;}
  .fbot .legal button{background:none;border:none;color:var(--dim);cursor:pointer;font:inherit;}
  .fbot .legal button:hover{color:var(--red);}

  /* reader = full-page article view (NYT style) */
  #reader{position:fixed;inset:0;z-index:80;background:#fff;overflow-y:auto;}
  .rbox{max-width:none;margin:0;background:#fff;border:none;border-radius:0;padding:0 0 72px;}
  .rtopbar{position:sticky;top:0;z-index:3;display:flex;align-items:center;gap:14px;background:rgba(255,255,255,.95);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);padding:11px 22px;}
  .rback{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--line2);background:#fff;color:var(--ink);font-size:13px;font-weight:600;padding:8px 14px;border-radius:7px;cursor:pointer;}
  .rback:hover{border-color:var(--ink);}
  .rtopbar .brand{margin:0 auto;}
  .rtopbar .brand .nm{font-size:20px;}
  .rtopbar .spacer{width:92px;flex:none;}
  @media(max-width:560px){.rtopbar .spacer{display:none;}.rtopbar .brand{margin-left:auto;}}
  .rinner{max-width:720px;margin:0 auto;padding:34px 22px 0;}
  .rbox h1{font-family:var(--serif);font-size:clamp(30px,4.4vw,48px);line-height:1.06;font-weight:700;letter-spacing:-.018em;margin:12px 0 16px;color:var(--ink);}
  .rmeta{display:flex;align-items:center;gap:11px;padding:16px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);}
  .ravatar{width:42px;height:42px;border-radius:50%;background:var(--ink);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;color:#fff;flex:none;}
  .rauthor{font-size:13.5px;font-weight:700;}
  .rsub{font-size:11.5px;color:var(--dim);}
  .rhero{max-width:1040px;margin:26px auto 0;padding:0 22px;}
  .rimg{aspect-ratio:16/9;border-radius:4px;border:1px solid var(--line);background-size:cover;background-position:center;}
  .rcap{font-size:12px;color:var(--dim);margin:9px 2px 0;}
  .rbody{font-family:var(--serif);font-size:19px;line-height:1.72;color:#23272d;}
  .rbody p{margin:0 0 22px;}
  .srclink{color:var(--red);font-family:var(--sans);font-size:14px;font-weight:600;}
  .srclink:hover{text-decoration:underline;}
  .relgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:22px;}
  .relcard{text-align:left;border:none;border-top:1px solid var(--line);background:none;cursor:pointer;padding:14px 0 0;color:var(--ink);}
  .reltitle{font-family:var(--serif);font-size:15.5px;line-height:1.25;font-weight:600;margin-top:8px;}
  .relcard:hover .reltitle{text-decoration:underline;text-underline-offset:3px;}

  /* A calmer editorial identity: paper, ink, and a single warm accent. */
  :root{--bg:#f5f3ee;--bg2:#eeece5;--paper:#fffefa;--ink:#222620;--ink2:#353b34;--mid:#5b6259;--dim:#626960;--line:#deded4;--line2:#cecec1;--red:#b44321;--green:#466347;}
  html{scroll-behavior:smooth;scroll-padding-top:150px;}
  body{font-size:14px;line-height:1.5;}
  [hidden]{display:none!important;}
  button,a,input{touch-action:manipulation;}
  button{cursor:pointer;}
  :focus-visible{outline:3px solid #b44321;outline-offset:4px;border-radius:3px;}
  a,button,input{ -webkit-tap-highlight-color:transparent; }
  .skip{position:fixed;top:10px;left:16px;z-index:100;background:var(--ink);color:#fff;padding:12px 18px;border-radius:8px;transform:translateY(-180%);}
  .skip:focus{transform:translateY(0);}
  .sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0;}
  .wrap{max-width:1240px;padding:28px 32px 20px;}
  .ticker{background:var(--ink);color:#f7f6f0;border:0;padding:9px max(24px,calc((100vw - 1176px)/2));gap:16px;}
  .ticker .bk{background:transparent;color:#e9a58b;padding:0;font-size:10px;letter-spacing:.14em;}
  .ticker .bk .d{background:#e9a58b;animation:none;}
  .tkrow{gap:30px;}
  .tk{color:#e6e7df;font-size:11px;}
  .tk .dot{background:#b7bcaa;}
  .tklive{color:#c6cbbe;font-size:10px;}
  header.mast{background:rgba(245,243,238,.96);border-color:var(--line2);}
  .mastrow{max-width:1240px;flex-wrap:wrap;padding:17px 32px 11px;gap:8px 20px;}
  .brand{gap:11px;}
  .orb{background:var(--red);border-radius:50%;width:33px;height:33px;}
  .brand .nm{font-size:28px;letter-spacing:-.05em;}
  .brandnote{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--mid);border-left:1px solid var(--line2);padding-left:20px;margin-right:auto;}
  nav.cats{order:3;flex-basis:100%;border-top:1px solid var(--line);margin-top:7px;padding:9px 0 0;gap:4px;}
  nav.cats button{font-size:12px;padding:8px 12px;min-height:38px;border-radius:5px;color:var(--mid);}
  nav.cats button.active{background:var(--ink);color:#fff;box-shadow:none;}
  nav.cats button:hover{background:#e7e5dd;color:var(--ink);}
  nav.cats button.active:hover{background:var(--ink);color:#fff;}
  .mright a{width:36px;height:36px;background:var(--paper);border-radius:50%;font-size:12px;}
  .edition{display:flex;justify-content:space-between;align-items:flex-end;gap:30px;margin-bottom:28px;}
  .eyebrow{font-size:10px;color:var(--red);font-weight:800;letter-spacing:.14em;text-transform:uppercase;display:flex;align-items:center;gap:8px;}
  .eyebrow:before{content:'';width:18px;height:1px;background:currentColor;}
  .edition h1{font-family:var(--serif);font-size:clamp(32px,4vw,48px);line-height:1.08;letter-spacing:-.035em;font-weight:500;margin:8px 0;}
  .edition p{margin:0;color:var(--mid);font-size:13px;max-width:580px;}
  .editionmeta{text-align:right;min-width:150px;}
  .editiondate{font-size:12px;font-weight:600;margin-bottom:5px;}
  .editionnote{font-size:10px;color:var(--mid);}
  .herogrid{grid-template-columns:minmax(0,1.7fr) minmax(0,1fr);gap:28px;padding:0;}
  .lead{position:relative;isolation:isolate;background:#25372e;color:#fffdf4;border-radius:14px;padding:28px;min-height:342px;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden;text-align:left;}
  .lead.has-image{padding:0;background:var(--paper);color:var(--ink);}
  .lead:after{content:'';position:absolute;width:380px;height:380px;border-radius:50%;border:1px solid rgba(194,211,178,.14);box-shadow:0 0 0 45px rgba(194,211,178,.035),0 0 0 90px rgba(194,211,178,.025);right:-170px;top:-230px;z-index:-1;}
  .leadviz{display:flex;align-items:center;gap:12px;color:#bbcabb;font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;margin-bottom:32px;}
  .radar-mark{width:40px;height:40px;border:1px solid #789782;border-radius:50%;position:relative;display:flex;align-items:center;justify-content:center;flex:none;}
  .radar-mark:before{content:'';width:22px;height:22px;border:1px solid #789782;border-radius:50%;}
  .radar-mark:after{content:'';position:absolute;width:18px;height:1px;background:#c6dbba;transform-origin:left;transform:rotate(-40deg);left:20px;top:19px;}
  .limg{border-radius:14px 14px 0 0;aspect-ratio:2/1;border:0;object-fit:cover;display:block;height:auto;width:100%;}
  .lbody{padding-top:0;}
  .has-image .lbody{padding:23px 25px;}
  .lead h2{font-family:var(--serif);font-size:clamp(26px,3vw,38px);line-height:1.11;letter-spacing:-.015em;font-weight:500;margin:12px 0 18px;color:inherit;}
  .lead:hover h2{text-decoration:underline;text-underline-offset:5px;text-decoration-thickness:1px;}
  .lead .cat{color:#e5bb99!important;}
  .lead.has-image .cat{color:var(--red)!important;}
  .leadbadge{color:#c4d3bb;font-size:9px;letter-spacing:.1em;}
  .leadbadge .dot{display:none;}
  .ldek{color:#e5ebdf;font-size:14px;}
  .has-image .ldek{color:var(--mid);}
  .lmeta{font-size:11px;color:#c4d3bb;flex-wrap:wrap;}
  .lead .src{color:#edf2e6;}
  .has-image .lmeta,.has-image .src{color:var(--mid);}
  .sourcearrow{margin-left:auto;color:inherit;font-size:12px;}
  .sidestack{padding:0 0 0 3px;}
  .stacklabel{font-size:10px;text-transform:uppercase;letter-spacing:.11em;color:var(--mid);margin-bottom:9px;}
  .scardx{padding:16px 0;min-width:0;}
  .sidestack .scardx:first-child{border-top:none;}
  .stitle{font-size:19px;line-height:1.2;font-weight:500;margin:7px 0 9px;}
  .cat{font-size:9px;letter-spacing:.1em;}
  .smeta{font-size:10.5px;}
  .statusrow{margin:28px 0 0;padding:16px 0;gap:15px;}
  .statusrow .live{font-family:var(--sans);font-size:11px;letter-spacing:0;flex-wrap:wrap;}
  .statusrow .live .d{box-shadow:none;width:6px;height:6px;}
  .statusrow.stale .live .d{background:#b44321;}
  .statusrow.stale .live{color:#974223;}
  .chips{gap:6px;}
  .chip{background:var(--paper);font-size:10px;min-height:32px;padding:5px 10px;}
  .chip.active{background:var(--ink);color:#fff;border-color:var(--ink);}
  .searchrow{margin:20px 0 28px;gap:8px;}
  .searchbox{background:var(--paper);border-radius:9px;min-width:0;}
  .searchbox input{min-width:0;font-size:13px;padding:13px 0;}
  .searchbtn{background:var(--ink);font-size:12px;padding:0 22px;}
  .cols{grid-template-columns:minmax(0,1fr) 290px;gap:42px;}
  .feedtop{gap:12px;align-items:center;flex-wrap:wrap;border-top:2px solid var(--ink);padding-top:14px;margin-bottom:5px;}
  .sec-h{font-family:var(--serif);font-size:23px;font-weight:500;text-transform:none;letter-spacing:-.02em;border-top:0;padding-top:0;}
  .feedtop .fb{background:#e7e6dd;border:1px solid var(--line);border-radius:7px;padding:3px;gap:2px;flex-wrap:wrap;}
  .feedtop .fb button{font-size:10px;min-height:30px;padding:4px 10px;background:transparent;border:0;border-radius:4px;}
  .feedtop .fb button.on{background:var(--paper);color:var(--ink);box-shadow:0 1px 3px #22262015;}
  .count{font-size:11px;color:var(--mid);min-height:20px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
  .resetfilters{font-size:11px;border:0;background:none;color:var(--red);padding:5px 0;min-height:28px;text-decoration:underline;text-underline-offset:3px;}
  .vrow{padding:22px 0;}
  .vtop{gap:12px;margin-bottom:9px;flex-wrap:wrap;}
  .vtitle{font-size:24px;font-weight:500;line-height:1.2;}
  .vmeta{font-size:11px;flex-wrap:wrap;gap:8px;margin-top:12px;}
  .savebtn{font-size:10px;min-height:32px;padding:5px 7px;border:1px solid transparent;border-radius:5px;}
  .savebtn:hover{background:var(--bg2);border-color:var(--line);}
  .savebtn.on{color:var(--red);background:#f4e4d9;}
  .hotsrc{color:#476347;font-size:9px;letter-spacing:.02em;font-weight:600;background:#e7ebe1;border-radius:4px;padding:3px 6px;}
  .hotsrc .pip{background:currentColor;}
  .more{background:var(--paper);border-color:var(--line2);border-radius:7px;font-size:12px;padding:12px 22px;}
  .empty{border:1px dashed var(--line2);border-radius:10px;margin:20px 0;padding:38px 20px;color:var(--mid);}
  .empty strong{display:block;font-family:var(--serif);font-size:25px;font-weight:500;color:var(--ink);margin-bottom:8px;}
  .empty p{font-size:12px;margin:0 0 12px;}
  .aside{top:160px;gap:24px;}
  .sblock{background:var(--paper);border:1px solid var(--line);border-radius:11px;padding:18px;}
  .shead{border:0;padding:0 0 10px;margin:0;font-size:10px;letter-spacing:.12em;}
  .trow{padding:13px 0;gap:11px;}
  .trow:last-child,.toolrow2:last-child{padding-bottom:0;}
  .trank{font-size:23px;color:var(--mid)!important;font-weight:400;}
  .ttitle{font-size:16px;font-weight:500;}
  .tmeta{font-size:10px;}
  .ticon{background:#e8ede3!important;color:#466347;width:32px;height:32px;border:1px solid #d8dfcf;font-size:12px;border-radius:7px;}
  .tname{font-size:12px;font-weight:500;}
  .ttag{font-size:10px;}
  .briefcard{position:relative;overflow:hidden;background:#ece9dc;padding:24px;border:0;border-radius:11px;}
  .briefh{font-size:26px;font-weight:500;letter-spacing:-.02em;}
  .briefcard p{font-size:12px;line-height:1.65;}
  .bbtn,.bbtn2{font-size:11px;margin-bottom:8px;min-height:38px;}
  .bbtn{background:var(--ink);}
  .bfoot{font-size:10px;}
  .trustnote{border-top:1px solid var(--line2);padding-top:15px;color:var(--mid);font-size:11px;line-height:1.7;}
  .trustnote strong{display:block;font-size:10px;color:var(--ink);letter-spacing:.08em;text-transform:uppercase;margin-bottom:5px;}
  .trustnote button{font-size:11px;border:0;background:none;text-decoration:underline;text-underline-offset:3px;padding:4px 0;color:var(--red);}
  footer{background:#eeece4;border-top:1px solid var(--line2);margin-top:64px;}
  .ftop,.fbot{max-width:1240px;padding-left:32px;padding-right:32px;}
  .fbrand p{font-size:12px;}
  .fcol a,.fcol .lk{font-size:12px;min-height:32px;overflow-wrap:anywhere;}
  .fbot{font-size:10px;}
  .fbot .legal button{padding:5px;min-height:30px;}
  .fsoc a{background:var(--paper);border-radius:50%;}
  #reader,.rbox{background:var(--bg);}
  .rtopbar{background:rgba(245,243,238,.96);}
  .rbody{font-size:20px;}
  .rimg{display:block;width:100%;height:auto;object-fit:cover;}
  .rbody a{overflow-wrap:anywhere;}
  .rmeta{flex-wrap:wrap;}
  .rsub{font-size:11px;}
  #researchwrap{padding-top:10px;}
  .rlabel{color:#615688;}
  @media(max-width:1000px){.cols{grid-template-columns:minmax(0,1fr) 260px;gap:26px;}.edition h1{font-size:39px;}}
  @media(max-width:900px){.herogrid{grid-template-columns:1.3fr 1fr;gap:24px;}.lead{padding:23px;min-height:345px;}.lead h2{font-size:30px;}.cols{grid-template-columns:1fr;}.aside{position:static;display:grid;grid-template-columns:1fr 1fr;gap:20px;}.trustnote{align-self:start;}.mastrow{gap:8px 15px;}}
  @media(max-width:640px){.wrap{padding:23px 20px 10px;}.mastrow{padding:13px 20px 9px;}.brandnote{display:none;}.mright{margin-left:auto;}nav.cats{margin-top:5px;padding-top:8px;}.edition{display:block;margin-bottom:23px;}.edition h1{font-size:36px;}.editionmeta{text-align:left;margin-top:13px;}.editiondate{font-size:10px;margin-bottom:1px;}.editionnote{display:none;}.herogrid{grid-template-columns:1fr;gap:20px;}.lead{min-height:290px;padding:23px;}.lead h2{font-size:31px;}.leadviz{margin-bottom:20px;}.sidestack{padding:0;}.scardx{padding:13px 0;}.stitle{font-size:20px;}.statusrow{margin-top:20px;gap:10px;}.chips{margin-left:0;width:100%;}.statusrow .live{font-size:10px;}.searchrow{margin:18px 0 24px;}.searchbtn{padding:0 15px;}.searchbox{gap:8px;padding:0 12px;}.searchbox input{font-size:12px;}.vtitle{font-size:22px;}.vmeta{font-size:10px;}.aside{grid-template-columns:1fr;}.aside .sblock{padding:20px;}.briefcard{padding:25px;}.ftop{padding:28px 20px 10px;gap:25px;}.fbot{padding:16px 20px 24px;}.ticker{padding:8px 20px;}.ticker .bk{font-size:9px;}.tk{font-size:10px;}.feedtop{align-items:flex-start;}.feedtop .sec-h{font-size:25px;}.feedtop .fb{margin-bottom:5px;}.rinner{padding-left:20px;padding-right:20px;}.rbody{font-size:19px;}.rbox h1{font-size:34px;}.rback{min-height:38px;}}
  @media(prefers-reduced-motion:reduce){html{scroll-behavior:auto;}*,*:before,*:after{animation:none!important;transition:none!important;}}
</style>
</head>
<body>
<a class="skip" href="#feed-start">Skip to the news feed</a>

<div class="ticker">
  <span class="bk"><span class="d"></span>ON THE RADAR</span>
  <div class="tkrow" id="ticker"></div>
  <span class="tklive mono">INDEPENDENT AI NEWS</span>
</div>

<header class="mast">
  <div class="mastrow">
    <a class="brand" href="./" aria-label="AI Radar home"><span class="orb" aria-hidden="true">
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"></circle><path d="M12 12L19 8"></path><circle cx="12" cy="12" r="2" fill="#fff" stroke="none"></circle></svg>
    </span><span class="nm">AI <b>Radar</b></span></a>
    <span class="brandnote">A clearer view of artificial intelligence</span>
    <nav class="cats" id="nav" aria-label="News topics"></nav>
    <div class="mright">
      <a href="https://x.com/aixahmad" target="_blank" rel="noopener" title="X / Twitter" aria-label="Follow AI x Ahmad on X (opens a new tab)">𝕏</a>
      <a href="https://youtube.com/@aixahmad" target="_blank" rel="noopener" title="YouTube" aria-label="AI x Ahmad on YouTube (opens a new tab)">▶</a>
    </div>
  </div>
</header>

<main class="wrap">
  <section class="edition" aria-labelledby="edition-title">
    <div><div class="eyebrow">The AI intelligence desk</div><h1 id="edition-title">Keep your eye on what’s next.</h1>
      <p>Models, ideas and breakthroughs. Explore the news behind a world changing with AI.</p></div>
    <div class="editionmeta"><div class="editiondate" id="editiondate"></div><div class="editionnote">__STORYCOUNT__ stories · __SOURCECOUNT__ feed sources in this edition</div></div>
  </section>
  <section id="hero" aria-label="Featured stories"></section>

  <div class="statusrow" id="freshness">
    <span class="live"><span class="d" aria-hidden="true"></span><span id="updlabel"></span></span>
    <div class="chips" id="trends" aria-label="Topics in this edition"></div>
  </div>

  <form class="searchrow" id="searchform" role="search">
    <div class="searchbox">
      <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#626960" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"></circle><path d="M21 21l-4-4"></path></svg>
      <input id="q" type="search" aria-label="Search headlines, publishers and topics" placeholder="Search headlines, publishers or topics…" autocomplete="off">
    </div>
    <button class="searchbtn" id="searchgo" type="submit">Search</button>
  </form>

  <div class="cols" id="feed-start" tabindex="-1">
    <div class="main">
      <div class="feedtop">
        <h2 class="sec-h" id="feedtitle" style="margin:0">The latest dispatches</h2>
        <div class="fb" role="group" aria-label="Feed view">
          <button id="fLatest" class="on" aria-pressed="true">Latest</button>
          <button id="fHot" aria-pressed="false">Most covered</button>
          <button id="fSaved" aria-pressed="false">Saved <span id="savedcount">0</span></button>
        </div>
      </div>
      <div class="count"><span id="count" role="status" aria-live="polite" aria-atomic="true"></span><button class="resetfilters" id="resetfilters" hidden>Clear filters</button></div>
      <span id="saveannouncement" class="sr-only" role="status" aria-live="polite"></span>
      <div class="feed" id="list"></div>
      <button class="more" id="more" style="display:none">Show more stories</button>
      <div id="researchwrap"></div>
    </div>

    <aside class="aside">
      <section class="sblock" id="trending"></section>
      <section class="sblock" id="tools"></section>
      <section class="briefcard">
        <div class="eyebrow" style="margin-bottom:12px">Stay curious</div>
        <div class="briefh">Make sense of the shift.</div>
        <p>Join AI x Ahmad for a closer look at the tools and ideas shaping what comes next.</p>
        <a class="bbtn" href="https://youtube.com/@aixahmad" target="_blank" rel="noopener">▶ Subscribe on YouTube</a>
        <a class="bbtn2" href="https://x.com/aixahmad" target="_blank" rel="noopener">𝕏 Follow on X</a>
        <div class="bfoot">Follow the conversation on your favorite platform.</div>
      </section>
      <div class="trustnote"><strong>Sources first. Always.</strong>Headlines link to their original publishers. Coverage counts show related links, not a measure of accuracy. Saved stories stay in this browser.<br><button onclick="openPage('how')">How the radar works →</button></div>
    </aside>
  </div>
</main>

<footer>
  <div class="ftop">
    <div class="fbrand">
      <a class="brand" href="./" aria-label="AI Radar home"><span class="orb" aria-hidden="true">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"></circle><path d="M12 12L19 8"></path></svg>
      </span><span class="nm">AI <b>Radar</b></span></a>
      <p>A clearer view of artificial intelligence. Browse the headlines, explore new ideas, and go straight to the original reporting.</p>
      <div class="fsoc">
        <a href="https://x.com/aixahmad" target="_blank" rel="noopener" title="X / Twitter">𝕏</a>
        <a href="https://youtube.com/@aixahmad" target="_blank" rel="noopener" title="YouTube">▶</a>
        <a href="mailto:__EMAIL__" title="Email">✉</a>
      </div>
    </div>
    <div class="fcol"><h4>Sections</h4><div id="fsections"></div></div>
    <div class="fcol"><h4>AI Radar</h4>
      <button class="lk" onclick="openPage('about')">About us</button>
      <button class="lk" onclick="openPage('how')">How it works</button>
      <button class="lk" onclick="openPage('editorial')">Editorial standards</button>
      <a href="studio.html">Newsroom (staff)</a>
    </div>
    <div class="fcol"><h4>Contact</h4>
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

<noscript><p class="wrap">Enable JavaScript to browse the news feed and save stories. <a href="digests/latest.html" style="text-decoration:underline">Read the latest generated digest</a>.</p></noscript>
<div id="reader" role="dialog" aria-modal="true" aria-labelledby="reader-title" tabindex="-1" hidden></div>

<script>
const PILLARS = __PILLARS__, ITEMS = __ITEMS__, TRENDS = __TRENDS__, COLORS = __COLORS__, PAGE = 18;
const PUBURL = __FBURLJSON__, CONTACT = "__EMAIL__", LAST_FETCHED = __FETCHEDJSON__;
let pillar = 0, feedView = "latest", q = "", shown = PAGE, PUBS = [];
let readerFocus = null;
let SAVED = new Set();
try{ const stored=JSON.parse(localStorage.getItem("air_saved")||"[]");
  if(Array.isArray(stored)) SAVED=new Set(stored.filter(u=>typeof u==="string")); }catch(e){}

document.getElementById("yr").textContent = new Date().getFullYear();
const lastFetch = LAST_FETCHED ? new Date(LAST_FETCHED) : null;
const hasFetch = lastFetch && Number.isFinite(lastFetch.getTime());
const stale = hasFetch && Date.now()-lastFetch.getTime()>24*3600*1000;
document.getElementById("freshness").classList.toggle("stale", !!stale);
document.getElementById("updlabel").textContent = hasFetch ?
  "Last collected " + lastFetch.toLocaleString("en-GB",{day:"numeric",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit",timeZoneName:"short"}) + (stale ? " · Collection is older than 24 hours" : "") : "Collection time unavailable";
document.getElementById("editiondate").textContent = hasFetch ? "Collected " + lastFetch.toLocaleDateString("en-GB",{day:"numeric",month:"long",year:"numeric"}) : "The news edition";

function ago(iso){ const dt=new Date(iso), s=(Date.now()-dt.getTime())/1000;
  if(!iso||!Number.isFinite(s)) return "Date unavailable";
  if(s<0||s>=604800) return fmtDate(iso);
  if(s<3600) return Math.max(1,s/60|0)+" min ago"; if(s<86400) return (s/3600|0)+"h ago"; return (s/86400|0)+"d ago"; }
function esc(t){ const d=document.createElement("div"); d.textContent=t==null?"":t; return d.innerHTML.replace(/"/g,"&quot;").replace(/'/g,"&#39;"); }
function fmtDate(ts){ const d=new Date(ts); return Number.isFinite(d.getTime()) ? d.toLocaleDateString("en-GB",{day:"numeric",month:"short",year:"numeric"}) : "Date unavailable"; }
function safeURL(value){ try{ const u=new URL(value); return /^(https?:)$/.test(u.protocol)?u.href:""; }catch(e){return "";} }
function openSource(url){ const u=safeURL(url); if(u) window.open(u,"_blank","noopener"); }
function coverageCount(it){ return new Set([it.u,...(Array.isArray(it.l)?it.l.map(l=>typeof l==="string"?l:l.url):[])].filter(safeURL)).size; }
function scrollFeed(){ document.getElementById("feed-start").scrollIntoView({behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth",block:"start"}); }
function resetFilters(){ pillar=0; q=""; shown=PAGE; document.getElementById("q").value=""; navBar(); trendsBar(); render(); }
function col(p){ return COLORS[p] || (p===0?"#11151a":"#5A6872"); }
function colByName(nm){ for(const k in PILLARS){ if(PILLARS[k]===nm) return col(+k); } return "#11151a"; }
function catTag(t,c){ return '<span class="cat" style="color:'+c+'">'+esc(t)+'</span>'; }
function thumbCSS(seed,hex){ const pos=['85% 12%','15% 18%','78% 82%','22% 78%','50% 0%','90% 50%','10% 50%'][((seed%7)+7)%7];
  return "background:radial-gradient(120% 110% at "+pos+","+hex+"26,rgba(255,255,255,0) 60%),linear-gradient(160deg,#f3f4f6,#e7e9ec);"; }
function bmIcon(on){ return '<svg aria-hidden="true" width="13" height="13" viewBox="0 0 24 24" fill="'+(on?"currentColor":"none")+'" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>'; }

function filtered(){ const words=q.toLowerCase().split(/\s+/).filter(Boolean); const items=ITEMS.filter(it =>
  (!pillar||it.p===pillar) && (feedView!=="saved"||SAVED.has(it.u)) &&
  words.every(n=>[it.t,it.s,PILLARS[it.p]].join(" ").toLowerCase().includes(n)));
  return items.sort((a,b)=>(feedView==="coverage"?coverageCount(b)-coverageCount(a):0)||((Date.parse(b.d)||0)-(Date.parse(a.d)||0))); }

/* ---- breaking ticker ---- */
function renderTicker(){
  document.getElementById("ticker").innerHTML = ITEMS.slice(0,4)
    .map(it=>'<span class="tk"><span class="dot"></span>'+esc(it.t.slice(0,82))+'</span>').join("");
}

/* ---- category nav ---- */
function navBar(){
  const el=document.getElementById("nav"); el.innerHTML="";
  const mk=(id,label)=>{ const b=document.createElement("button"); b.textContent=label; b.className=id===pillar?"active":""; b.setAttribute("aria-pressed",String(id===pillar));
    b.onclick=()=>{ pillar=id; shown=PAGE; navBar(); render(); scrollFeed(); }; el.appendChild(b); };
  mk(0,"All stories"); Object.entries(PILLARS).forEach(([k,v])=>mk(+k,v));
}

/* ---- trend chips ---- */
function trendsBar(){ const el=document.getElementById("trends"); el.innerHTML="";
  TRENDS.slice(0,5).forEach(t=>{ const c=document.createElement("button"); const on=q.toLowerCase()===t.display.toLowerCase(); c.className="chip"+(on?" active":""); c.setAttribute("aria-pressed",String(on));
    c.textContent=t.display;
    c.onclick=()=>{ q=on?"":t.display; document.getElementById("q").value=q; shown=PAGE; trendsBar(); render(); scrollFeed(); };
    el.appendChild(c); }); }

/* ---- hero (editor articles, else top news) ---- */
function heroEntries(){
  const out=[];
  PUBS.slice(0,4).forEach((p,i)=>out.push({ title:p.title, catName:(p.cat||"Featured"), color:colByName(p.cat),
    source:"AI Radar", time:fmtDate(p.ts), dek:(p.body||"").replace(/\s+/g," ").trim().slice(0,170),
    img:safeURL(p.image), editorial:true, seed:i, open:()=>openArticle(i) }));
  let i=0;
  while(out.length<4 && i<ITEMS.length){ const it=ITEMS[i];
    out.push({ title:it.t, catName:PILLARS[it.p], color:col(it.p), source:it.s, time:ago(it.d), dek:"",
      img:"", editorial:false, seed:i+3, open:()=>openSource(it.u) }); i++; }
  return out;
}
function renderHero(){
  const e=heroEntries(); const el=document.getElementById("hero");
  if(!e.length){ el.innerHTML=""; return; }
  const lead=e[0], side=e.slice(1,4);
  const L=document.createElement("button"); L.className="lead"+(lead.img?" has-image":""); L.onclick=lead.open;
  L.innerHTML=(lead.img?'<img class="limg" src="'+esc(lead.img)+'" alt="" loading="eager">':'<div class="leadviz" aria-hidden="true"><span class="radar-mark"></span><span>Signal / Intelligence / Perspective</span></div>')+
    '<div class="lbody"><div class="lbadges">'+catTag(lead.catName,lead.color)+'<span class="leadbadge"><span class="dot"></span>Lead story</span></div>'+
    '<h2>'+esc(lead.title)+'</h2>'+(lead.dek?'<p class="ldek">'+esc(lead.dek)+'…</p>':'')+
    '<div class="lmeta"><span class="src">'+esc(lead.source)+'</span><span>·</span><span>'+esc(lead.time)+'</span><span class="sourcearrow">'+(lead.editorial?'Read feature →':'Read source ↗')+'</span></div></div>';
  const S=document.createElement("div"); S.className="sidestack";
  const label=document.createElement("div"); label.className="stacklabel"; label.textContent="Also on the radar"; S.appendChild(label);
  side.forEach(s=>{ const b=document.createElement("button"); b.className="scardx"; b.onclick=s.open;
    b.innerHTML='<div class="lbadges">'+catTag(s.catName,s.color)+'</div><div class="stitle">'+esc(s.title)+'</div>'+
      '<div class="smeta"><span class="src">'+esc(s.source)+'</span> · '+esc(s.time)+'</div>';
    S.appendChild(b); });
  const grid=document.createElement("div"); grid.className="herogrid"; grid.appendChild(L); grid.appendChild(S);
  el.innerHTML=""; el.appendChild(grid);
}

/* ---- feed (text-forward, hairline divided) ---- */
function render(){
  const items=filtered();
  document.getElementById("feedtitle").textContent=feedView==="saved"?"Your reading list":pillar?PILLARS[pillar]:"The latest dispatches";
  document.getElementById("count").textContent=items.length+" "+(items.length===1?"story":"stories")+(q?' for “'+q+'”':"")+(feedView==="coverage"?" · ranked by linked reports":feedView==="saved"?" · saved in this browser":" · newest publication first");
  document.getElementById("resetfilters").hidden=!(q||pillar);
  document.getElementById("savedcount").textContent=ITEMS.filter(it=>SAVED.has(it.u)).length;
  const list=document.getElementById("list");
  list.innerHTML=items.length?"":'<div class="empty"><strong>'+(feedView==="saved"&&!q&&!pillar?'A little space for your next read.':'No matching stories.')+'</strong><p>'+(feedView==="saved"&&!q&&!pillar?'Use Save on a story to keep it here. Saved links stay in this browser.':'Try a different keyword, publisher or topic.')+'</p>'+(q||pillar?'<button class="resetfilters" onclick="resetFilters()">Clear filters</button>':'')+'</div>';
  items.slice(0,shown).forEach((it,idx)=>{
    const a=document.createElement("article"); a.className="vrow";
    const coverage=coverageCount(it), hot=coverage>1?'<span class="hotsrc"><span class="pip"></span>'+coverage+' linked reports</span>':'';
    const on=SAVED.has(it.u);
    a.innerHTML='<div class="vmain"><div class="vtop">'+catTag(PILLARS[it.p],col(it.p))+hot+'</div>'+
      '<a class="vtitle" href="'+esc(safeURL(it.u))+'" target="_blank" rel="noopener" aria-label="'+esc(it.t)+' (opens original publisher in a new tab)">'+esc(it.t)+'</a>'+
      '<div class="vmeta"><span class="src">'+esc(it.s)+'</span><span>·</span><time datetime="'+esc(it.d)+'" title="'+esc(fmtDate(it.d))+'">'+ago(it.d)+'</time>'+
      '<button class="savebtn'+(on?" on":"")+'" data-url="'+esc(it.u)+'" aria-pressed="'+on+'" aria-label="'+(on?'Remove saved story: ':'Save story: ')+esc(it.t)+'">'+bmIcon(on)+(on?"Saved":"Save")+'</button></div></div>';
    a.querySelector(".savebtn").onclick=(e)=>{ e.stopPropagation(); toggleSave(it.u); };
    list.appendChild(a);
  });
  document.getElementById("more").style.display=items.length>shown?"block":"none";
}
function toggleSave(u){ if(SAVED.has(u)) SAVED.delete(u); else SAVED.add(u);
  let persisted=true; try{ localStorage.setItem("air_saved", JSON.stringify([...SAVED])); }catch(e){persisted=false;}
  render();
  document.getElementById("saveannouncement").textContent=(SAVED.has(u)?"Story saved.":"Story removed from saved.")+(persisted?"":" Browser storage is unavailable; saves last for this visit.");
  const button=Array.from(document.querySelectorAll(".savebtn")).find(b=>b.dataset.url===u);
  (button||document.getElementById("fSaved")).focus({preventScroll:true}); }

/* ---- research grid ---- */
function renderResearch(){
  const rs=ITEMS.filter(it=>it.p===9).slice(0,4);
  const w=document.getElementById("researchwrap");
  if(!rs.length){ w.innerHTML=""; return; }
  let h='<div class="sec-h" style="margin-top:34px"><span class="bar"></span>Research Papers</div><div class="rgrid">';
  rs.forEach(it=>{ h+='<button class="rcard" data-u="'+esc(it.u)+'"><span class="rlabel">Research</span>'+
    '<div class="rtitle">'+esc(it.t)+'</div><div class="rmeta"><span class="src">'+esc(it.s)+'</span> · '+ago(it.d)+'</div></button>'; });
  w.innerHTML=h+"</div>";
  w.querySelectorAll(".rcard").forEach(b=>b.onclick=()=>openSource(b.dataset.u));
}

/* ---- sidebar: trending ---- */
function renderTrending(){
  const top=ITEMS.filter(it=>coverageCount(it)>1).sort((a,b)=>coverageCount(b)-coverageCount(a)||((Date.parse(b.d)||0)-(Date.parse(a.d)||0))).slice(0,5);
  if(!top.length){ document.getElementById("trending").hidden=true; return; }
  let h='<div class="shead">Most covered</div>';
  top.forEach((it,i)=>{ const rc=i===0?'#c8102e':'#11151a';
    h+='<button class="trow" data-u="'+esc(it.u)+'"><span class="trank" style="color:'+rc+'">'+(i+1)+'</span>'+
      '<div class="tbody"><div class="ttitle">'+esc(it.t)+'</div><div class="tmeta">'+coverageCount(it)+' linked reports · '+ago(it.d)+'</div></div></button>'; });
  const el=document.getElementById("trending"); el.innerHTML=h;
  el.querySelectorAll(".trow").forEach(b=>b.onclick=()=>openSource(b.dataset.u));
}

/* ---- sidebar: new tools & models (category 1) ---- */
function renderTools(){
  const ts=ITEMS.filter(it=>it.p===1).slice(0,4);
  const el=document.getElementById("tools");
  if(!ts.length){ el.innerHTML=""; return; }
  const c=col(1);
  let h='<div class="shead">New Tools &amp; Models</div>';
  ts.forEach(it=>{ const ini=((it.t||"A").trim()[0]||"A").toUpperCase();
    h+='<button class="toolrow2" data-u="'+esc(it.u)+'"><div class="ticon" style="background:'+c+'">'+esc(ini)+'</div>'+
      '<div style="min-width:0;flex:1"><div class="tname">'+esc(it.t.slice(0,64))+'</div><div class="ttag">'+esc(it.s)+' · '+ago(it.d)+'</div></div></button>'; });
  el.innerHTML=h;
  el.querySelectorAll(".toolrow2").forEach(b=>b.onclick=()=>openSource(b.dataset.u));
}

/* ---- editor-published articles from Firebase ---- */
async function loadFeatured(){
  if(!PUBURL) return;
  try{
    const r=await fetch(PUBURL.replace(/\/+$/,"")+"/published.json"); if(!r.ok) return;
    const data=await r.json()||{}; PUBS=Object.values(data).filter(p=>p&&typeof p.title==="string"&&typeof p.body==="string").sort((a,b)=>(b.ts||0)-(a.ts||0));
    if(PUBS.length){ renderHero(); openArticleFromHash(); }
  }catch(e){}
}
const RTOP = '<div class="rtopbar"><button class="rback" onclick="closeArticle()">← Back</button>'+
  '<a class="brand" href="./" aria-label="AI Radar home"><span class="orb" aria-hidden="true"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"></circle><path d="M12 12L19 8"></path></svg></span><span class="nm">AI <b>Radar</b></span></a>'+
  '<span class="spacer"></span></div>';
function showReader(){ const rd=document.getElementById("reader");
  if(rd.hidden) readerFocus=document.activeElement;
  rd.hidden=false; rd.scrollTop=0; document.body.style.overflow="hidden";
  document.querySelectorAll("main,header.mast,footer,.ticker,.skip").forEach(el=>el.inert=true);
  rd.querySelector(".rback").focus({preventScroll:true}); }
function openArticle(i){
  const p=PUBS[i]; if(!p) return;
  const color=colByName(p.cat);
  const txt=(p.body||"");
  const paras=txt.split(/\n\s*\n/).map(t=>"<p>"+esc(t).replace(/\n/g,"<br>")+"</p>").join("");
  const mins=Math.max(1,Math.round(txt.split(/\s+/).filter(Boolean).length/200));
  const src=safeURL(p.url)?'<p style="margin-top:8px"><a class="srclink" href="'+esc(safeURL(p.url))+'" target="_blank" rel="noopener">Read the original source ↗</a></p>':"";
  const rel=PUBS.map((x,j)=>({x,j})).filter(o=>o.j!==i).slice(0,3).map(o=>
    '<button class="relcard" onclick="openArticle('+o.j+')">'+
    catTag(o.x.cat||"Featured",colByName(o.x.cat))+'<div class="reltitle">'+esc(o.x.title)+'</div></button>').join("");
  document.getElementById("reader").innerHTML='<div class="rbox">'+RTOP+
    '<article class="rinner">'+catTag(p.cat||"Featured",color)+'<h1 id="reader-title">'+esc(p.title)+'</h1>'+
    '<div class="rmeta"><span class="ravatar">A</span><div><div class="rauthor">AI Radar Desk</div><div class="rsub">AI Radar · '+fmtDate(p.ts)+' · '+mins+' min read</div></div></div></article>'+
    (safeURL(p.image)?'<div class="rhero"><img class="rimg" src="'+esc(safeURL(p.image))+'" alt=""></div>':'')+
    '<div class="rinner"><div class="rbody">'+paras+src+'</div>'+
    (rel?'<div class="sec-h" style="margin-top:42px">More from AI Radar</div><div class="relgrid">'+rel+'</div>':'')+
    '</div></div>';
  showReader();
  try{ history.replaceState(null,"","#a="+encodeURIComponent(p.id||"")); }catch(e){}
}
function closeArticle(){ document.getElementById("reader").hidden=true; document.body.style.overflow="";
  document.querySelectorAll("main,header.mast,footer,.ticker,.skip").forEach(el=>el.inert=false);
  if(readerFocus&&readerFocus.isConnected) readerFocus.focus({preventScroll:true});
  readerFocus=null;
  try{ history.replaceState(null,"",location.pathname+location.search); }catch(e){} }
document.getElementById("reader").addEventListener("click",e=>{ if(e.target.id==="reader") closeArticle(); });
/* deep link: #a=<id> opens that article (used by shares) */
function openArticleFromHash(){
  const m=(location.hash||"").match(/a=([^&]+)/); if(!m) return;
  let articleId; try{articleId=decodeURIComponent(m[1]);}catch(e){return;}
  const idx=PUBS.findIndex(p=>String(p.id)===articleId); if(idx>=0) openArticle(idx);
}

/* ---- footer section links ---- */
function footerSections(){
  const el=document.getElementById("fsections");
  Object.entries(PILLARS).slice(0,8).forEach(([k,v])=>{ const b=document.createElement("button"); b.className="lk"; b.textContent=v;
    b.onclick=()=>{ pillar=+k; shown=PAGE; navBar(); render(); scrollFeed(); }; el.appendChild(b); });
}

/* ---- static pages (About / Privacy / ...) in the reader ---- */
const PAGES={
  about:["About AI Radar",
    "<p>AI Radar is an independent aggregator that follows artificial intelligence through company blogs, research labs, news outlets and developer communities. Each headline links to its original publisher. The collection timestamp on the home page shows when the feed was last gathered.</p><p>Our goal is simple: make the news easier to explore. AI Radar is created and edited by <a class='srclink' href='https://x.com/aixahmad' target='_blank' rel='noopener'>@aixahmad</a>.</p>"],
  how:["How AI Radar works",
    "<p><b>1. We collect.</b> Automated collection gathers AI-related headlines. This page is a generated snapshot; its collection timestamp comes from the feed, rather than the time the page was built.</p><p><b>2. We organise.</b> Keyword rules group headlines by topic. Related links are combined when the collector detects overlapping coverage.</p><p><b>3. You explore.</b> Latest sorts by publication date. Most covered ranks by the number of linked reports, which does not establish their accuracy. Search matches headlines, publisher names and topic labels.</p><p><b>4. You read.</b> Headlines open the original publisher in a new tab. Save adds a link to your browser’s reading list. It works without an account and does not sync between devices. The list displays saved stories that are still included in the current feed.</p>"],
  editorial:["Editorial standards",
    "<p>AI Radar aggregates and curates; it does not alter the words of the original publishers. Headlines and short excerpts are shown for identification and always link back to the source.</p><p>Featured articles written by our team are based only on the underlying reporting — we do not fabricate facts, numbers or quotes. Corrections are made promptly; if you spot an error, please contact us.</p>"],
  advertise:["Advertise & partner",
    "<p>Interested in partnering with AI Radar? Reach out at <a class='srclink' href='mailto:"+CONTACT+"'>"+CONTACT+"</a> or DM <a class='srclink' href='https://x.com/aixahmad' target='_blank' rel='noopener'>@aixahmad</a> on X to discuss opportunities.</p>"],
  contact:["Send a tip",
    "<p>Got a launch or a story we should be covering? We'd love to hear it.</p><p>Email <a class='srclink' href='mailto:"+CONTACT+"'>"+CONTACT+"</a> or message <a class='srclink' href='https://x.com/aixahmad' target='_blank' rel='noopener'>@aixahmad</a> on X.</p>"],
  privacy:["Privacy policy",
    "<p>You can browse AI Radar without an account. Saved story links are stored locally in this browser and can be removed using the Saved view.</p><p>The site is served as static pages, uses Google Fonts, and may load editor-published features from its configured publishing service. Hosting and third-party services may process connection information under their own privacy policies. External story links take you to the original publisher. Contact <a class='srclink' href='mailto:"+CONTACT+"'>"+CONTACT+"</a> for questions.</p>"],
  terms:["Terms of use",
    "<p>AI Radar is provided \"as is\", for informational purposes only. While we work to keep the feed accurate and current, we make no warranty as to completeness or accuracy and accept no liability for decisions made based on its content.</p><p>Headlines, excerpts and trademarks belong to their respective owners. If you are a rights holder and would like a link or excerpt amended, contact <a class='srclink' href='mailto:"+CONTACT+"'>"+CONTACT+"</a>.</p>"],
  disclaimer:["Disclaimer",
    "<p>AI Radar is an independent news aggregator and is not affiliated with, endorsed by, or sponsored by any of the companies or publications whose stories it links to.</p><p>All product names, logos and brands are property of their respective owners. Content is aggregated automatically; the appearance of a source does not imply endorsement either way.</p>"],
};
function openPage(key){
  const p=PAGES[key]; if(!p) return;
  document.getElementById("reader").innerHTML='<div class="rbox">'+RTOP+
    '<article class="rinner"><h1 id="reader-title">'+p[0]+'</h1><div class="rbody">'+p[1]+'</div></article></div>';
  showReader();
}
document.addEventListener("keydown",e=>{ const rd=document.getElementById("reader"); if(rd.hidden) return;
  if(e.key==="Escape"){e.preventDefault(); closeArticle();}
  if(e.key==="Tab"){const focusable=Array.from(rd.querySelectorAll("a[href],button:not([disabled])")); const first=focusable[0],last=focusable[focusable.length-1];
    if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
    else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();} } });

/* ---- events + init ---- */
document.getElementById("q").addEventListener("input",e=>{ q=e.target.value.trim(); shown=PAGE; render(); trendsBar(); });
document.getElementById("searchform").onsubmit=e=>{e.preventDefault(); scrollFeed();};
document.getElementById("resetfilters").onclick=resetFilters;
document.getElementById("more").onclick=()=>{ shown+=PAGE; render(); };
function setFeedView(view){ feedView=view; shown=PAGE;
  for(const [id,value] of [["fLatest","latest"],["fHot","coverage"],["fSaved","saved"]]){ const button=document.getElementById(id); button.classList.toggle("on",view===value); button.setAttribute("aria-pressed",String(view===value)); }
  render(); }
document.getElementById("fHot").onclick=()=>setFeedView("coverage");
document.getElementById("fLatest").onclick=()=>setFeedView("latest");
document.getElementById("fSaved").onclick=()=>setFeedView("saved");

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
        "ORDER BY COALESCE(published, fetched) DESC, fetched DESC LIMIT ?", (MAX_STORIES,)
    ).fetchall()
    last_fetched = conn.execute("SELECT MAX(fetched) FROM items").fetchone()[0]
    trends = scoring.compute_trends(conn)
    chips = [t for t in trends if t["status"] in ("new", "rising")][:8]
    conn.close()

    items = [{
        "t": r["title"], "u": r["url"], "s": r["source"], "p": r["pillar"],
        "d": r["published"] or r["fetched"], "l": json.loads(r["links"] or "[]"),
    } for r in rows]

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
            .replace("__JSONLD__", _script_json(jsonld))
            .replace("__PILLARS__", _script_json(config.CATEGORIES))
            .replace("__ITEMS__", _script_json(items))
            .replace("__TRENDS__", _script_json(chips))
            .replace("__COLORS__", _script_json(CATCOLORS))
            .replace("__FBURLJSON__", _script_json(_load_fburl()))
            .replace("__FETCHEDJSON__", _script_json(last_fetched))
            .replace("__EMAIL__", CONTACT_EMAIL)
            .replace("__STORYCOUNT__", str(len(items)))
            .replace("__SOURCECOUNT__", str(len({item["s"] for item in items}))))

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # robots.txt — let crawlers in, keep the private studio out, point to sitemap
    with open(os.path.join(OUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\nDisallow: /studio.html\nDisallow: /studio-legacy.html\n"
                "Disallow: /pipeline.json\n\n"
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
