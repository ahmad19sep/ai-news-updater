"""
AI News Radar - Creator Studio (Phase B)

Run:   python dashboard.py
Open:  http://localhost:5000

Three tabs:
  News       - all stories (filters, search, done marks) + "Plan video" button
  Planner    - your video board: Idea -> Script -> Record -> Edit -> Uploaded -> Published
  Video Prep - paste a story link -> research brief + a ready prompt to copy into Claude
"""

import json
import re
import subprocess
from datetime import datetime, timezone
from html.parser import HTMLParser

import requests
from flask import Flask, redirect, render_template_string, request

import config
import database

app = Flask(__name__)

PAGE_SIZE = 60

STAGES = ["idea", "script", "record", "edit", "uploaded", "published"]
STAGE_NAMES = {
    "idea": "💡 Idea", "script": "✍️ Script", "record": "🎥 Record",
    "edit": "✂️ Edit", "uploaded": "⬆️ Uploaded", "published": "✅ Published",
}

BASE_CSS = """
  :root { --bg:#0f1217; --card:#171c24; --text:#e8eaed; --dim:#9aa3af;
          --accent:#4f9cff; --border:#262d38; --gold:#e0c36b; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
         font:15px/1.5 system-ui, "Segoe UI", sans-serif; }
  .wrap { max-width:1100px; margin:0 auto; padding:18px 14px 60px; }
  h1 { font-size:22px; margin:6px 0 14px; } h1 .dot { color:var(--accent); }
  .tabs { display:flex; gap:8px; margin-bottom:18px; }
  .tabs a { background:var(--card); color:var(--text); border:1px solid var(--border);
      padding:8px 18px; border-radius:8px; text-decoration:none; font-size:14px; }
  .tabs a.active { background:var(--accent); border-color:var(--accent); color:#fff; }
  .bar { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:14px; }
  .bar a, .bar button { background:var(--card); color:var(--text);
      border:1px solid var(--border); padding:6px 12px; border-radius:18px;
      text-decoration:none; font-size:13px; cursor:pointer; }
  .bar a.active { background:var(--accent); border-color:var(--accent); color:#fff; }
  .card { background:var(--card); border:1px solid var(--border);
      border-radius:10px; padding:14px 16px; margin-bottom:10px; }
  .card.done { opacity:.45; }
  .card h2 { font-size:16px; margin:0 0 6px; line-height:1.35; }
  .card h2 a { color:var(--text); text-decoration:none; }
  .card h2 a:hover { color:var(--accent); }
  .meta { font-size:12.5px; color:var(--dim); display:flex; flex-wrap:wrap;
      gap:6px 14px; align-items:center; }
  .pill { background:#20283a; color:#9cc1ff; padding:2px 9px; border-radius:10px; }
  button.small, .meta form button { background:none; border:1px solid var(--border);
      color:var(--dim); border-radius:6px; padding:3px 10px; font-size:12px; cursor:pointer; }
  button.small:hover, .meta form button:hover { border-color:var(--accent); color:var(--accent); }
  input, textarea, select { background:#11151c; border:1px solid var(--border);
      color:var(--text); padding:8px 12px; border-radius:8px; font-size:14px; }
  .btn { background:var(--accent); border:none; color:#fff; padding:9px 16px;
      border-radius:8px; cursor:pointer; font-size:14px; }
"""

LAYOUT_TOP = """
<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI News Radar Studio</title><style>{css}{extra_css}</style></head><body>
<div class="wrap">
  <h1>AI News Radar Studio <span class="dot">●</span></h1>
  <div class="tabs">
    <a href="/" class="{news_active}">📰 News</a>
    <a href="/studio" class="{studio_active}">🎬 Planner</a>
    <a href="/prep" class="{prep_active}">📝 Video Prep</a>
  </div>
"""

# ---------------------------------------------------------------- News tab

