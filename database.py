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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    return conn


# Your personal studio data (video plans, done marks) lives in a SEPARATE
# file. news.db is written by the cloud server every hour - keeping your
# edits out of it means "Get latest" can always pull without conflicts.
PLANS_DB = "plans.db"


def connect_plans():
    conn = sqlite3.connect(PLANS_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT NOT NULL,
            url          TEXT DEFAULT '',
            notes        TEXT DEFAULT '',
            platform     TEXT DEFAULT 'both',      -- long / short / both
            stage        TEXT DEFAULT 'idea',      -- idea/script/record/edit/uploaded/published
            planned_date TEXT DEFAULT '',
            created      TEXT NOT NULL,
            updated      TEXT NOT NULL
        )
    """)
    conn.execute("CREATE TABLE IF NOT EXISTS done_urls (url TEXT PRIMARY KEY)")
    conn.commit()
    return conn


def get_meta(conn, key, default=None):
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_meta(conn, key, value):
    conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value))
    conn.commit()


def mark_notified(conn, item_id):
    conn.execute("UPDATE items SET notified = 1 WHERE id = ?", (item_id,))
    conn.commit()


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
