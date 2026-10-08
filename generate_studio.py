"""Builds the Studio shell (docs/studio.html) from studio/index.html +
app.css + private-state.js + app.js, baking in news, the Agents & AI classification,
the content/ files and the access-code hash. The pipeline state itself
(candidates, drafts) is NOT baked in. studio_server.py serves this shell with
an authenticated private API. Static hosting retains the legacy Firebase/file
client for compatibility; its access-code gate is not database authorization.

    python generate_studio.py
"""

import hashlib
import json
import os
import re
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
                       "scoreKind": "engagement", "scoreLabel": "stars" if "github.com/" in r["url"] else "likes" if "huggingface.co/spaces/" in r["url"] else "votes",
                       "primary": meta["primary"], "tabs": meta.get("discovery_tabs", []),
                       "domains": meta.get("domains", []), "dateLabel": _agent_date_label(r["source"])})
    collected_at = max((r["fetched"] for r in rows if r["fetched"]), default="")
    return news, agents, chips, now, collected_at


def _deployed(pattern):
    """A value baked into the currently deployed page (new or old format)."""
    for name in ("studio.html", "studio-legacy.html"):
        try:
            with open(os.path.join(ROOT, "docs", name), encoding="utf-8") as f:
                m = re.search(pattern, f.read(200000))
            if m and m.group(1):
                return m.group(1)
        except FileNotFoundError:
            pass
    return ""


def generate():
    news, agents, chips, now, collected_at = collect()
    code = _load_passcode()
    lock_hash = hashlib.sha256(code.encode()).hexdigest() if code else ""
    fb_url = _load_fburl()
    if not lock_hash:
        # No secret on this machine: keep the deployed lock instead of shipping an
        # open page (a local rebuild must never unlock the studio).
        lock_hash = _deployed(r'"lockHash": ?"([0-9a-f]{64})"') or _deployed(r'const LOCKHASH = "([0-9a-f]{64})"')
    if not fb_url:
        fb_url = _deployed(r'"fbUrl": ?"(https://[^"]+)"') or _deployed(r'const FBURL = "(https://[^"]+)"')
    data = {
        "lockHash": lock_hash,
        "fbUrl": fb_url,
        "updated": now.strftime("%d %b %Y, %H:%M UTC"),
        "builtAt": now.isoformat(),
        "collectedAt": collected_at,
        "cache": now.strftime("%Y%m%d%H%M"),
        "pillars": config.CATEGORIES,
        "topics": config.PIPELINE_TOPICS,
        "draftsPerRun": config.PIPELINE_DRAFTS_PER_RUN,
        "agentTabs": [list(t[:2]) for t in agent_ai_radar.DISCOVERY_TABS],
        "news": news, "agents": agents, "trends": chips,
        "content": {"hooks": content.hooks(), "rules": content.rules(),
                    "examples": content.examples(), "voice": content.voice()["raw"],
                    "image_prompt": content.image_prompt()},
        "mode": config.PIPELINE_MODE,
        "prompts": {"angle": angle.SYSTEM, "writer": writer.SYSTEM_HEAD, "judge": verify.JUDGE_SYSTEM},
    }
    page = (_read(os.path.join(SRC, "index.html"))
            .replace("/*__CSS__*/", _read(os.path.join(SRC, "app.css")))
            .replace("/*__PRIVATE_JS__*/", _read(os.path.join(SRC, "private-state.js")))
            .replace("/*__JS__*/", _read(os.path.join(SRC, "app.js")))
            .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    lock_note = " (locked)" if code else " (locked with the deployed hash)" if lock_hash else " (NO passcode -> open)"
    print(f"docs/studio.html written: {len(news)} stories, {len(agents)} agent items, "
          f"{len(data['content']['hooks'])} hooks{lock_note}")


if __name__ == "__main__":
    generate()