NEWS_TMPL = """
  <div class="bar">
    <a href="{{ url_for('index', q=q, done=done_filter) }}" class="{{ 'active' if not pillar }}">All</a>
    {% for num, name in pillars.items() %}
      <a href="{{ url_for('index', pillar=num, q=q, done=done_filter) }}"
         class="{{ 'active' if pillar == num }}">{{ name }}</a>
    {% endfor %}
    <a href="{{ url_for('index', pillar=pillar, q=q, done='hide' if done_filter != 'hide' else '') }}"
       class="{{ 'active' if done_filter == 'hide' }}">Hide covered</a>
    <form method="post" action="{{ url_for('update') }}" style="margin:0">
      <button>&#8635; Get latest</button>
    </form>
  </div>
  <form style="display:flex;gap:8px;margin-bottom:14px" method="get">
    {% if pillar %}<input type="hidden" name="pillar" value="{{ pillar }}">{% endif %}
    <input style="flex:1" name="q" value="{{ q }}" placeholder="Search stories...">
    <button class="btn">Search</button>
  </form>
  <p style="color:var(--dim);font-size:13px">{{ total }} stories</p>
  {% for it in items %}
  <div class="card {{ 'done' if it.done }}">
    <h2><a href="{{ it.url }}" target="_blank" rel="noopener">{{ it.title }}</a></h2>
    <div class="meta">
      <span class="pill">{{ pillars[it.pillar] }}</span>
      <span>{{ it.source }}</span><span>{{ it.ago }}</span>
      <span style="margin-left:auto;display:flex;gap:6px">
        <form method="post" action="{{ url_for('plan_new') }}">
          <input type="hidden" name="title" value="{{ it.title }}">
          <input type="hidden" name="url" value="{{ it.url }}">
          <button title="Add to your video planner">🎬 Plan</button>
        </form>
        <form method="post" action="{{ url_for('toggle_done', item_id=it.id) }}">
          <input type="hidden" name="back" value="{{ request.full_path }}">
          <button>{{ 'undo' if it.done else 'done ✓' }}</button>
        </form>
      </span>
    </div>
    {% if it.extra_links %}
    <div style="font-size:12.5px;margin-top:6px">also covered by:
      {% for l in it.extra_links %}
        <a style="color:var(--accent);text-decoration:none;margin-right:12px"
           href="{{ l.url }}" target="_blank">{{ l.source }}</a>
      {% endfor %}
    </div>
    {% endif %}
  </div>
  {% else %}<p style="color:var(--dim);text-align:center;padding:40px">No stories found.</p>{% endfor %}
  <div style="display:flex;gap:10px;justify-content:center;margin-top:18px">
    {% if page > 1 %}<a class="btn" href="{{ url_for('index', pillar=pillar, q=q, done=done_filter, page=page-1) }}">&larr; Newer</a>{% endif %}
    {% if has_more %}<a class="btn" href="{{ url_for('index', pillar=pillar, q=q, done=done_filter, page=page+1) }}">Older &rarr;</a>{% endif %}
  </div>
</div></body></html>
"""

# ------------------------------------------------------------- Planner tab

STUDIO_CSS = """
  .board { display:flex; gap:12px; overflow-x:auto; padding-bottom:20px; }
  .col { min-width:240px; width:240px; flex-shrink:0; }
  .col h3 { font-size:14px; color:var(--dim); margin:0 0 10px; }
  .pcard { background:var(--card); border:1px solid var(--border); border-radius:10px;
           padding:10px 12px; margin-bottom:10px; font-size:13.5px; }
  .pcard .t { font-weight:600; margin-bottom:6px; line-height:1.3; }
  .pcard a { color:var(--accent); font-size:12px; text-decoration:none; }
  .pcard .row { display:flex; gap:6px; margin-top:8px; flex-wrap:wrap; }
  .pcard textarea { width:100%; min-height:42px; font-size:12.5px; margin-top:6px; }
  .pcard input[type=date], .pcard select { font-size:12px; padding:4px 8px; }
  .addform { display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; }
  .addform input[name=title] { flex:1; min-width:240px; }
"""

STUDIO_TMPL = """
  <form class="addform" method="post" action="{{ url_for('plan_new') }}">
    <input name="title" placeholder="New video idea (or use 🎬 Plan on any news story)" required>
    <input name="url" placeholder="link (optional)" style="width:220px">
    <button class="btn">+ Add idea</button>
  </form>
  <div class="board">
    {% for stage in stages %}
    <div class="col">
      <h3>{{ stage_names[stage] }} ({{ plans_by_stage[stage]|length }})</h3>
      {% for p in plans_by_stage[stage] %}
      <div class="pcard">
        <div class="t">{{ p.title }}</div>
        {% if p.url %}<a href="{{ p.url }}" target="_blank">source link</a>{% endif %}
        <form method="post" action="{{ url_for('plan_update', plan_id=p.id) }}">
          <div class="row">
            <select name="platform">
              <option value="long" {{ 'selected' if p.platform=='long' }}>Long</option>
              <option value="short" {{ 'selected' if p.platform=='short' }}>Short</option>
              <option value="both" {{ 'selected' if p.platform=='both' }}>Both</option>
            </select>
            <input type="date" name="planned_date" value="{{ p.planned_date }}">
          </div>
          <textarea name="notes" placeholder="notes...">{{ p.notes }}</textarea>
          <div class="row"><button class="small">save</button></div>
        </form>
        <div class="row">
          {% if not loop0 %}{% endif %}
          <form method="post" action="{{ url_for('plan_move', plan_id=p.id) }}" style="display:flex;gap:6px">
            {% if stage != 'idea' %}<button class="small" name="dir" value="prev">&larr;</button>{% endif %}
            {% if stage != 'published' %}<button class="small" name="dir" value="next">&rarr;</button>{% endif %}
          </form>
          <a class="small" style="padding:3px 10px;border:1px solid var(--border);border-radius:6px;
             color:var(--gold);text-decoration:none;font-size:12px"
             href="{{ url_for('prep') }}?url={{ p.url|urlencode }}&title={{ p.title|urlencode }}">📝 prep</a>
          <form method="post" action="{{ url_for('plan_delete', plan_id=p.id) }}"
                onsubmit="return confirm('Delete this card?')">
            <button class="small">✕</button>
          </form>
        </div>
      </div>
      {% endfor %}
    </div>
    {% endfor %}
  </div>
</div></body></html>
"""

