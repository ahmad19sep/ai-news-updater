"""
AI News Radar - Database
One small SQLite file. Stores every news item, prevents duplicates,
and slowly becomes your personal AI news archive.
"""

import json
import sqlite3
from datetime import datetime, timedelta, timezone

import config


def connect():
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            title     TEXT NOT NULL,
            url       TEXT NOT NULL UNIQUE,
            links     TEXT NOT NULL DEFAULT '[]',  -- extra links (JSON) when other sites cover the same story
            source    TEXT NOT NULL,
            pillar    INTEGER NOT NULL,
            published TEXT,                        -- original publish time (UTC ISO)
            fetched   TEXT NOT NULL,               -- when we saved it (UTC ISO)
            notified  INTEGER NOT NULL DEFAULT 0,  -- 0 = not yet sent to phone (Phase 2)
            done      INTEGER NOT NULL DEFAULT 0   -- 1 = you already made a video on this
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_items_fetched ON items(fetched)")
    conn.commit()
    return conn


def url_exists(conn, url):
    return conn.execute("SELECT 1 FROM items WHERE url = ?", (url,)).fetchone() is not None


def recent_items(conn, hours):
    """Items from the last N hours - used for duplicate detection."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    return conn.execute(
        "SELECT id, title, links FROM items WHERE fetched >= ?", (cutoff,)
    ).fetchall()


def add_item(conn, title, url, source, pillar, published):
    cur = conn.execute(
        "INSERT OR IGNORE INTO items (title, url, source, pillar, published, fetched) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (title, url, source, pillar, published,
         datetime.now(timezone.utc).isoformat()),
    )
    return cur.lastrowid


def add_link_to_item(conn, item_id, url, source):
    """Same story found on another site -> attach the extra link to the existing card."""
    row = conn.execute("SELECT links FROM items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        return
    links = json.loads(row["links"])
    if not any(l["url"] == url for l in links):
        links.append({"url": url, "source": source})
        conn.execute("UPDATE items SET links = ? WHERE id = ?",
                     (json.dumps(links), item_id))


def count_by_pillar(conn, since_hours=24):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).isoformat()
    rows = conn.execute(
        "SELECT pillar, COUNT(*) AS n FROM items WHERE fetched >= ? GROUP BY pillar",
        (cutoff,),
    ).fetchall()
    return {row["pillar"]: row["n"] for row in rows}


def total_count(conn):
    return conn.execute("SELECT COUNT(*) AS n FROM items").fetchone()["n"]
