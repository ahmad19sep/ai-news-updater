"""
AI News Radar - Fetcher
Downloads every RSS feed, applies the filters, and saves new items
to the database. Also fetches Hugging Face trending papers (no RSS).
"""

import re
import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests

import config
import database
import filters

# Some sites (especially Reddit) block requests without a real User-Agent.
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AINewsRadar/1.0"}

REQUEST_TIMEOUT = 20  # seconds per feed


def _entry_published(entry):
    """Get the publish time of a feed entry as UTC datetime, or None."""
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
    return None


def _too_old(published):
    if published is None:
        return False  # no date -> keep it, better safe than missing news
    cutoff = datetime.now(timezone.utc) - timedelta(days=config.MAX_ITEM_AGE_DAYS)
    return published < cutoff


def fetch_feed(conn, feed_cfg, existing, stats):
    """Download one RSS feed and save its new items."""
    name, url = feed_cfg["name"], feed_cfg["url"]
    pillar, trusted = feed_cfg["pillar"], feed_cfg["trusted"]

    parsed = None
    for attempt in (1, 2):  # one retry, some feeds time out occasionally
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
            break
        except Exception as e:
            if attempt == 2:
                print(f"  [!] {name}: failed ({type(e).__name__})")
                stats["failed_feeds"].append(name)
                return
            time.sleep(2)

    new_count = 0
    for entry in parsed.entries[:30]:  # max 30 per feed per run
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue

        published = _entry_published(entry)
        if _too_old(published):
            continue

        # --- Filters ---
        if filters.is_junk(title):
            stats["junk"] += 1
            continue
        if not trusted and not filters.is_ai_related(title):
            stats["not_ai"] += 1
            continue
        if database.url_exists(conn, link):
            continue

        # --- Duplicate story from another site? Attach link instead. ---
        dup_id = filters.find_duplicate(title, existing)
        if dup_id is not None:
            database.add_link_to_item(conn, dup_id, link, name)
            stats["grouped"] += 1
            continue

        # --- New story ---
        new_id = database.add_item(conn, title, link, name, pillar,
                                   published.isoformat() if published else None)
        existing.append({"id": new_id, "title": title})  # so later feeds can group with it
        new_count += 1
        stats["new"] += 1

        # Official lab announcement -> goes straight to the phone
        if name in config.INSTANT_SOURCES:
            stats["alerts"].append(
                {"id": new_id, "title": title, "url": link, "source": name})

    conn.commit()
    if new_count:
        print(f"  [+] {name}: {new_count} new")


def fetch_hf_papers(conn, existing, stats):
    """Hugging Face trending papers page has no RSS, so we read the HTML
    and pull out the paper links and titles with a simple pattern."""
    try:
        resp = requests.get("https://huggingface.co/papers",
                            headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [!] Hugging Face Papers: failed ({type(e).__name__})")
        stats["failed_feeds"].append("Hugging Face Papers")
        return

    # Links look like: <a ... href="/papers/2406.12345">Paper Title</a>
    found = re.findall(r'href="(/papers/\d{4}\.\d{4,5})"[^>]*>([^<]{15,})</a>',
                       resp.text)
    new_count = 0
    seen = set()
    for path, title in found[:20]:
        title = title.strip()
        link = "https://huggingface.co" + path
        if link in seen or not title:
            continue
        seen.add(link)
        if database.url_exists(conn, link):
            continue
        if filters.find_duplicate(title, existing) is not None:
            continue
        new_id = database.add_item(conn, title, link, "HF Trending Papers", 5, None)
        existing.append({"id": new_id, "title": title})
        new_count += 1
        stats["new"] += 1

    conn.commit()
    if new_count:
        print(f"  [+] HF Trending Papers: {new_count} new")


def run_fetch():
    """One full fetch cycle over all sources. Returns the stats dict."""
    conn = database.connect()
    existing = [dict(r) for r in
                database.recent_items(conn, config.DUPLICATE_WINDOW_HOURS)]
    stats = {"new": 0, "grouped": 0, "junk": 0, "not_ai": 0,
             "failed_feeds": [], "alerts": []}

    print(f"Fetching {len(config.FEEDS)} feeds + HF papers ...")
    for feed_cfg in config.FEEDS:
        fetch_feed(conn, feed_cfg, existing, stats)
    fetch_hf_papers(conn, existing, stats)

    # --- Summary ---
    print()
    print("=" * 52)
    print(f"  New stories saved : {stats['new']}")
    print(f"  Grouped as dupes  : {stats['grouped']} (extra links attached)")
    print(f"  Filtered out      : {stats['not_ai']} not-AI, {stats['junk']} junk")
    if stats["failed_feeds"]:
        print(f"  Failed feeds      : {', '.join(stats['failed_feeds'])}")
    print("-" * 52)
    by_pillar = database.count_by_pillar(conn, since_hours=24)
    for num, pname in config.PILLARS.items():
        print(f"  Pillar {num} ({pname}): {by_pillar.get(num, 0)} in last 24h")
    print(f"  Total stories in archive: {database.total_count(conn)}")
    print("=" * 52)

    conn.close()
    return stats
