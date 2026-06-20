"""
AI News Radar - Fetcher
Downloads every RSS feed, applies the filters, and saves new items
to the database. Also fetches Hugging Face trending papers (no RSS).
"""

import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import feedparser
import requests

import config
import database
import filters

# Some sites (especially Reddit) block requests without a real User-Agent.
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AINewsRadar/1.0"}

REQUEST_TIMEOUT = 15   # seconds per feed (parallel, so this caps total wall time)
MAX_WORKERS = 16       # feeds downloaded concurrently


def _entry_published(entry):
    """Get the publish time of a feed entry as UTC datetime, or None."""
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
    return None


def _too_old(published, max_days=None):
    if published is None:
        return False  # no date -> keep it, better safe than missing news
    days = max_days or config.MAX_ITEM_AGE_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return published < cutoff


def _hn_engagement(entry):
    """Hacker News RSS (hnrss.org) puts 'Points: N' and '# Comments: N' in the
    item description. Returns (upvotes, comments)."""
    text = entry.get("summary", "") or entry.get("description", "")
    up = re.search(r"Points:\s*(\d+)", text)
    com = re.search(r"Comments:\s*(\d+)", text)
    return (int(up.group(1)) if up else 0, int(com.group(1)) if com else 0)


def _reddit_id(url):
    m = re.search(r"/comments/([a-z0-9]+)", url or "")
    return m.group(1) if m else None


def _reddit_scores(feed_url):
    """One cheap call to the subreddit's public .json gives score + comments
    for each post (no API key). Returns {comment_id: (upvotes, comments)}.
    Any failure -> empty map (engagement just stays 0, never breaks fetch)."""
    out = {}
    try:
        jurl = feed_url.replace(".rss", ".json")
        r = requests.get(jurl, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        for ch in (r.json().get("data", {}).get("children", []) or []):
            d = ch.get("data", {})
            cid = _reddit_id(d.get("permalink", ""))
            if cid:
                out[cid] = (int(d.get("score", 0) or 0), int(d.get("num_comments", 0) or 0))
    except Exception:
        pass
    return out


def _download_feed(feed_cfg):
    """NETWORK ONLY (thread-safe, no DB): download + parse a feed, trying the
    main URL then the fallback (Bing News when Google News blocks cloud IPs),
    one retry each. Returns (feed_cfg, parsed_or_None, reddit_map)."""
    url = feed_cfg["url"]
    reddit_map = _reddit_scores(url) if "reddit.com" in url else {}
    urls = [url] + ([feed_cfg["fallback"]] if feed_cfg.get("fallback") else [])
    parsed = None
    for try_url in urls:
        for _ in (1, 2):
            try:
                resp = requests.get(try_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                parsed = feedparser.parse(resp.content)
                if parsed.entries:
                    break
            except Exception:
                parsed = None
                time.sleep(1)
        if parsed is not None and parsed.entries:
            break
    return feed_cfg, parsed, reddit_map


def _process_feed(conn, feed_cfg, parsed, reddit_map, existing, stats):
    """DB phase (main thread): filter, de-dupe and save a downloaded feed's items."""
    name = feed_cfg["name"]
    default_cat, trusted = feed_cfg["category"], feed_cfg["trusted"]
    lock = feed_cfg.get("lock", False)
    is_reddit = "reddit.com" in feed_cfg["url"]
    is_hn = "ycombinator" in feed_cfg["url"] or "hnrss" in feed_cfg["url"]

    new_count = 0
    for entry in parsed.entries[:30]:  # max 30 per feed per run
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue

        published = _entry_published(entry)
        if _too_old(published, feed_cfg.get("max_age_days")):
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

        # --- Engagement (for the weekly digest) ---
        upvotes, comments = 0, 0
        if is_reddit:
            upvotes, comments = reddit_map.get(_reddit_id(link), (0, 0))
        elif is_hn:
            upvotes, comments = _hn_engagement(entry)

        # --- New story ---
        category = default_cat if lock else filters.classify(title, default_cat)
        new_id = database.add_item(conn, title, link, name, category,
                                   published.isoformat() if published else None,
                                   upvotes, comments)
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


def _newsdata_key():
    """API key from the NEWSDATA_KEY env var (cloud) or a gitignored
    newsdata_key.txt (local). Empty string if not configured."""
    import os
    k = os.environ.get("NEWSDATA_KEY", "").strip()
    if not k:
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "newsdata_key.txt")) as f:
                k = f.read().strip()
        except FileNotFoundError:
            pass
    return k