# ---------------------------------------------------------- Video Prep tab

PREP_CSS = """
  .brief { background:var(--card); border:1px solid var(--border); border-radius:10px;
           padding:16px 18px; margin-bottom:14px; }
  .brief h3 { margin:0 0 8px; font-size:15px; color:var(--gold); }
  .brief p, .brief li { font-size:13.5px; color:var(--text); }
  #prompt { width:100%; min-height:300px; font-family:Consolas, monospace; font-size:12.5px; }
  .copied { color:#7ee087; font-size:13px; margin-left:10px; }
"""

PREP_TMPL = """
  <p style="color:var(--dim);font-size:13.5px">Paste a story link. The tool fetches the article,
  finds related coverage from your archive, and builds a ready prompt -
  <b>copy it into your Claude app</b> to get the full script kit. No API needed.</p>
  <form style="display:flex;gap:8px;margin-bottom:18px" method="get">
    <input style="flex:1" name="url" value="{{ url }}" placeholder="https://... story link" required>
    <input name="title" value="{{ title }}" placeholder="title (optional)" style="width:220px">
    <button class="btn">Prepare</button>
  </form>

  {% if brief %}
  <div class="brief">
    <h3>📋 Research brief</h3>
    <p><b>{{ brief.title }}</b></p>
    {% if brief.note %}<p style="color:var(--dim)">{{ brief.note }}</p>{% endif %}
    {% if brief.text %}<p>{{ brief.text[:600] }}{% if brief.text|length > 600 %}...{% endif %}</p>{% endif %}
    {% if brief.related %}
    <p style="margin-bottom:4px"><b>Related coverage in your archive:</b></p>
    <ul>
      {% for r in brief.related %}
      <li><a style="color:var(--accent)" href="{{ r.url }}" target="_blank">{{ r.title }}</a>
          <span style="color:var(--dim)">({{ r.source }})</span></li>
      {% endfor %}
    </ul>
    {% endif %}
  </div>
  <div class="brief">
    <h3>🤖 Prompt for Claude <button class="small" onclick="copyPrompt()">📋 Copy</button>
        <span id="ok" class="copied"></span></h3>
    <textarea id="prompt" readonly>{{ prompt }}</textarea>
  </div>
  <script>
    function copyPrompt() {
      navigator.clipboard.writeText(document.getElementById("prompt").value)
        .then(() => document.getElementById("ok").textContent = "copied! paste it in Claude");
    }
  </script>
  {% endif %}
</div></body></html>
"""


# ---------------------------------------------------------------- helpers

def layout_vars(active, extra_css=""):
    return dict(
        css=BASE_CSS, extra_css=extra_css,
        news_active="active" if active == "news" else "",
        studio_active="active" if active == "studio" else "",
        prep_active="active" if active == "prep" else "",
    )


def render(body_tmpl, active, extra_css="", **kw):
    # Format only the layout part - the body contains Jinja {% %} blocks
    # that Python's .format() must never touch.
    top = LAYOUT_TOP.format(**layout_vars(active, extra_css))
    return render_template_string(top + body_tmpl, **kw)


def time_ago(iso_str):
    if not iso_str:
        return ""
    try:
        then = datetime.fromisoformat(iso_str)
        if then.tzinfo is None:
            then = then.replace(tzinfo=timezone.utc)
    except ValueError:
        return ""
    secs = (datetime.now(timezone.utc) - then).total_seconds()
    if secs < 3600:
        return f"{max(1, int(secs // 60))} min ago"
    if secs < 86400:
        return f"{int(secs // 3600)} hours ago"
    return f"{int(secs // 86400)} days ago"


