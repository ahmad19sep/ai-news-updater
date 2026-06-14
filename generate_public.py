"""
AI Radar - PUBLIC news website generator.

Reads news.db and writes docs/index.html = a clean, OPEN, SEO-friendly public
AI-news site (no login). It's an aggregator: every card links to the original
source. The private creator studio is generated separately to docs/studio.html.

Run:  python generate_public.py
"""

import html as _h
import json
import os
from datetime import datetime, timezone

import config
import database
import scoring

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
MAX_STORIES = 600          # public site stays fast
SITE_NAME = "AI Radar"
SITE_URL = "https://hafizahmad.com/"
SITE_DESC = ("The latest artificial-intelligence news in one place: new models and tools, "
             "AI in science, leaders, and research — updated every 30 minutes, with links "
             "to the original sources.")

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0b0f17">
<title>__SITE__ — Latest AI News, updated all day</title>
<meta name="description" content="__DESC__">
<link rel="canonical" href="__URL__">
<meta property="og:title" content="__SITE__ — Latest AI News">
<meta property="og:description" content="__DESC__">
<meta property="og:type" content="website">
<meta property="og:url" content="__URL__">
<meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<style>
  :root { --bg:#0b0f17; --surface:#121a26; --surface2:#18202e; --text:#e7ecf3;
          --dim:#97a1b2; --faint:#5f6b7e; --line:rgba(255,255,255,.08);
          --line2:rgba(255,255,255,.16); --accent:#22d3ee; --accent2:#6366f1;
          --orange:#fb923c; --green:#34d399;
          --grad:linear-gradient(135deg,#6366f1,#22d3ee);
          --display:"Space Grotesk", Inter, sans-serif; }
  * { box-sizing:border-box; }
  body { margin:0; background:radial-gradient(1100px 460px at 70% -10%, #16203a 0%, var(--bg) 55%);
         color:var(--text); font:15px/1.55 Inter, system-ui, sans-serif; -webkit-font-smoothing:antialiased; }
  a { color:var(--accent); }
  .wrap { max-width:960px; margin:0 auto; padding:0 16px 70px; }
  header { position:sticky; top:0; z-index:30; backdrop-filter:blur(12px);
           background:rgba(11,15,23,.72); border-bottom:1px solid var(--line); }
  .hrow { max-width:960px; margin:0 auto; padding:13px 16px; display:flex; align-items:center; gap:12px; }
  .logo { display:flex; align-items:center; gap:10px; font:800 18px var(--display); letter-spacing:-.02em;
          text-decoration:none; color:inherit; }
  .logo .orb { width:30px; height:30px; border-radius:9px; background:var(--grad);
          display:flex; align-items:center; justify-content:center; font-size:16px; }
  .social { margin-left:auto; display:flex; gap:8px; }
  .social a { color:var(--dim); text-decoration:none; font-size:13px; font-weight:600;
          border:1px solid var(--line); border-radius:999px; padding:6px 13px; }
  .social a:hover { color:var(--text); border-color:var(--line2); }
  .hero { text-align:center; padding:40px 0 14px; }
  .hero h1 { font:800 clamp(28px,5vw,44px) var(--display); letter-spacing:-.03em; margin:0 0 10px; }
  .hero h1 .g { background:var(--grad); -webkit-background-clip:text; background-clip:text; color:transparent; }
  .hero p { color:var(--dim); font-size:15.5px; margin:0 auto; max-width:520px; }
  .updated { color:var(--faint); font-size:12px; margin-top:12px; }
  .updated .live { display:inline-block; width:8px; height:8px; border-radius:50%; background:#22c55e;
          box-shadow:0 0 0 3px rgba(34,197,94,.2); animation:pulse 2s infinite; vertical-align:middle; margin-right:5px; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }
  .trends { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin:16px 0 4px; }
  .chip { background:rgba(52,211,153,.1); color:var(--green); border:1px solid rgba(52,211,153,.28);
          border-radius:999px; padding:5px 13px; font:500 12.5px Inter; cursor:pointer; }
  .chip:hover { background:rgba(52,211,153,.18); }
  .bar { display:flex; flex-wrap:wrap; gap:8px; margin:18px 0 6px; align-items:center; }
  .bar button, .bar select { background:var(--surface); color:var(--dim); border:1px solid var(--line);
          padding:7px 14px; border-radius:999px; font:500 12.5px Inter; cursor:pointer; }
  .bar button.active { background:var(--grad); border-color:transparent; color:#fff; font-weight:600; }
  .search { display:flex; margin:14px 0 4px; }
  .search input { flex:1; background:var(--surface); border:1px solid var(--line); color:var(--text);
          padding:11px 16px; border-radius:12px; font:14px Inter; outline:none; }
  .search input:focus { border-color:var(--accent2); box-shadow:0 0 0 3px rgba(99,102,241,.18); }
  .count { color:var(--faint); font-size:12.5px; margin:10px 2px; }
  .card { background:var(--surface); border:1px solid var(--line); border-radius:14px;
          padding:15px 18px; margin-bottom:11px; transition:.15s; }
  .card:hover { border-color:var(--line2); transform:translateY(-1px); }
  .card h2 { font-size:16px; font-weight:600; line-height:1.4; margin:0 0 8px; letter-spacing:-.01em; }
  .card h2 a { color:var(--text); text-decoration:none; }
  .card h2 a:hover { color:var(--accent); }
  .meta { font-size:12px; color:var(--dim); display:flex; flex-wrap:wrap; gap:6px 12px; align-items:center; }
  .pill { background:rgba(99,102,241,.15); color:#a5b4fc; padding:2.5px 10px; border-radius:999px; font-size:11px; font-weight:500; }
  .pill.hot { background:rgba(251,146,60,.14); color:var(--orange); }
  .extra { font-size:12px; margin-top:7px; color:var(--dim); }
  .extra a { text-decoration:none; margin-right:12px; }
  .more { display:block; margin:22px auto; background:var(--surface); color:var(--text); border:1px solid var(--line);
          padding:11px 32px; border-radius:999px; font:600 13px Inter; cursor:pointer; }
  .empty { color:var(--faint); text-align:center; padding:50px 0; }
  footer { border-top:1px solid var(--line); margin-top:30px; padding:24px 16px; text-align:center;
           color:var(--faint); font-size:12.5px; }
  footer a { color:var(--dim); text-decoration:none; margin:0 8px; }
</style>
</head>
<body>
<header>
  <div class="hrow">
    <a class="logo" href="/"><span class="orb">📡</span> __SITE__</a>
    <nav class="social">
      <a href="https://x.com/aixahmad" target="_blank" rel="noopener">𝕏</a>
      <a href="https://youtube.com/@aixahmad" target="_blank" rel="noopener">YouTube</a>
    </nav>
  </div>
</header>
<div class="wrap">
  <div class="hero">
    <h1>The World of <span class="g">AI</span>, every day</h1>
    <p>__DESC__</p>
    <div class="updated"><span class="live"></span> Updated __UPDATED__ · refreshes every 30 min</div>
  </div>
  <div class="trends" id="trends"></div>
  <div class="search"><input id="q" placeholder="Search AI news… models, tools, companies"></div>
  <div class="bar" id="bar"></div>
  <div class="count" id="count"></div>
  <div id="list"></div>
  <button class="more" id="more" style="display:none">Show more</button>
</div>
<footer>
  <div>© <span id="yr"></span> __SITE__ — AI news aggregator. Headlines link to original sources.</div>
  <div style="margin-top:8px">
    <a href="https://x.com/aixahmad" target="_blank" rel="noopener">@aixahmad on X</a> ·
    <a href="https://youtube.com/@aixahmad" target="_blank" rel="noopener">YouTube</a>
  </div>
</footer>
<script>
const PILLARS = __PILLARS__, ITEMS = __ITEMS__, TRENDS = __TRENDS__, PAGE = 40;
let pillar = 0, hotOnly = false, q = "", shown = PAGE;
document.getElementById("yr").textContent = new Date().getFullYear();
function ago(iso){ if(!iso) return ""; const s=(Date.now()-new Date(iso).getTime())/1000;
  if(s<3600) return Math.max(1,s/60|0)+" min ago"; if(s<86400) return (s/3600|0)+"h ago"; return (s/86400|0)+"d ago"; }
function esc(t){ const d=document.createElement("div"); d.textContent=t; return d.innerHTML; }
function filtered(){ const n=q.toLowerCase(); return ITEMS.filter(it =>
  (!pillar||it.p===pillar) && (!hotOnly||(it.l&&it.l.length)) && (!n||it.t.toLowerCase().includes(n))); }
function render(){
  const items=filtered();
  document.getElementById("count").textContent = items.length+" stories"+(q?' for "'+q+'"':"")+(pillar?" in "+PILLARS[pillar]:"");
  const list=document.getElementById("list");
  list.innerHTML = items.length?"":'<div class="empty">No stories found.</div>';
  items.slice(0,shown).forEach(it=>{
    const d=document.createElement("div"); d.className="card";
    let hot="",extra="";
    if(it.l&&it.l.length){ hot='<span class="pill hot">🔥 '+(it.l.length+1)+" sources</span>";
      extra='<div class="extra">also: '+it.l.slice(0,4).map(x=>'<a href="'+esc(x.url)+'" target="_blank" rel="noopener">'+esc(x.source)+"</a>").join("")+"</div>"; }
    d.innerHTML='<h2><a href="'+esc(it.u)+'" target="_blank" rel="noopener">'+esc(it.t)+"</a></h2>"+
      '<div class="meta"><span class="pill">'+PILLARS[it.p]+"</span>"+hot+"<span>"+esc(it.s)+"</span><span>"+ago(it.d)+"</span></div>"+extra;
    list.appendChild(d);
  });
  document.getElementById("more").style.display = items.length>shown?"block":"none";
}
function bar(){
  const el=document.getElementById("bar"); el.innerHTML="";
  const all=document.createElement("button"); all.textContent="All"; all.className=pillar?"":"active";
  all.onclick=()=>{pillar=0;shown=PAGE;bar();render();}; el.appendChild(all);
  const sel=document.createElement("select");
  sel.innerHTML='<option value="0">Categories…</option>'+Object.entries(PILLARS).map(([k,v])=>'<option value="'+k+'"'+(+k===pillar?" selected":"")+">"+v+"</option>").join("");
  sel.onchange=e=>{pillar=+e.target.value;shown=PAGE;bar();render();}; el.appendChild(sel);
  const hot=document.createElement("button"); hot.innerHTML="🔥 Hot"; hot.className=hotOnly?"active":"";
  hot.onclick=()=>{hotOnly=!hotOnly;shown=PAGE;bar();render();}; el.appendChild(hot);
}
function trendsBar(){ const el=document.getElementById("trends");
  TRENDS.forEach(t=>{ const c=document.createElement("button"); c.className="chip";
    c.innerHTML=(t.status==="new"?"🆕":"🚀")+" "+esc(t.display);
    c.onclick=()=>{q=t.display;document.getElementById("q").value=t.display;shown=PAGE;render();}; el.appendChild(c); }); }
document.getElementById("q").addEventListener("input",e=>{q=e.target.value.trim();shown=PAGE;render();});
document.getElementById("more").onclick=()=>{shown+=PAGE;render();};
trendsBar(); bar(); render();
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

    updated = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    html = (PAGE
            .replace("__SITE__", SITE_NAME)
            .replace("__URL__", SITE_URL)
            .replace("__DESC__", _h.escape(SITE_DESC, quote=True))
            .replace("__PILLARS__", json.dumps(config.CATEGORIES))
            .replace("__ITEMS__", json.dumps(items, ensure_ascii=False))
            .replace("__TRENDS__", json.dumps(chips, ensure_ascii=False))
            .replace("__UPDATED__", updated))

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Public site written: docs/index.html ({len(items)} stories)")


if __name__ == "__main__":
    generate()