def fetch_newsdata(conn, existing, stats):
    """Pull the latest AI news from NewsData.io (free API). Adds a broad
    breaking-news stream on top of the RSS feeds. Skips silently if no key."""
    key = _newsdata_key()
    if not key:
        return
    try:
        resp = requests.get("https://newsdata.io/api/1/latest", params={
            "apikey": key,
            "q": "artificial intelligence OR generative AI OR LLM",
            "language": "en",
            "category": "technology",
        }, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [!] NewsData.io: failed ({type(e).__name__})")
        stats["failed_feeds"].append("NewsData.io")
        return

    if data.get("status") != "success":
        print(f"  [!] NewsData.io: {data.get('message') or 'no results'}")
        return

    new_count = 0
    for art in (data.get("results") or [])[:30]:
        title = (art.get("title") or "").strip()
        link = (art.get("link") or "").strip()
        if not title or not link:
            continue

        published = None
        pd = art.get("pubDate")
        if pd:
            try:
                published = datetime.strptime(pd, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except ValueError:
                published = None
        if _too_old(published):
            continue

        if filters.is_junk(title):
            stats["junk"] += 1
            continue
        if not filters.is_ai_related(title):
            stats["not_ai"] += 1
            continue
        if database.url_exists(conn, link):
            continue

        dup_id = filters.find_duplicate(title, existing)
        if dup_id is not None:
            database.add_link_to_item(conn, dup_id, link, art.get("source_id") or "NewsData")
            stats["grouped"] += 1
            continue

        category = filters.classify(title, 10)
        new_id = database.add_item(conn, title, link, art.get("source_id") or "NewsData",
                                   category, published.isoformat() if published else None)
        existing.append({"id": new_id, "title": title})
        new_count += 1
        stats["new"] += 1

    conn.commit()
    if new_count:
        print(f"  [+] NewsData.io: {new_count} new")


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
        new_id = database.add_item(conn, title, link, "HF Trending Papers", 9, None)
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

    print(f"Fetching {len(config.FEEDS)} feeds in parallel (x{MAX_WORKERS}) + HF papers + NewsData ...")
    t0 = time.time()
    # 1) download + parse every feed concurrently (network-bound, no DB here)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        downloaded = list(ex.map(_download_feed, config.FEEDS))
    # 2) save serially on the main thread (SQLite + de-dup ordering)
    for feed_cfg, parsed, reddit_map in downloaded:
        if parsed is None or not parsed.entries:
            stats["failed_feeds"].append(feed_cfg["name"])
            continue
        _process_feed(conn, feed_cfg, parsed, reddit_map, existing, stats)
    print(f"  Feeds fetched in {time.time() - t0:.0f}s")
    fetch_hf_papers(conn, existing, stats)
    fetch_newsdata(conn, existing, stats)

    # --- Summary ---
    print()
    print("=" * 52)
    print(f"  New stories saved : {stats['new']}")
    print(f"  Grouped as dupes  : {stats['grouped']} (extra links attached)")
    print(f"  Filtered out      : {stats['not_ai']} not-AI, {stats['junk']} junk")
    if stats["failed_feeds"]:
        print(f"  Failed feeds      : {', '.join(stats['failed_feeds'])}")
    print("-" * 52)
    by_cat = database.count_by_pillar(conn, since_hours=24)
    for num, cname in config.CATEGORIES.items():
        print(f"  {cname}: {by_cat.get(num, 0)} in last 24h")
    # --- Auto-delete old news (retention) ---
    purged = database.purge_old(conn, getattr(config, "NEWS_RETENTION_DAYS", 7))
    if purged:
        print(f"  Purged {purged} story(ies) older than "
              f"{getattr(config, 'NEWS_RETENTION_DAYS', 7)} days")
    stats["purged"] = purged

    print(f"  Total stories in archive: {database.total_count(conn)}")
    print("=" * 52)

    conn.close()
    return stats