class _TextGrabber(HTMLParser):
    """Pull readable paragraphs out of an article page (no extra libraries)."""
    SKIP = {"script", "style", "nav", "footer", "header", "aside", "form"}

    def __init__(self):
        super().__init__()
        self.parts, self._stack, self._in_p = [], [], False
        self.page_title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._stack.append(tag)
        elif tag == "p":
            self._in_p = True
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if self._stack and tag == self._stack[-1]:
            self._stack.pop()
        elif tag == "p":
            self._in_p = False
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.page_title += data
        if self._in_p and not self._stack:
            text = data.strip()
            if text:
                self.parts.append(text)


def fetch_article(url):
    """Return (title, text, note). Best effort - some sites block robots."""
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        resp.raise_for_status()
    except Exception as e:
        return "", "", f"Could not open the page ({type(e).__name__}). Open the link yourself and copy 2-3 main paragraphs into Claude."
    grabber = _TextGrabber()
    try:
        grabber.feed(resp.text)
    except Exception:
        pass
    text = " ".join(grabber.parts)
    text = re.sub(r"\s+", " ", text).strip()[:6000]
    title = re.sub(r"\s+", " ", grabber.page_title).strip()
    note = ""
    if len(text) < 400:
        note = ("The site did not give full text (paywall or blocking). "
                "Open the link, copy the main points, and add them to the prompt.")
    return title, text, note


_WORD_RE = re.compile(r"[a-zA-Z0-9]{3,}")
_COMMON = {"the", "and", "for", "with", "that", "this", "from", "what", "how",
           "why", "new", "its", "has", "have", "are", "was", "will", "can",
           "you", "your", "says", "after", "about", "over", "into", "more"}


def related_stories(conn, title, exclude_url, limit=6):
    """Find archive stories sharing 2+ meaningful words with the title."""
    words = {w.lower() for w in _WORD_RE.findall(title)} - _COMMON
    if not words:
        return []
    rows = conn.execute(
        "SELECT title, url, source FROM items ORDER BY fetched DESC LIMIT 800"
    ).fetchall()
    scored = []
    for r in rows:
        if r["url"] == exclude_url:
            continue
        rw = {w.lower() for w in _WORD_RE.findall(r["title"])} - _COMMON
        common = len(words & rw)
        if common >= 2:
            scored.append((common, dict(r)))
    scored.sort(key=lambda x: -x[0])
    return [s[1] for s in scored[:limit]]


def build_prompt(title, text, related, url):
    rel_lines = "\n".join(f"- {r['title']} ({r['source']}) {r['url']}" for r in related)
    return f"""You are my video scriptwriter for my AI news YouTube channel. My audience is Pakistan and India - simple people who love AI news in easy Roman Urdu/Hindi.

THE STORY: {title}
SOURCE LINK: {url}

ARTICLE TEXT:
{text if text else "(could not fetch - I will paste key points below)"}

RELATED COVERAGE (for extra angles):
{rel_lines if rel_lines else "(none found)"}

CREATE FOR ME:

1. LONG VIDEO SCRIPT (5-8 minutes, Roman Urdu/Hindi):
   - Hook in first 10 seconds (a question or shocking fact)
   - Explain the story simply, like talking to a friend
   - Why it matters for normal people in Pakistan/India
   - My opinion section (leave a placeholder for me)
   - Ending with subscribe call-to-action

2. SHORT/REEL SCRIPT (45-60 seconds, Roman Urdu/Hindi):
   - Hook -> 3 punchy facts -> strong ending line

3. FIVE TITLE OPTIONS (mix Roman Urdu + English keywords people search)

4. YOUTUBE DESCRIPTION (2-3 lines + hashtags + 15 SEO tags)

5. THREE THUMBNAIL TEXT IDEAS (max 4 words each, curiosity-making)

Keep all language SIMPLE. Avoid difficult English words. Energy high."""


# ----------------------------------------------------------------- routes

