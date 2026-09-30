"""Builds the private Studio (docs/studio.html) from studio/index.html +
app.css + app.js, baking in the latest news, the Agents & AI classification,
the content/ files and the access-code hash. The pipeline state itself
(candidates, drafts) is NOT baked in: the page loads it live from Firebase or
from docs/pipeline.json.

    python generate_studio.py
"""

import hashlib
import json
import os
from datetime import datetime, timezone

import agent_ai_radar
import config
import database
import scoring
from agents import angle, content, verify, writer
from agents.store import doc_id
from generate_site import _agent_date_label, _load_fburl, _load_passcode

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "studio")
OUT = os.path.join(ROOT, "docs", "studio.html")
MAX_STORIES = 900
MAX_AGENT = 400


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def collect():
    conn = database.connect()
    rows = conn.execute(
        "SELECT id, title, url, links, source, pillar, published, fetched, summary FROM items "
        "ORDER BY fetched DESC, COALESCE(published, fetched) DESC LIMIT ?", (MAX_STORIES,)
    ).fetchall()
    agent_rows = conn.execute(
        "SELECT title, url, source, published, fetched, summary, upvotes FROM agent_discoveries "
        "ORDER BY fetched DESC LIMIT ?", (MAX_AGENT,)
    ).fetchall()
    trends = scoring.compute_trends(conn)
    conn.close()
    hot = scoring.rising_terms(trends)[:15]
    chips = [t for t in trends if t["status"] in ("new", "rising")][:10]
    now = datetime.now(timezone.utc)

    news, agents, seen = [], [], set()
    for r in rows:
        links = json.loads(r["links"] or "[]")
        when = r["published"] or r["fetched"]
        summary = (r["summary"] or "")[:400]
        try:
            age_h = (now - datetime.fromisoformat(when)).total_seconds() / 3600
        except ValueError:
            age_h = 999
        score, _reasons, _local = scoring.audience_score(r["title"], r["pillar"], len(links), age_h, hot)
        key = doc_id(r["url"])
        news.append({"k": key, "t": r["title"], "u": r["url"], "s": r["source"], "p": r["pillar"],
                     "d": when, "l": links, "sc": score, "sm": summary})
        meta = agent_ai_radar.classify(r["title"], source=r["source"], url=r["url"], summary=summary, pillar=r["pillar"])
        if meta.get("relevant"):
            seen.add(key)
            agents.append({"k": key, "t": r["title"], "u": r["url"], "s": r["source"], "p": r["pillar"], "pub": when,
                           "sm": summary, "sc": score, "primary": meta["primary"], "tabs": meta.get("discovery_tabs", []),
                           "domains": meta.get("domains", [])})
    for r in agent_rows:
        key = doc_id(r["url"])
        if key in seen:
            continue
        summary = (r["summary"] or "")[:400]
        meta = agent_ai_radar.classify(r["title"], source=r["source"], url=r["url"], summary=summary, pillar=2)
        if not meta.get("relevant"):
            continue
        agents.append({"k": key, "t": r["title"], "u": r["url"], "s": r["source"], "p": 2,
                       "pub": r["published"] or r["fetched"], "sm": summary, "sc": int(r["upvotes"] or 0),
                       "primary": meta["primary"], "tabs": meta.get("discovery_tabs", []),
                       "domains": meta.get("domains", []), "dateLabel": _agent_date_label(r["source"])})
    return news, agents, chips, now


def generate():
    news, agents, chips, now = collect()
    code = _load_passcode()
    data = {
        "lockHash": hashlib.sha256(code.encode()).hexdigest() if code else "",
        "fbUrl": _load_fburl(),
        "updated": now.strftime("%d %b %Y, %H:%M UTC"),
        "cache": now.strftime("%Y%m%d%H%M"),
        "pillars": config.CATEGORIES,
        "topics": config.PIPELINE_TOPICS,
        "draftsPerRun": config.PIPELINE_DRAFTS_PER_RUN,
        "agentTabs": [list(t[:2]) for t in agent_ai_radar.DISCOVERY_TABS],
        "news": news, "agents": agents, "trends": chips,
        "content": {"hooks": content.hooks(), "rules": content.rules(),
                    "examples": content.examples(), "voice": content.voice()["raw"]},
        "mode": config.PIPELINE_MODE,
        "prompts": {"angle": angle.SYSTEM, "writer": writer.SYSTEM_HEAD, "judge": verify.JUDGE_SYSTEM},
    }
    page = (_read(os.path.join(SRC, "index.html"))
            .replace("/*__CSS__*/", _read(os.path.join(SRC, "app.css")))
            .replace("/*__JS__*/", _read(os.path.join(SRC, "app.js")))
            .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"docs/studio.html written: {len(news)} stories, {len(agents)} agent items, "
          f"{len(data['content']['hooks'])} hooks{' (locked)' if code else ' (NO passcode -> open)'}")


if __name__ == "__main__":
    generate()
