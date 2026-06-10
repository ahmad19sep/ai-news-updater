"""
AI News Radar - Web Dashboard (Phase 3)

Run:   python dashboard.py
Open:  http://localhost:5000

- All stories newest first, with "2 hours ago" timestamps
- Filter buttons per pillar + search box
- Extra source links shown when one story was covered by many sites
- "Done" button to mark stories you already covered
- "Get latest" button pulls the newest cloud database (git pull)
"""

import json
import subprocess
from datetime import datetime, timezone

from flask import Flask, redirect, render_template_string, request

import config
import database

app = Flask(__name__)

PAGE_SIZE = 60

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI News Radar</title>
<style>
  :root { --bg:#0f1217; --card:#171c24; --text:#e8eaed; --dim:#9aa3af;
          --accent:#4f9cff; --done:#3a4252; --border:#262d38; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
         font:15px/1.5 system-ui, "Segoe UI", sans-serif; }
  .wrap { max-width: 880px; margin: 0 auto; padding: 18px 14px 60px; }
  h1 { font-size:22px; margin:6px 0 14px; }
  h1 .dot { color:var(--accent); }
  .bar { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:14px; }
  .bar a, .bar button {
      background:var(--card); color:var(--text); border:1px solid var(--border);
      padding:6px 12px; border-radius:18px; text-decoration:none; font-size:13px;
      cursor:pointer; }
  .bar a.active { background:var(--accent); border-color:var(--accent); color:#fff; }
  form.search { display:flex; gap:8px; margin-bottom:18px; }
  form.search input { flex:1; background:var(--card); border:1px solid var(--border);
      color:var(--text); padding:9px 14px; border-radius:8px; font-size:14px; }
  form.search button { background:var(--accent); border:none; color:#fff;
      padding:9px 16px; border-radius:8px; cursor:pointer; }
  .card { background:var(--card); border:1px solid var(--border);
      border-radius:10px; padding:14px 16px; margin-bottom:10px; }
  .card.done { opacity:.45; }
  .card h2 { font-size:16px; margin:0 0 6px; line-height:1.35; }
  .card h2 a { color:var(--text); text-decoration:none; }
  .card h2 a:hover { color:var(--accent); }
  .meta { font-size:12.5px; color:var(--dim); display:flex; flex-wrap:wrap;
      gap:6px 14px; align-items:center; }
  .pill { background:#20283a; color:#9cc1ff; padding:2px 9px; border-radius:10px; }
  .extra { font-size:12.5px; margin-top:6px; }
  .extra a { color:var(--accent); text-decoration:none; margin-right:12px; }
  .donebtn { margin-left:auto; }
  .donebtn button { background:none; border:1px solid var(--border); color:var(--dim);
      border-radius:6px; padding:3px 10px; font-size:12px; cursor:pointer; }
  .donebtn button:hover { border-color:var(--accent); color:var(--accent); }
  .count { color:var(--dim); font-size:13px; margin:0 0 12px; }
  .pager { display:flex; gap:10px; justify-content:center; margin-top:18px; }
  .pager a { color:var(--accent); text-decoration:none; padding:8px 18px;
      border:1px solid var(--border); border-radius:8px; }
  .empty { color:var(--dim); text-align:center; padding:50px 0; }
</style>
</head>
<body>
<div class="wrap">
  <h1>AI News Radar <span class="dot">●</span></h1>

  <div class="bar">
    <a href="{{ url_for('index', q=q, done=done_filter) }}"
       class="{{ 'active' if not pillar }}">All</a>
    {% for num, name in pillars.items() %}
      <a href="{{ url_for('index', pillar=num, q=q, done=done_filter) }}"
         class="{{ 'active' if pillar == num }}">{{ name }}</a>
    {% endfor %}
    <a href="{{ url_for('index', pillar=pillar, q=q, done='hide' if done_filter != 'hide' else '') }}"
       class="{{ 'active' if done_filter == 'hide' }}">Hide covered</a>
    <form method="post" action="{{ url_for('update') }}" style="margin:0">
      <button title="Pull the newest news from the cloud">&#8635; Get latest</button>
    </form>
  </div>

  <form class="search" method="get">
    {% if pillar %}<input type="hidden" name="pillar" value="{{ pillar }}">{% endif %}
    {% if done_filter %}<input type="hidden" name="done" value="{{ done_filter }}">{% endif %}
    <input name="q" value="{{ q }}" placeholder="Search stories... (e.g. Gemini, Altman, robot)">
    <button>Search</button>
  </form>

  <p class="count">{{ total }} stories{% if q %} for "{{ q }}"{% endif %}
     {% if pillar %} in {{ pillars[pillar] }}{% endif %}</p>

  {% for it in items %}
  <div class="card {{ 'done' if it.done }}">
    <h2><a href="{{ it.url }}" target="_blank" rel="noopener">{{ it.title }}</a></h2>
    <div class="meta">
      <span class="pill">{{ pillars[it.pillar] }}</span>
      <span>{{ it.source }}</span>
      <span>{{ it.ago }}</span>
      <span class="donebtn">
        <form method="post" action="{{ url_for('toggle_done', item_id=it.id) }}">
          <input type="hidden" name="back" value="{{ request.full_path }}">
          <button>{{ 'undo' if it.done else 'done ✓' }}</button>
        </form>
      </span>
    </div>
    {% if it.extra_links %}
    <div class="extra">also covered by:
      {% for l in it.extra_links %}
        <a href="{{ l.url }}" target="_blank" rel="noopener">{{ l.source }}</a>
      {% endfor %}
    </div>
    {% endif %}
  </div>
  {% else %}
  <div class="empty">No stories found. Try "Get latest" or another search.</div>
  {% endfor %}

  <div class="pager">
    {% if page > 1 %}
      <a href="{{ url_for('index', pillar=pillar, q=q, done=done_filter, page=page-1) }}">&larr; Newer</a>
    {% endif %}
    {% if has_more %}
      <a href="{{ url_for('index', pillar=pillar, q=q, done=done_filter, page=page+1) }}">Older &rarr;</a>
    {% endif %}
  </div>
</div>
</body>
</html>
"""


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
    items = []
    for r in rows[:PAGE_SIZE]:
        items.append({
            "id": r["id"], "title": r["title"], "url": r["url"],
            "source": r["source"], "pillar": r["pillar"], "done": r["done"],
            "ago": time_ago(r["published"] or r["fetched"]),
            "extra_links": json.loads(r["links"] or "[]"),
        })

    return render_template_string(
        TEMPLATE, items=items, pillars=config.CATEGORIES, pillar=pillar,
        q=q, done_filter=done_filter, page=page, has_more=has_more, total=total,
    )


@app.route("/done/<int:item_id>", methods=["POST"])
def toggle_done(item_id):
    conn = database.connect()
    conn.execute("UPDATE items SET done = 1 - done WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    back = request.form.get("back") or "/"
    return redirect(back)


@app.route("/update", methods=["POST"])
def update():
    """Pull the newest database that the cloud server saved to GitHub."""
    try:
        subprocess.run(["git", "pull", "--ff-only"], cwd=app.root_path,
                       timeout=60, capture_output=True)
    except Exception:
        pass  # offline is fine - just show what we have
    return redirect("/")


if __name__ == "__main__":
    print("AI News Radar dashboard -> http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
