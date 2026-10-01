"""
AI Radar - PUBLIC news website generator (cream and forest-green editorial design).

Reads news.db and writes docs/index.html = an open, SEO-friendly AI-news site
styled with warm paper, forest-green accents, a custom radar identity, local
vector illustrations, featured stories, searchable news cards, saved stories,
a research grid, and an accessible article reader. Editor-published articles (from
Firebase /published) become the hero + related stories. The private studio is
generated separately to docs/studio.html.

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
SITE_URL = "https://ahmad19sep.github.io/ai-news-updater/"
# Paste the Google Search Console "HTML tag" verification code here, then re-run.
GSC_VERIFY = ""
SITE_DESC = ("Breaking artificial-intelligence news, every day: new models and tools, "
             "AI in science, business, and research — updated every 30 minutes, with links "
             "to the original sources.")
CONTACT_EMAIL = "get.shahzadsaddique@gmail.com"

# section kicker colours, keyed by category id — chosen for strong contrast on
# a white background (used as small uppercase labels, like a newspaper kicker).
CATCOLORS = {1: "#38664c", 2: "#556697", 3: "#9a6544", 4: "#697d43", 5: "#8b6541",
             6: "#6b5b87", 7: "#557d39", 8: "#986075", 9: "#6b5b87", 10: "#637156"}

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#f7f8f2">
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
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;450;500;550;600;650;700;750&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/public.css">
</head>
<body>
<a class="skip-link" href="#news">Skip to news</a>
<header class="mast">
  <div class="mastrow">
    <a class="brand" href="./" aria-label="AI Radar home"><span class="orb"><img src="assets/radar.svg" width="40" height="40" alt=""></span><span class="nm">AI<span class="brand-space"> </span>Radar<span class="brand-dot">.</span></span></a>
    <span class="mast-tag">A little signal. A lot less noise.</span>
    <div class="mright">
      <span class="live-pill"><span class="d"></span>Always scanning</span>
      <button class="header-save" id="savedToggle" aria-pressed="false" aria-label="Show saved stories"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M6 4h12v17l-6-4-6 4z"/></svg><span>Saved</span><span class="saved-count" id="savedCount">0</span></button>
      <a class="follow-btn" href="https://x.com/aixahmad" target="_blank" rel="noopener">Follow the radar <span aria-hidden="true">↗</span></a>
    </div>
  </div>
  <div class="nav-wrap"><nav class="cats" id="nav" aria-label="News topics"></nav></div>
</header>
<main class="wrap" id="main-content">
  <section class="intro" aria-labelledby="intro-title">
    <div><div class="eyebrow"><span class="eyebrow-line"></span>YOUR WINDOW INTO WHAT'S NEXT</div>
      <h1 id="intro-title">The future moves fast.<br>Stay <em>one story ahead.</em></h1>
      <p>The latest in AI, thoughtfully organized. Discover the tools, ideas,<br class="desktop-break"> and breakthroughs shaping tomorrow.</p>
    </div>
    <div class="intro-note"><span class="note-icon" aria-hidden="true">✳</span><span class="note-title">Curiosity, meet clarity.</span><span>Original sources. Fresh perspectives.<br>Your daily dose of the AI world.</span><a href="#news">Explore the latest <span aria-hidden="true">↓</span></a></div>
  </section>
  <div class="ticker"><span class="bk"><span class="d"></span>ON THE RADAR</span><div class="tkrow" id="ticker"></div><span class="tklive mono">__UPDATED__</span></div>
  <section class="featured-section" aria-labelledby="featured-title">
    <div class="section-line"><h2 id="featured-title">In the spotlight</h2><span class="section-note">The stories worth your attention <span aria-hidden="true">↗</span></span></div><div id="hero"></div>
  </section>
  <div class="statusrow"><span class="live"><span class="d"></span><span id="updlabel"></span></span><div class="chips" id="trends" aria-label="Trending topics"></div></div>
  <section class="news-section" id="news" aria-label="Browse AI news">
    <div class="searchrow" role="search"><div class="searchbox"><svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg><input id="q" type="search" aria-label="Search AI news" placeholder="Find your next rabbit hole. Search models, tools, or ideas…" autocomplete="off"><kbd class="search-shortcut" aria-hidden="true">/</kbd></div><button class="searchbtn" id="searchgo">Search <span aria-hidden="true">↗</span></button></div>
    <div class="cols">
      <div class="main">
        <div class="feedtop"><h2 class="sec-h" id="feed-title">The latest signals<span class="heading-dot"></span></h2><div class="fb" aria-label="Story filters"><button id="fLatest" class="on" aria-pressed="true">Latest</button><button id="fHot" aria-pressed="false">Most covered</button></div></div>
        <div class="count" id="count" role="status" aria-live="polite"></div><div class="feed" id="list"></div><button class="more" id="more" style="display:none">A little more discovery <span aria-hidden="true">↓</span></button><div id="researchwrap"></div>
      </div>
      <aside class="aside" aria-label="More to discover">
        <section class="sblock" id="trending"></section>
        <section class="briefcard"><div class="brief-label"><span aria-hidden="true">✳</span> STAY CURIOUS</div><h2 class="briefh">Your next big idea<br>starts with a little<br><em>discovery.</em></h2><p>Follow AI x Ahmad for a closer look at the tools and ideas moving AI forward.</p><a class="bbtn" href="https://youtube.com/@aixahmad" target="_blank" rel="noopener"><svg width="18" height="14" viewBox="0 0 24 18" fill="currentColor" aria-hidden="true"><rect width="24" height="18" rx="5"/><path d="m10 5 6 4-6 4z" fill="#1e4438"/></svg>Explore on YouTube <span aria-hidden="true">↗</span></a><a class="bbtn2" href="https://x.com/aixahmad" target="_blank" rel="noopener">Follow @aixahmad on X <span aria-hidden="true">↗</span></a><div class="bfoot">Good stories. Fresh perspectives.</div></section>
        <section class="sblock" id="tools"></section>
        <a class="about-note" href="#about" onclick="event.preventDefault();openPage('how')"><span class="note-icon" aria-hidden="true">⌁</span><span><b>A radar, not an echo chamber.</b><small>See how we find the signal.</small></span><span aria-hidden="true">↗</span></a>
      </aside>
    </div>
  </section>
</main>
<footer>
  <div class="ftop">
    <div class="fbrand"><a class="brand" href="./" aria-label="AI Radar home"><span class="orb"><img src="assets/radar.svg" width="40" height="40" alt=""></span><span class="nm">AI<span class="brand-space"> </span>Radar<span class="brand-dot">.</span></span></a><p>A clearer view of artificial intelligence.<br>Made for the endlessly curious.</p><div class="fsoc"><a href="https://x.com/aixahmad" target="_blank" rel="noopener" aria-label="AI x Ahmad on X">𝕏</a><a href="https://youtube.com/@aixahmad" target="_blank" rel="noopener" aria-label="AI x Ahmad on YouTube">▶</a><a href="mailto:__EMAIL__" aria-label="Email AI Radar">✉</a></div></div>
    <div class="fcol"><h4>Explore</h4><div id="fsections"></div></div>
    <div class="fcol"><h4>Behind the radar</h4><button class="lk" onclick="openPage('about')">Our story</button><button class="lk" onclick="openPage('how')">How it works</button><button class="lk" onclick="openPage('editorial')">Editorial standards</button><a href="studio.html">Newsroom ↗</a></div>
    <div class="fcol"><h4>Say hello</h4><a href="mailto:__EMAIL__">Get in touch ↗</a><a href="https://x.com/aixahmad" target="_blank" rel="noopener">@aixahmad on X</a><button class="lk" onclick="openPage('advertise')">Work with us</button><button class="lk" onclick="openPage('contact')">Share a story</button></div>
  </div>
  <div class="fbot"><span>© <span id="yr"></span> AI Radar. Independently curious.</span><span class="footer-signoff">Built for a world that doesn't stand still. <span aria-hidden="true">✳</span></span><span class="legal"><button onclick="openPage('privacy')">Privacy</button><button onclick="openPage('terms')">Terms</button><button onclick="openPage('disclaimer')">Disclaimer</button></span></div>
</footer>
<div id="reader" role="dialog" aria-modal="true" aria-label="AI Radar reader" tabindex="-1" hidden></div>
<script>
const PILLARS = __PILLARS__, ITEMS = __ITEMS__, TRENDS = __TRENDS__, COLORS = __COLORS__, PAGE = 18;
const PUBURL = "__FBURL__", CONTACT = "__EMAIL__";
let pillar = 0, hotOnly = false, savedOnly = false, q = "", shown = PAGE, PUBS = [], readerTrigger = null;
let SAVED = new Set();
try { const stored=JSON.parse(localStorage.getItem("air_saved")||"[]"); if(Array.isArray(stored))SAVED=new Set(stored.filter(x=>typeof x==="string")); } catch(e){}

document.getElementById("yr").textContent = new Date().getFullYear();
document.getElementById("updlabel").textContent = "Updated __UPDATED__ · " + ITEMS.length + " stories in view";

function ago(iso){ if(!iso) return ""; const s=(Date.now()-new Date(iso).getTime())/1000;
  if(s<3600) return Math.max(1,s/60|0)+" min ago"; if(s<86400) return (s/3600|0)+"h ago"; return (s/86400|0)+"d ago"; }
function esc(t){ const d=document.createElement("div"); d.textContent=t==null?"":t; return d.innerHTML.replace(/"/g,"&quot;").replace(/\x27/g,"&#39;"); }
function fmtDate(ts){ try{ return new Date(ts).toLocaleDateString("en-GB",{day:"numeric",month:"short"}); }catch(e){ return ""; } }
function col(p){ return COLORS[p] || (p===0?"#11151a":"#5A6872"); }
function colByName(nm){ for(const k in PILLARS){ if(PILLARS[k]===nm) return col(+k); } return "#11151a"; }
function catTag(t,c){ return '<span class="cat" style="color:'+c+'">'+esc(t)+'</span>'; }
function artwork(p){ return p===2?"code":p===9?"research":p===1?"models":"signal"; }
function thumbCSS(seed,hex){ return "background-image:url('assets/"+["models","signal","code","research"][Math.abs(seed)%4]+".svg');"; }
function sourceBadge(source){
 const label=String(source||"AI Radar"), key=label.toLowerCase();
 let mark=label.split(/\s+/).map(s=>s[0]).join("").slice(0,2).toUpperCase(),brand="generic";
 if(/openai|chatgpt/.test(key)){mark="◎";brand="openai";}
 else if(/anthropic|claude/.test(key)){mark="A";brand="anthropic";}
 else if(/google|deepmind/.test(key)){mark="G";brand="google";}
 else if(/meta|facebook/.test(key)){mark="∞";brand="meta";}
 else if(/microsoft/.test(key)){mark="⊞";brand="microsoft";}
 else if(/hugging/.test(key)){mark="H";brand="hugging";}
 else if(/github/.test(key)){mark="⌘";brand="github";}
 else if(/arxiv/.test(key)){mark="a";brand="arxiv";}
 return '<span class="source-logo '+brand+'" aria-hidden="true">'+esc(mark)+'</span>';
}
function scrollNews(){document.getElementById("news").scrollIntoView({behavior:"smooth",block:"start"});}
function bmIcon(on){ return '<svg width="13" height="13" viewBox="0 0 24 24" fill="'+(on?"currentColor":"none")+'" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>'; }

function filtered(){ const n=q.toLowerCase(); return ITEMS.filter(it =>
  (!pillar||it.p===pillar) && (!hotOnly||(it.l&&it.l.length)) && (!savedOnly||SAVED.has(it.u)) && (!n||(it.t+" "+it.s+" "+(PILLARS[it.p]||"")).toLowerCase().includes(n))); }

/* ---- breaking ticker ---- */
function renderTicker(){
  document.getElementById("ticker").innerHTML = ITEMS.slice(0,4)
    .map(it=>'<span class="tk"><span class="dot"></span>'+esc(it.t.slice(0,82))+'</span>').join("");
}

/* ---- category nav ---- */
function navBar(){
  const el=document.getElementById("nav"), restoreFocus=el.contains(document.activeElement); el.innerHTML="";
  const mk=(id,label)=>{ const b=document.createElement("button"); b.textContent=label; b.className=id===pillar?"active":""; b.setAttribute("aria-pressed",String(id===pillar));
    b.onclick=()=>{ pillar=id; shown=PAGE; navBar(); render(); scrollNews(); }; el.appendChild(b); };
  const labels={1:"Tools & models",2:"Coding",3:"People & ideas",4:"The future",5:"Defense",6:"Space",7:"Agriculture",8:"Health & science",9:"Research",10:"AI world"}; mk(0,"All stories"); Object.entries(PILLARS).forEach(([k,v])=>mk(+k,labels[k]||v));
  if(restoreFocus)el.querySelector(".active").focus({preventScroll:true});
}

/* ---- trend chips ---- */
function trendsBar(){ const el=document.getElementById("trends"); el.innerHTML="";
  TRENDS.forEach(t=>{ const c=document.createElement("button"); c.className="chip";
    c.textContent="# "+t.display;
    c.onclick=()=>{ q=t.display; document.getElementById("q").value=t.display; shown=PAGE; render(); scrollNews(); };
    el.appendChild(c); }); }

/* ---- hero (editor articles, else top news) ---- */
function heroEntries(){
  const out=[];
  PUBS.slice(0,4).forEach((p,i)=>out.push({ title:p.title, catName:(p.cat||"Featured"), pillar:Number(Object.keys(PILLARS).find(k=>PILLARS[k]===p.cat))||0, color:colByName(p.cat),
    source:"AI Radar", time:fmtDate(p.ts), dek:(p.body||"").replace(/\s+/g," ").trim().slice(0,170),
    img:p.image||"", seed:i, open:()=>openArticle(i) }));
  let i=0;
  while(out.length<4 && i<ITEMS.length){ const it=ITEMS[i];
    out.push({ title:it.t, catName:PILLARS[it.p], pillar:it.p, color:col(it.p), source:it.s, time:ago(it.d), dek:"",
      img:"", seed:i+3, open:()=>window.open(it.u,"_blank","noopener") }); i++; }
  return out;
}
function renderHero(){
 const entries=heroEntries(),el=document.getElementById("hero");
 if(!entries.length){el.innerHTML='<div class="empty"><b>The radar is warming up.</b><p>New stories will appear here as they arrive.</p></div>';return;}
 const lead=entries[0],L=document.createElement("button");L.className="lead";L.onclick=lead.open;
 L.innerHTML='<div class="limg"><img src="'+esc(lead.img||"assets/"+artwork(lead.pillar)+".svg")+'" alt="" fetchpriority="high" decoding="async"><span class="cover-label"><span class="d"></span>IN FOCUS</span><span class="cover-arrow" aria-hidden="true">↗</span></div>'+
 '<div class="lbody"><div class="lbadges">'+catTag(lead.catName,lead.color)+'<span class="leadbadge">Featured story</span></div><h3>'+esc(lead.title)+'</h3>'+(lead.dek?'<p class="ldek">'+esc(lead.dek)+'…</p>':'')+
 '<div class="lmeta">'+sourceBadge(lead.source)+'<span class="src">'+esc(lead.source)+'</span><span class="meta-dot">·</span><span>'+esc(lead.time)+'</span><span class="read-link">Read the story ↗</span></div></div>';
 const side=document.createElement("div");side.className="sidestack";
 entries.slice(1,4).forEach(s=>{const b=document.createElement("button");b.className="scardx";b.onclick=s.open;
 b.innerHTML='<span class="side-art"><img src="'+esc(s.img||"assets/"+artwork(s.pillar)+".svg")+'" alt="" loading="lazy" decoding="async"></span><span class="side-body"><span class="lbadges">'+catTag(s.catName,s.color)+'</span><span class="stitle">'+esc(s.title)+'</span><span class="smeta">'+sourceBadge(s.source)+'<span class="src">'+esc(s.source)+'</span><span>· '+esc(s.time)+'</span></span></span><span class="side-arrow" aria-hidden="true">↗</span>';side.appendChild(b);});
 const grid=document.createElement("div");grid.className="herogrid";grid.append(L,side);el.replaceChildren(grid);
}
function render(){
 const items=filtered();
 document.getElementById("feed-title").innerHTML=(savedOnly?"Your reading list":"The latest signals")+'<span class="heading-dot"></span>';
 document.getElementById("savedCount").textContent=SAVED.size;
 document.getElementById("savedToggle").setAttribute("aria-pressed",String(savedOnly));
 document.getElementById("count").textContent=items.length+" stories"+(q?' matching "'+q+'"':"")+(pillar?" · "+PILLARS[pillar]:"")+(hotOnly?" · covered by multiple sources":" · newest first");
 document.getElementById("fLatest").setAttribute("aria-pressed",String(!hotOnly));
 document.getElementById("fHot").setAttribute("aria-pressed",String(hotOnly));
 const list=document.getElementById("list");list.replaceChildren();
 if(!items.length){
 const empty=document.createElement("div");empty.className="empty";
 empty.innerHTML='<span class="empty-icon" aria-hidden="true">⌕</span><b>'+(savedOnly&&!SAVED.size?"A little space for your next discovery.":"No signals found here yet.")+'</b><p>'+(savedOnly&&!SAVED.size?"Save a story to come back to it later.":"Try another search or explore all topics.")+'</p><button class="reset-btn">Explore all stories ↗</button>';
 empty.querySelector("button").onclick=()=>{q="";pillar=0;savedOnly=false;hotOnly=false;shown=PAGE;document.getElementById("q").value="";document.getElementById("fLatest").classList.add("on");document.getElementById("fHot").classList.remove("on");navBar();render();};list.appendChild(empty);}
 items.slice(0,shown).forEach(it=>{
 const a=document.createElement("article");a.className="vrow";
 const hot=it.l&&it.l.length?'<span class="hotsrc"><span class="pip"></span>'+(it.l.length+1)+' sources</span>':'',on=SAVED.has(it.u);
 a.innerHTML='<a class="vthumb" href="'+esc(it.u)+'" target="_blank" rel="noopener" aria-label="'+esc("Read "+it.t)+'"><img src="assets/'+artwork(it.p)+'.svg" alt="" loading="lazy" decoding="async"><span aria-hidden="true">↗</span></a>'+
 '<div class="vmain"><div class="vtop">'+catTag(PILLARS[it.p],col(it.p))+hot+'</div><h3><a class="vtitle" href="'+esc(it.u)+'" target="_blank" rel="noopener">'+esc(it.t)+'</a></h3><div class="vmeta">'+sourceBadge(it.s)+'<span class="src">'+esc(it.s)+'</span><span class="meta-dot">·</span><span>'+ago(it.d)+'</span></div></div>'+
 '<button class="savebtn'+(on?" on":"")+'" aria-pressed="'+on+'" aria-label="'+esc((on?"Unsave ":"Save ")+it.t)+'" title="'+(on?"Unsave story":"Save for later")+'">'+bmIcon(on)+'</button>';
 a.querySelector(".savebtn").onclick=e=>{e.stopPropagation();toggleSave(it.u);const next=Array.from(list.querySelectorAll(".vtitle")).find(x=>x.getAttribute("href")===it.u);const focusTarget=next?next.closest(".vrow").querySelector(".savebtn"):list.querySelector(".savebtn,.reset-btn");if(focusTarget)focusTarget.focus({preventScroll:true});};
 list.appendChild(a);});
 document.getElementById("more").style.display=items.length>shown?"block":"none";
}
function toggleSave(u){if(SAVED.has(u))SAVED.delete(u);else SAVED.add(u);try{localStorage.setItem("air_saved",JSON.stringify([...SAVED]));}catch(e){}render();}

/* ---- research grid ---- */
function renderResearch(){
  const rs=ITEMS.filter(it=>it.p===9).slice(0,4);
  const w=document.getElementById("researchwrap");
  if(!rs.length){ w.innerHTML=""; return; }
  let h='<h2 class="sec-h research-heading">From the research desk<span class="heading-dot"></span></h2><div class="rgrid">';
  rs.forEach(it=>{ h+='<button class="rcard" data-u="'+esc(it.u)+'"><span class="rlabel">Research</span>'+
    '<div class="rtitle">'+esc(it.t)+'</div><div class="rmeta"><span class="src">'+esc(it.s)+'</span> · '+ago(it.d)+'</div></button>'; });
  w.innerHTML=h+"</div>";
  w.querySelectorAll(".rcard").forEach(b=>b.onclick=()=>window.open(b.dataset.u,"_blank","noopener"));
}

/* ---- sidebar: trending ---- */
function renderTrending(){
  const top=ITEMS.slice().sort((a,b)=>((b.l?b.l.length:0)-(a.l?a.l.length:0))).slice(0,5);
  let h='<h2 class="shead">Making waves <span aria-hidden="true">↗</span></h2><p class="sidebar-dek">The conversations picking up momentum.</p>';
  top.forEach((it,i)=>{ const rc=i===0?'#23644b':'#a4b2a8';
    h+='<button class="trow" data-u="'+esc(it.u)+'"><span class="trank" style="color:'+rc+'">'+String(i+1).padStart(2,'0')+'</span>'+
      '<div class="tbody"><div class="ttitle">'+esc(it.t)+'</div><div class="tmeta">'+esc(it.s)+' · '+ago(it.d)+'</div></div></button>'; });
  const el=document.getElementById("trending"); el.innerHTML=h;
  el.querySelectorAll(".trow").forEach(b=>b.onclick=()=>window.open(b.dataset.u,"_blank","noopener"));
}

/* ---- sidebar: new tools & models (category 1) ---- */
function renderTools(){
  const ts=ITEMS.filter(it=>it.p===1).slice(0,4);
  const el=document.getElementById("tools");
  if(!ts.length){ el.innerHTML=""; return; }
  const c=col(1);
  let h='<h2 class="shead">The tool shelf <span aria-hidden="true">⌘</span></h2><p class="sidebar-dek">Something new for your next project.</p>';
  ts.forEach(it=>{ const ini=sourceBadge(it.s);
    h+='<button class="toolrow2" data-u="'+esc(it.u)+'"><div class="ticon">'+ini+'</div>'+
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
const RTOP = '<div class="rtopbar"><button class="rback" onclick="closeArticle()">? Back</button>'+
  '<a class="brand" href="./" aria-label="AI Radar home"><span class="orb"><img src="assets/radar.svg" width="28" height="28" alt=""></span><span class="nm">AI<span class="brand-space"> </span>Radar<span class="brand-dot">.</span></span></a>'+
  '<span class="spacer"></span></div>';
function openArticle(i){
  const p=PUBS[i]; if(!p) return;
  const color=colByName(p.cat);
  const txt=(p.body||"");
  const paras=txt.split(/\n\s*\n/).map(t=>"<p>"+esc(t).replace(/\n/g,"<br>")+"</p>").join("");
  const mins=Math.max(1,Math.round(txt.split(/\s+/).filter(Boolean).length/200));
  const src=p.url?'<p style="margin-top:8px"><a class="srclink" href="'+esc(p.url)+'" target="_blank" rel="noopener">Read the original source ↗</a></p>':"";
  const rel=PUBS.map((x,j)=>({x,j})).filter(o=>o.j!==i).slice(0,3).map(o=>
    '<button class="relcard" onclick="openArticle('+o.j+')">'+
    catTag(o.x.cat||"Featured",colByName(o.x.cat))+'<div class="reltitle">'+esc(o.x.title)+'</div></button>').join("");
  document.getElementById("reader").innerHTML='<div class="rbox">'+RTOP+
    '<article class="rinner">'+catTag(p.cat||"Featured",color)+'<h1>'+esc(p.title)+'</h1>'+
    '<div class="rmeta"><span class="ravatar">A</span><div><div class="rauthor">AI Radar Desk</div><div class="rsub">AI Radar · '+fmtDate(p.ts)+' · '+mins+' min read</div></div></div></article>'+
    '<div class="rhero"><div class="rimg" style="'+(p.image?("background-image:url('"+esc(p.image)+"')"):thumbCSS(i,color))+'"></div></div>'+
    '<div class="rinner"><div class="rbody">'+paras+src+'</div>'+
    (rel?'<div class="sec-h" style="margin-top:42px">More from AI Radar</div><div class="relgrid">'+rel+'</div>':'')+
    '</div></div>';
  showReader();
  try{ history.replaceState(null,"","#a="+(p.id||"")); }catch(e){}
}
function showReader(){
 const rd=document.getElementById("reader");if(rd.hidden)readerTrigger=document.activeElement;
 rd.hidden=false;rd.scrollTop=0;document.body.style.overflow="hidden";
 document.querySelectorAll("body > header, body > main, body > footer").forEach(el=>el.inert=true);
 rd.querySelector(".rback").focus({preventScroll:true});
}
function closeArticle(){ document.getElementById("reader").hidden=true; document.body.style.overflow="";
 document.querySelectorAll("body > header, body > main, body > footer").forEach(el=>el.inert=false);
 if(readerTrigger&&readerTrigger.isConnected)readerTrigger.focus({preventScroll:true});
  try{ history.replaceState(null,"",location.pathname+location.search); }catch(e){} }
document.getElementById("reader").addEventListener("click",e=>{ if(e.target.id==="reader") closeArticle(); });
/* deep link: #a=<id> opens that article (used by shares) */
function openArticleFromHash(){
  const m=(location.hash||"").match(/a=([^&]+)/); if(!m) return;
  const idx=PUBS.findIndex(p=>String(p.id)===m[1]); if(idx>=0) openArticle(idx);
}

/* ---- footer section links ---- */
function footerSections(){
  const el=document.getElementById("fsections");
  Object.entries(PILLARS).slice(0,8).forEach(([k,v])=>{ const b=document.createElement("button"); b.className="lk"; b.textContent=v;
    b.onclick=()=>{ pillar=+k; shown=PAGE; navBar(); render(); scrollNews(); }; el.appendChild(b); });
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
  document.getElementById("reader").innerHTML='<div class="rbox">'+RTOP+
    '<article class="rinner"><h1>'+p[0]+'</h1><div class="rbody">'+p[1]+'</div></article></div>';
  showReader();
}
document.addEventListener("keydown",e=>{
 const rd=document.getElementById("reader");
 if(e.key==="Escape"&&!rd.hidden){closeArticle();return;}
 if(!rd.hidden&&e.key==="Tab"){
 const focusable=Array.from(rd.querySelectorAll('button,a[href],input,[tabindex="0"]')),first=focusable[0],last=focusable[focusable.length-1];
 if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
 else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}
 if(e.key==="/"&&rd.hidden&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)&&!document.activeElement.isContentEditable){e.preventDefault();document.getElementById("q").focus();}
});

/* ---- events + init ---- */
document.getElementById("savedToggle").onclick=()=>{savedOnly=!savedOnly;shown=PAGE;render();scrollNews();};
document.getElementById("q").addEventListener("keydown",e=>{if(e.key==="Enter"){render();scrollNews();}});

document.getElementById("q").addEventListener("input",e=>{ q=e.target.value.trim(); shown=PAGE; render(); });
document.getElementById("searchgo").onclick=()=>scrollNews();
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
