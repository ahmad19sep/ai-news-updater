"""
AI Radar - PUBLIC news website generator (modern news-site layout).

Reads news.db and writes docs/index.html = an open, SEO-friendly AI-news site
styled like a modern publication (masthead, lead story, section tags, headline
river). Editor-published articles (from Firebase /published) appear as featured
stories. The private studio is generated separately to docs/studio.html.

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
# Custom domain (GitHub Pages serves the repo at the root of this domain).
SITE_URL = "https://hafizahmad.com/"
# Paste the content value from Google Search Console's "HTML tag" verification
# method here (just the long code), then re-run. Leave "" to skip.
GSC_VERIFY = ""
SITE_DESC = ("Breaking artificial-intelligence news, every day: new models and tools, "
             "AI in science, business, and research — updated every 30 minutes, with links "
             "to the original sources.")
CONTACT_EMAIL = "get.shahzadsaddique@gmail.com"   # shown in footer/contact; change anytime

# section colours (newspaper-style tags), keyed by category id
CATCOLORS = {1: "#4f7cff", 2: "#22c55e", 3: "#a855f7", 4: "#f59e0b", 5: "#ef4444",
             6: "#06b6d4", 7: "#84cc16", 8: "#ec4899", 9: "#8b5cf6", 10: "#94a3b8"}

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#070b18">
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
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&family=Newsreader:opsz,wght@6..72,500;6..72,600;6..72,700&display=swap" rel="stylesheet">
<style>
  :root { --bg:#070b18; --surface:#0e1730; --surface2:#15213e; --text:#e8edfb;
          --dim:#97a4c6; --faint:#5e6b8c; --line:rgba(125,150,220,.14);
          --line2:rgba(125,150,220,.28); --accent:#38bdf8; --accent2:#4f7cff;
          --orange:#fb923c; --grad:linear-gradient(135deg,#4f7cff,#38bdf8);
          --display:"Space Grotesk", Inter, sans-serif;
          --head:"Newsreader", Georgia, serif; }
  * { box-sizing:border-box; }
  body { margin:0; background:radial-gradient(1200px 560px at 72% -14%, #16275a 0%, #0a1330 40%, var(--bg) 72%);
         color:var(--text); font:15px/1.55 Inter, system-ui, sans-serif; -webkit-font-smoothing:antialiased; }
  a { color:inherit; text-decoration:none; }
  .wrap { max-width:1080px; margin:0 auto; padding:0 18px 70px; }

  /* masthead */
  header { border-bottom:1px solid var(--line); background:rgba(7,11,24,.78); backdrop-filter:blur(12px);
           position:sticky; top:0; z-index:30; }
  .mast { max-width:1080px; margin:0 auto; padding:14px 18px; display:flex; align-items:center; gap:14px; }
  .brand { display:flex; align-items:center; gap:11px; }
  .brand .orb { width:34px; height:34px; border-radius:10px; background:var(--grad);
          display:flex; align-items:center; justify-content:center; font-size:18px;
          box-shadow:0 0 22px rgba(79,124,255,.5); }
  .brand .nm { font:800 22px var(--display); letter-spacing:-.02em; }
  .brand .nm b { background:var(--grad); -webkit-background-clip:text; background-clip:text; color:transparent; }
  .mast .date { color:var(--faint); font-size:12.5px; margin-left:4px; }
  .mast .right { margin-left:auto; display:flex; gap:8px; }
  .mast .right a { color:var(--dim); font-size:12.5px; font-weight:600; border:1px solid var(--line);
          border-radius:999px; padding:6px 13px; }
  .mast .right a:hover { color:var(--text); border-color:var(--line2); }
  /* category nav */
  .nav { border-bottom:1px solid var(--line); background:rgba(7,11,24,.6); }
  .navrow { max-width:1080px; margin:0 auto; padding:0 12px; display:flex; gap:2px; overflow-x:auto; scrollbar-width:none; }
  .navrow::-webkit-scrollbar { display:none; }
  .navrow button { background:none; border:none; color:var(--dim); font:600 13px Inter; cursor:pointer;
          padding:12px 13px; white-space:nowrap; border-bottom:2px solid transparent; }
  .navrow button:hover { color:var(--text); }
  .navrow button.active { color:#fff; border-bottom-color:var(--accent); }

  .tag { font:700 10.5px Inter; letter-spacing:.05em; text-transform:uppercase; }
  .live { display:inline-block; width:7px; height:7px; border-radius:50%; background:#22c55e;
          box-shadow:0 0 0 3px rgba(34,197,94,.2); animation:pulse 2s infinite; vertical-align:middle; margin-right:6px; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }

  /* featured (editor-published) */
  .feat-h, .sec-h { font:700 13px var(--display); color:var(--dim); text-transform:uppercase;
          letter-spacing:.1em; margin:26px 2px 14px; display:flex; align-items:center; gap:8px; }
  .lead { display:grid; grid-template-columns:1.3fr 1fr; gap:20px; align-items:stretch;
          background:var(--surface); border:1px solid var(--line); border-radius:16px; overflow:hidden;
          cursor:pointer; transition:.15s; margin-bottom:14px; }
  .lead:hover { border-color:var(--line2); }
  .lead .img { min-height:240px; background-size:cover; background-position:center; background-color:#0c1428; }
  .lead .tx { padding:24px; display:flex; flex-direction:column; justify-content:center; }
  .lead h2 { font:700 clamp(22px,3vw,30px) var(--head); line-height:1.2; margin:10px 0 10px; }
  .lead .ex { color:var(--dim); font-size:14.5px; line-height:1.6; }
  .lead .m { color:var(--faint); font-size:12px; margin-top:12px; }
  .frow { display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:14px; }
  .fcard { background:var(--surface); border:1px solid var(--line); border-radius:14px; overflow:hidden;
           cursor:pointer; transition:.15s; }
  .fcard:hover { border-color:var(--line2); transform:translateY(-2px); }
  .fcard .img { height:140px; background-size:cover; background-position:center; background-color:#0c1428; }
  .fcard .fb { padding:13px 15px; }
  .fcard h3 { font:600 16px var(--head); line-height:1.3; margin:6px 0 0; }

  /* trending */
  .trends { display:flex; flex-wrap:wrap; gap:8px; margin:6px 0 4px; }
  .chip { background:rgba(56,189,248,.1); color:var(--accent); border:1px solid rgba(56,189,248,.28);
          border-radius:999px; padding:5px 13px; font:600 12.5px Inter; cursor:pointer; }
  .chip:hover { background:rgba(56,189,248,.18); }

  .toolrow { display:flex; gap:10px; align-items:center; margin:14px 0 4px; flex-wrap:wrap; }
  .search { flex:1; min-width:200px; }
  .search input { width:100%; background:var(--surface); border:1px solid var(--line); color:var(--text);
          padding:11px 16px; border-radius:12px; font:14px Inter; outline:none; }
  .search input:focus { border-color:var(--accent2); box-shadow:0 0 0 3px rgba(79,124,255,.2); }
  .hotbtn { background:var(--surface); border:1px solid var(--line); color:var(--dim);
          border-radius:999px; padding:9px 16px; font:600 12.5px Inter; cursor:pointer; }
  .hotbtn.active { background:var(--orange); border-color:var(--orange); color:#15110a; }
  .count { color:var(--faint); font-size:12.5px; margin:12px 2px; }

  /* headline river */
  .river { display:grid; grid-template-columns:1fr 1fr; gap:0 28px; }
  @media (max-width:680px){ .river { grid-template-columns:1fr; } .lead { grid-template-columns:1fr; } .lead .img{min-height:180px;} }
  .item { padding:15px 0; border-bottom:1px solid var(--line); }
  .item h3 { font:600 16.5px/1.4 var(--head); margin:7px 0 0; letter-spacing:-.005em; }
  .item:hover h3 { color:#fff; }
  .item h3 a:hover { color:var(--accent); }
  .item .m { color:var(--faint); font-size:12px; margin-top:7px; display:flex; flex-wrap:wrap; gap:5px 12px; align-items:center; }
  .hotpill { color:var(--orange); font-weight:700; }
  .more { display:block; margin:24px auto 0; background:var(--surface); color:var(--text); border:1px solid var(--line);
          padding:11px 34px; border-radius:999px; font:700 13px Inter; cursor:pointer; }
  .more:hover { border-color:var(--accent); }
  .empty { color:var(--faint); text-align:center; padding:50px 0; }

  /* footer */
  footer { border-top:1px solid var(--line); margin-top:46px; background:rgba(7,11,24,.55); }
  .ftop { max-width:1080px; margin:0 auto; padding:44px 18px 30px;
          display:grid; grid-template-columns:1.7fr 1fr 1fr 1fr; gap:34px; }
  @media (max-width:680px){ .ftop { grid-template-columns:1fr 1fr; gap:28px 18px; } }
  .fbrand .brand { margin-bottom:14px; }
  .fbrand p { color:var(--faint); font-size:13px; line-height:1.65; max-width:300px; margin:0 0 16px; }
  .fsoc { display:flex; gap:9px; }
  .fsoc a { width:38px; height:38px; border:1px solid var(--line); border-radius:11px; display:flex;
            align-items:center; justify-content:center; color:var(--dim); font-size:15px; transition:.15s; }
  .fsoc a:hover { border-color:var(--accent); color:var(--accent); transform:translateY(-2px); }
  .fcol h4 { font:700 12px var(--display); text-transform:uppercase; letter-spacing:.1em;
             color:var(--dim); margin:2px 0 14px; }
  .fcol a, .fcol .lk { display:block; color:var(--faint); font-size:13.5px; padding:5px 0;
             cursor:pointer; background:none; border:none; text-align:left; font-family:Inter; }
  .fcol a:hover, .fcol .lk:hover { color:var(--accent); }
  .fbot { border-top:1px solid var(--line); max-width:1080px; margin:0 auto;
          padding:20px 18px 30px; color:var(--faint); font-size:12px; line-height:1.7;
          display:flex; flex-wrap:wrap; gap:6px 16px; align-items:center; justify-content:space-between; }
  .fbot .legal button { background:none; border:none; color:var(--dim); cursor:pointer; font:12px Inter; padding:0 2px; }
  .fbot .legal button:hover { color:var(--accent); }

  /* article reader */
  #reader { position:fixed; inset:0; z-index:60; background:rgba(4,7,16,.78); overflow-y:auto; }
  .rbox { max-width:720px; margin:40px auto; background:var(--surface); border:1px solid var(--line); border-radius:16px; padding:0 0 30px; }
  .rbox .img { width:100%; height:320px; background-size:cover; background-position:center; border-radius:16px 16px 0 0; background-color:#0c1428; }
  .rinner { padding:26px 28px; }
  .rbox h1 { font:700 clamp(24px,4vw,36px) var(--head); line-height:1.22; margin:0 0 10px; }
  .rbox .rm { color:var(--faint); font-size:13px; margin-bottom:20px; }
  .rbox .body { font:17px/1.75 var(--head); color:#dfe6f7; }
  .rbox .body p { margin:0 0 16px; }
  .rclose { position:sticky; top:12px; float:right; margin:12px 12px 0 0; background:var(--surface2);
            border:1px solid var(--line); color:var(--text); border-radius:999px; width:38px; height:38px; font-size:16px; cursor:pointer; z-index:2; }
</style>
</head>
<body>
<header>
  <div class="mast">
    <a class="brand" href="/"><span class="orb">📡</span><span class="nm">AI <b>Radar</b></span></a>
    <span class="date" id="date"></span>
    <span class="right">
      <a href="https://x.com/aixahmad" target="_blank" rel="noopener">𝕏</a>
      <a href="https://youtube.com/@aixahmad" target="_blank" rel="noopener">YouTube</a>
    </span>
  </div>
</header>
<nav class="nav"><div class="navrow" id="nav"></div></nav>
<div class="wrap">
  <div id="featured"></div>
  <div class="sec-h"><span class="live"></span> <span id="updlabel"></span></div>
  <div class="trends" id="trends"></div>
  <div class="toolrow">
    <div class="search"><input id="q" placeholder="Search AI news… models, tools, companies"></div>
    <button class="hotbtn" id="hot">🔥 Hot</button>
  </div>
  <div class="count" id="count"></div>
  <div class="river" id="list"></div>
  <button class="more" id="more" style="display:none">Show more</button>
</div>
<footer>
  <div class="ftop">
    <div class="fbrand">
      <a class="brand" href="/"><span class="orb">📡</span><span class="nm">AI <b>Radar</b></span></a>
      <p>The fastest way to follow artificial intelligence. We scan hundreds of sources and surface what matters — new models, tools, research and the people behind them — refreshed every 30 minutes.</p>
      <div class="fsoc">
        <a href="https://x.com/aixahmad" target="_blank" rel="noopener" title="X / Twitter">𝕏</a>
        <a href="https://youtube.com/@aixahmad" target="_blank" rel="noopener" title="YouTube">▶</a>
        <a href="mailto:__EMAIL__" title="Email">✉</a>
      </div>
    </div>
    <div class="fcol">
      <h4>Sections</h4>
      <div id="fsections"></div>
    </div>
    <div class="fcol">
      <h4>AI Radar</h4>
      <button class="lk" onclick="openPage('about')">About us</button>
      <button class="lk" onclick="openPage('how')">How it works</button>
      <button class="lk" onclick="openPage('editorial')">Editorial standards</button>
      <a href="/studio.html">Newsroom (staff)</a>
    </div>
    <div class="fcol">
      <h4>Contact</h4>
      <a href="mailto:__EMAIL__">__EMAIL__</a>
      <a href="https://x.com/aixahmad" target="_blank" rel="noopener">DM @aixahmad on X</a>
      <a href="https://youtube.com/@aixahmad" target="_blank" rel="noopener">YouTube @aixahmad</a>
      <button class="lk" onclick="openPage('advertise')">Advertise / partner</button>
      <button class="lk" onclick="openPage('contact')">Send a tip</button>
    </div>
  </div>
  <div class="fbot">
    <span>© <span id="yr"></span> AI Radar · An independent AI-news aggregator. Headlines and excerpts remain © their original publishers and link back to the source.</span>
    <span class="legal">
      <button onclick="openPage('privacy')">Privacy</button>·
      <button onclick="openPage('terms')">Terms</button>·
      <button onclick="openPage('disclaimer')">Disclaimer</button>
    </span>
  </div>
</footer>
<div id="reader" hidden></div>
<script>
const PILLARS = __PILLARS__, ITEMS = __ITEMS__, TRENDS = __TRENDS__, COLORS = __COLORS__, PAGE = 30;
const PUBURL = "__FBURL__";
let pillar = 0, hotOnly = false, q = "", shown = PAGE;
document.getElementById("yr").textContent = new Date().getFullYear();
document.getElementById("date").textContent = new Date().toLocaleDateString("en-GB",{weekday:"long",day:"numeric",month:"long",year:"numeric"});
document.getElementById("updlabel").textContent = "Updated __UPDATED__ · refreshes every 30 min";
function ago(iso){ if(!iso) return ""; const s=(Date.now()-new Date(iso).getTime())/1000;
  if(s<3600) return Math.max(1,s/60|0)+" min ago"; if(s<86400) return (s/3600|0)+"h ago"; return (s/86400|0)+"d ago"; }
function esc(t){ const d=document.createElement("div"); d.textContent=t; return d.innerHTML; }
function col(p){ return COLORS[p]||"#94a3b8"; }
function filtered(){ const n=q.toLowerCase(); return ITEMS.filter(it =>
  (!pillar||it.p===pillar) && (!hotOnly||(it.l&&it.l.length)) && (!n||it.t.toLowerCase().includes(n))); }
function render(){
  const items=filtered();
  document.getElementById("count").textContent = items.length+" stories"+(q?' for "'+q+'"':"")+(pillar?" · "+PILLARS[pillar]:"");
  const list=document.getElementById("list");
  list.innerHTML = items.length?"":'<div class="empty">No stories found.</div>';
  items.slice(0,shown).forEach(it=>{
    const d=document.createElement("div"); d.className="item";
    const hot=(it.l&&it.l.length)?'<span class="hotpill">🔥 '+(it.l.length+1)+" sources</span>":"";
    d.innerHTML='<span class="tag" style="color:'+col(it.p)+'">'+esc(PILLARS[it.p])+"</span>"+
      '<h3><a href="'+esc(it.u)+'" target="_blank" rel="noopener">'+esc(it.t)+"</a></h3>"+
      '<div class="m"><span>'+esc(it.s)+"</span><span>"+ago(it.d)+"</span>"+hot+"</div>";
    list.appendChild(d);
  });
  document.getElementById("more").style.display = items.length>shown?"block":"none";
}
function navBar(){
  const el=document.getElementById("nav"); el.innerHTML="";
  const mk=(id,label)=>{ const b=document.createElement("button"); b.textContent=label;
    b.className=id===pillar?"active":""; b.onclick=()=>{pillar=id;shown=PAGE;navBar();render();}; el.appendChild(b); };
  mk(0,"Top"); Object.entries(PILLARS).forEach(([k,v])=>mk(+k,v));
}
function trendsBar(){ const el=document.getElementById("trends");
  TRENDS.forEach(t=>{ const c=document.createElement("button"); c.className="chip";
    c.innerHTML=(t.status==="new"?"🆕":"🚀")+" "+esc(t.display);
    c.onclick=()=>{q=t.display;document.getElementById("q").value=t.display;shown=PAGE;render();}; el.appendChild(c); }); }
document.getElementById("q").addEventListener("input",e=>{q=e.target.value.trim();shown=PAGE;render();});
document.getElementById("hot").onclick=()=>{ hotOnly=!hotOnly; document.getElementById("hot").classList.toggle("active",hotOnly); shown=PAGE; render(); };
document.getElementById("more").onclick=()=>{shown+=PAGE;render();};

/* editor-published articles -> lead + featured row */
let PUBS=[];
function fmtDate(ts){ try{ return new Date(ts).toLocaleDateString("en-GB",{day:"numeric",month:"short"}); }catch(e){ return ""; } }
async function loadFeatured(){
  if(!PUBURL) return;
  try{
    const r=await fetch(PUBURL.replace(/\/+$/,"")+"/published.json"); if(!r.ok) return;
    const data=await r.json()||{}; PUBS=Object.values(data).filter(Boolean).sort((a,b)=>(b.ts||0)-(a.ts||0));
    const el=document.getElementById("featured"); if(!PUBS.length){ el.innerHTML=""; return; }
    el.innerHTML='<div class="feat-h">📡 Latest from AI Radar</div>';
    const lead=PUBS[0];
    const ld=document.createElement("div"); ld.className="lead"; ld.onclick=()=>openArticle(0);
    ld.innerHTML=(lead.image?'<div class="img" style="background-image:url(\''+esc(lead.image)+'\')"></div>':'<div class="img"></div>')+
      '<div class="tx"><span class="tag" style="color:'+(lead.cat?"#38bdf8":"#94a3b8")+'">'+esc(lead.cat||"Featured")+"</span>"+
      "<h2>"+esc(lead.title)+"</h2><div class='ex'>"+esc((lead.body||"").replace(/\s+/g," ").slice(0,180))+"…</div>"+
      "<div class='m'>"+fmtDate(lead.ts)+" · AI Radar</div></div>";
    el.appendChild(ld);
    if(PUBS.length>1){
      const row=document.createElement("div"); row.className="frow";
      PUBS.slice(1,5).forEach((p,i)=>{ const c=document.createElement("div"); c.className="fcard"; c.onclick=()=>openArticle(i+1);
        c.innerHTML=(p.image?'<div class="img" style="background-image:url(\''+esc(p.image)+'\')"></div>':'<div class="img"></div>')+
          '<div class="fb"><span class="tag" style="color:#38bdf8">'+esc(p.cat||"Featured")+'</span><h3>'+esc(p.title)+"</h3></div>";
        row.appendChild(c); });
      el.appendChild(row);
    }
  }catch(e){}
}
function openArticle(i){
  const p=PUBS[i]; if(!p) return;
  const paras=(p.body||"").split(/\n\s*\n/).map(t=>"<p>"+esc(t).replace(/\n/g,"<br>")+"</p>").join("");
  const src=p.url?'<p><a style="color:var(--accent)" href="'+esc(p.url)+'" target="_blank" rel="noopener">Source ↗</a></p>':"";
  document.getElementById("reader").innerHTML='<div class="rbox"><button class="rclose" onclick="closeArticle()">✕</button>'+
    (p.image?'<div class="img" style="background-image:url(\''+esc(p.image)+'\')"></div>':"")+
    '<div class="rinner"><h1>'+esc(p.title)+"</h1><div class='rm'>"+(p.cat?esc(p.cat)+" · ":"")+fmtDate(p.ts)+" · AI Radar</div>"+
    "<div class='body'>"+paras+src+"</div></div></div>";
  document.getElementById("reader").hidden=false; document.body.style.overflow="hidden";
}
function closeArticle(){ document.getElementById("reader").hidden=true; document.body.style.overflow=""; }
document.getElementById("reader").addEventListener("click",e=>{ if(e.target.id==="reader") closeArticle(); });

/* footer section links -> filter the feed */
function footerSections(){
  const el=document.getElementById("fsections");
  Object.entries(PILLARS).slice(0,8).forEach(([k,v])=>{ const b=document.createElement("button"); b.className="lk";
    b.textContent=v; b.onclick=()=>{ pillar=+k; shown=PAGE; navBar(); render(); window.scrollTo({top:0,behavior:"smooth"}); };
    el.appendChild(b); });
}
/* static pages (About / Privacy / Terms ...) shown in the reader overlay */
const CONTACT="__EMAIL__";
const PAGES={
  about:["About AI Radar",
    "<p>AI Radar is an independent publication that tracks the fast-moving world of artificial intelligence. Every 30 minutes we scan hundreds of trusted sources — company blogs, research labs, news outlets and developer communities — and surface the stories that matter, with a direct link to every original source.</p><p>Our goal is simple: help you stay first. Whether you build with AI, invest in it, report on it or are just curious, AI Radar gives you a single, fast, no-noise view of what just happened.</p><p>AI Radar is created and edited by <a style='color:var(--accent)' href='https://x.com/aixahmad' target='_blank' rel='noopener'>@aixahmad</a>.</p>"],
  how:["How AI Radar works",
    "<p><b>1. We collect.</b> Our system continuously pulls headlines from a wide list of AI sources around the clock.</p><p><b>2. We organise.</b> Stories are sorted into sections (new tools &amp; models, AI in coding, research, health, defense and more) and de-duplicated, so a story covered by many outlets shows its source count.</p><p><b>3. We surface.</b> Trending topics and the most-covered stories rise to the top. Editor-picked features appear under “Latest from AI Radar”.</p><p><b>4. You read.</b> Click any headline to go straight to the original publisher. We never hide the source.</p><p>The feed refreshes every 30 minutes, automatically.</p>"],
  editorial:["Editorial standards",
    "<p>AI Radar aggregates and curates; it does not alter the words of the original publishers. Headlines and short excerpts are shown for identification and always link back to the source.</p><p>Featured articles written by our team are based only on the underlying reporting — we do not fabricate facts, numbers or quotes. Corrections are made promptly; if you spot an error, please contact us.</p><p>We aim for a respectful tone and never mock real tragedy.</p>"],
  advertise:["Advertise &amp; partner",
    "<p>Interested in reaching an audience that lives and breathes AI? AI Radar offers sponsorships, newsletter placements and content partnerships.</p><p>Reach out at <a style='color:var(--accent)' href='mailto:"+CONTACT+"'>"+CONTACT+"</a> or DM <a style='color:var(--accent)' href='https://x.com/aixahmad' target='_blank' rel='noopener'>@aixahmad</a> on X.</p>"],
  contact:["Send a tip",
    "<p>Got a scoop, a launch, or a story we should be covering? We’d love to hear it.</p><p>Email <a style='color:var(--accent)' href='mailto:"+CONTACT+"'>"+CONTACT+"</a> or message <a style='color:var(--accent)' href='https://x.com/aixahmad' target='_blank' rel='noopener'>@aixahmad</a> on X. Tips can be sent confidentially.</p>"],
  privacy:["Privacy policy",
    "<p>AI Radar is built to respect your privacy. We do not require an account, we do not sell data, and we do not run invasive advertising trackers.</p><p>The site is served as static pages. Standard web-server logs (such as your browser type and approximate region) may be collected by our hosting provider for security and analytics in aggregate. We do not use this to identify you.</p><p>External links take you to third-party sites with their own privacy policies. Questions? Email <a style='color:var(--accent)' href='mailto:"+CONTACT+"'>"+CONTACT+"</a>.</p>"],
  terms:["Terms of use",
    "<p>AI Radar is provided “as is”, for informational purposes only. While we work to keep the feed accurate and current, we make no warranty as to completeness or accuracy and accept no liability for decisions made based on its content.</p><p>Headlines, excerpts and trademarks belong to their respective owners. AI Radar links to original sources and claims no ownership over third-party content. If you are a rights holder and would like a link or excerpt amended, contact <a style='color:var(--accent)' href='mailto:"+CONTACT+"'>"+CONTACT+"</a>.</p><p>By using this site you agree to these terms.</p>"],
  disclaimer:["Disclaimer",
    "<p>AI Radar is an independent news aggregator and is not affiliated with, endorsed by, or sponsored by any of the companies or publications whose stories it links to.</p><p>All product names, logos and brands are property of their respective owners. Content is aggregated automatically; the appearance of a source does not imply endorsement either way.</p>"],
};
function openPage(key){
  const p=PAGES[key]; if(!p) return;
  document.getElementById("reader").innerHTML='<div class="rbox"><button class="rclose" onclick="closeArticle()">✕</button>'+
    '<div class="rinner"><h1>'+p[0]+'</h1><div class="body">'+p[1]+'</div></div></div>';
  document.getElementById("reader").hidden=false; document.body.style.overflow="hidden";
}

const _qp=new URLSearchParams(location.search).get("q");
if(_qp){ q=_qp.trim(); document.getElementById("q").value=q; }
navBar(); trendsBar(); render(); loadFeatured(); footerSections();
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

    # --- structured data (helps Google understand the site / show rich results) ---
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
