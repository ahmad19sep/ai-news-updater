"""Reads the news the hourly collector already saved (news.db) and hands the
pipeline what is new since the last triage."""

import json
from datetime import datetime, timedelta, timezone

import config
import database


def new_stories(conn, store, hours=None, limit=None):
    """Stories fetched in the lookback window that triage has not seen yet."""
    hours = hours or config.PIPELINE_TRIAGE_LOOKBACK_HOURS
    limit = limit or config.PIPELINE_TRIAGE_MAX_STORIES
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    rows = conn.execute(
        "SELECT id, title, url, links, source, pillar, published, fetched, summary, upvotes, comments "
        "FROM items WHERE fetched >= ? ORDER BY fetched DESC LIMIT ?", (cutoff, limit * 3)
    ).fetchall()
    seen = set(store.all("candidates"))
    seen |= set((store.get("settings", "triaged") or {}).get("ids") or [])
    out = []
    for r in rows:
        from agents.store import doc_id
        i = doc_id(r["url"])
        if i in seen:
            continue
        out.append({
            "id": i, "title": r["title"], "url": r["url"], "source": r["source"],
            "category": config.CATEGORIES.get(r["pillar"], "AI General News"),
            "published": r["published"] or r["fetched"], "fetched": r["fetched"],
            "summary": (r["summary"] or "")[:500],
            "links": json.loads(r["links"] or "[]"),
            "upvotes": r["upvotes"] or 0, "comments": r["comments"] or 0,
        })
        if len(out) >= limit:
            break
    return out


def remember_triaged(store, ids):
    """Stories scored below the keep threshold are not stored as candidates;
    remember their ids so they are not re-scored every run."""
    doc = store.get("settings", "triaged") or {"ids": []}
    known = list(doc.get("ids") or [])
    known.extend(i for i in ids if i not in known)
    store.put("settings", "triaged", {"ids": known[-3000:]})


def open_db():
    return database.connect()