@app.route("/")
def index():
    pillar = request.args.get("pillar", type=int)
    q = request.args.get("q", "").strip()
    done_filter = request.args.get("done", "")
    page = max(1, request.args.get("page", 1, type=int))

    where, params = [], []
    if pillar:
        where.append("pillar = ?")
        params.append(pillar)
    if q:
        where.append("title LIKE ?")
        params.append(f"%{q}%")
    if done_filter == "hide":
        where.append("done = 0")
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    conn = database.connect()
    total = conn.execute(f"SELECT COUNT(*) AS n FROM items {where_sql}", params).fetchone()["n"]
    rows = conn.execute(
        f"SELECT * FROM items {where_sql} "
        "ORDER BY COALESCE(published, fetched) DESC LIMIT ? OFFSET ?",
        params + [PAGE_SIZE + 1, (page - 1) * PAGE_SIZE],
    ).fetchall()
    conn.close()

    has_more = len(rows) > PAGE_SIZE
    items = [{
        "id": r["id"], "title": r["title"], "url": r["url"],
        "source": r["source"], "pillar": r["pillar"], "done": r["done"],
        "ago": time_ago(r["published"] or r["fetched"]),
        "extra_links": json.loads(r["links"] or "[]"),
    } for r in rows[:PAGE_SIZE]]

    return render(NEWS_TMPL, "news", items=items, pillars=config.CATEGORIES,
                  pillar=pillar, q=q, done_filter=done_filter, page=page,
                  has_more=has_more, total=total)


@app.route("/done/<int:item_id>", methods=["POST"])
def toggle_done(item_id):
    conn = database.connect()
    conn.execute("UPDATE items SET done = 1 - done WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(request.form.get("back") or "/")


@app.route("/update", methods=["POST"])
def update():
    try:
        subprocess.run(["git", "pull", "--ff-only"], cwd=app.root_path,
                       timeout=60, capture_output=True)
    except Exception:
        pass
    return redirect("/")


@app.route("/studio")
def studio():
    conn = database.connect()
    rows = conn.execute("SELECT * FROM plans ORDER BY updated DESC").fetchall()
    conn.close()
    plans_by_stage = {s: [] for s in STAGES}
    for r in rows:
        plans_by_stage.get(r["stage"], plans_by_stage["idea"]).append(dict(r))
    return render(STUDIO_TMPL, "studio", extra_css=STUDIO_CSS,
                  stages=STAGES, stage_names=STAGE_NAMES,
                  plans_by_stage=plans_by_stage)


@app.route("/plan/new", methods=["POST"])
def plan_new():
    title = request.form.get("title", "").strip()
    url = request.form.get("url", "").strip()
    if title:
        now = datetime.now(timezone.utc).isoformat()
        conn = database.connect()
        conn.execute(
            "INSERT INTO plans (title, url, created, updated) VALUES (?, ?, ?, ?)",
            (title, url, now, now))
        conn.commit()
        conn.close()
    return redirect("/studio")


@app.route("/plan/move/<int:plan_id>", methods=["POST"])
def plan_move(plan_id):
    direction = request.form.get("dir")
    conn = database.connect()
    row = conn.execute("SELECT stage FROM plans WHERE id = ?", (plan_id,)).fetchone()
    if row:
        i = STAGES.index(row["stage"]) if row["stage"] in STAGES else 0
        i = min(len(STAGES) - 1, i + 1) if direction == "next" else max(0, i - 1)
        conn.execute("UPDATE plans SET stage = ?, updated = ? WHERE id = ?",
                     (STAGES[i], datetime.now(timezone.utc).isoformat(), plan_id))
        conn.commit()
    conn.close()
    return redirect("/studio")


@app.route("/plan/update/<int:plan_id>", methods=["POST"])
def plan_update(plan_id):
    conn = database.connect()
    conn.execute(
        "UPDATE plans SET notes = ?, platform = ?, planned_date = ?, updated = ? WHERE id = ?",
        (request.form.get("notes", ""), request.form.get("platform", "both"),
         request.form.get("planned_date", ""),
         datetime.now(timezone.utc).isoformat(), plan_id))
    conn.commit()
    conn.close()
    return redirect("/studio")


@app.route("/plan/delete/<int:plan_id>", methods=["POST"])
def plan_delete(plan_id):
    conn = database.connect()
    conn.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
    conn.commit()
    conn.close()
    return redirect("/studio")


@app.route("/prep")
def prep():
    url = request.args.get("url", "").strip()
    title = request.args.get("title", "").strip()
    brief, prompt = None, ""
    if url:
        page_title, text, note = fetch_article(url)
        final_title = title or page_title or url
        conn = database.connect()
        related = related_stories(conn, final_title, url)
        conn.close()
        brief = {"title": final_title, "text": text, "note": note, "related": related}
        prompt = build_prompt(final_title, text, related, url)
    return render(PREP_TMPL, "prep", extra_css=PREP_CSS,
                  url=url, title=title, brief=brief, prompt=prompt)


if __name__ == "__main__":
    print("AI News Radar Studio -> http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
