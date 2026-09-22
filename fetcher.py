"""
AI News Radar - Fetcher
Downloads every RSS feed, applies the filters, and saves new items
to the database. Also fetches Hugging Face papers and public agent projects.
"""

import html
import json
import os
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


def _health_update(health, source, ok, detail=""):
    """Record collection health without turning one adapter failure into a run failure."""
    now = datetime.now(timezone.utc).isoformat()
    previous = health.get(source) if isinstance(health.get(source), dict) else {}
    health[source] = {
        "last_attempt": now,
        "last_success": now if ok else previous.get("last_success"),
        "state": "healthy" if ok else "failed",
        "detail": str(detail or "")[:160],
    }


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


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _entry_summary(entry, max_chars=700):
    """The 1-3 sentences a feed ships with its item. This is what the LinkedIn
    writer uses as source facts when the AI cannot open the link itself, so it
    matters that it is real text: tags stripped, entities decoded, no truncation
    mid-word. Google News summaries are mostly link markup, so those come back
    short or empty - that is honest, and better than a fabricated summary."""
    raw = entry.get("summary") or entry.get("description") or ""
    if not raw and entry.get("content"):
        try:
            raw = entry["content"][0].get("value", "")
        except Exception:
            raw = ""
    text = html.unescape(_TAG_RE.sub(" ", raw))
    text = _WS_RE.sub(" ", text).strip()
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    return cut[:cut.rfind(" ")] + "…" if " " in cut else cut


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

        title_lower = title.lower()
        required = feed_cfg.get("require_any") or []
        excluded = feed_cfg.get("exclude_any") or []
        if required and not any(term.lower() in title_lower for term in required):
            stats["not_ai"] += 1
            continue
        if excluded and any(term.lower() in title_lower for term in excluded):
            stats["junk"] += 1
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

        if feed_cfg.get("agent_only"):
            if database.url_exists(conn, link) or database.agent_discovery_exists(conn, link):
                continue
            upvotes, comments = _hn_engagement(entry) if is_hn else (0, 0)
            database.add_agent_discovery(
                conn, title, link, name,
                published.isoformat() if published else None,
                _entry_summary(entry), upvotes,
            )
            new_count += 1
            stats["new"] += 1
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
                                   upvotes, comments, _entry_summary(entry))
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
                                   category, published.isoformat() if published else None,
                                   summary=(art.get("description") or "")[:700])
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


def _api_datetime(value):
    """Parse the ISO timestamps used by GitHub and Hugging Face APIs."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _hf_space_story(space):
    """Normalize one public Hugging Face Space into an item-shaped dict."""
    if not isinstance(space, dict) or space.get("private"):
        return None
    repo_id = str(space.get("id") or "").strip()
    card = space.get("cardData") if isinstance(space.get("cardData"), dict) else {}
    display = str(card.get("title") or (repo_id.split("/", 1)[-1] if repo_id else "")).strip()
    description = str(card.get("short_description") or "").strip()
    tags = [str(x) for x in (space.get("tags") or []) if x]
    blob = " ".join([repo_id, display, description] + tags).lower()
    if not repo_id or not any(term in blob for term in (
            "agent", "assistant", "automation", "workflow", "rag", "mcp")):
        return None
    author = str(space.get("author") or repo_id.split("/", 1)[0]).strip()
    likes = int(space.get("likes") or 0)
    sdk = str(space.get("sdk") or card.get("sdk") or "unknown")
    facts = [f"Public Hugging Face Space by {author}."]
    if description:
        facts.append(f"Description: {description}.")
    facts.append(f"SDK: {sdk}. Likes: {likes}.")
    if tags:
        facts.append("Tags: " + ", ".join(tags[:10]) + ".")
    return {
        "title": f"{display} - agent demo by {author}",
        "url": "https://huggingface.co/spaces/" + repo_id,
        "published": _api_datetime(space.get("createdAt")),
        "summary": " ".join(facts)[:700],
        "upvotes": likes,
    }


def _github_repo_story(repo):
    """Normalize one public GitHub agent repository into an item-shaped dict."""
    if not isinstance(repo, dict) or repo.get("private") or repo.get("fork") or repo.get("archived"):
        return None
    full_name = str(repo.get("full_name") or "").strip()
    url = str(repo.get("html_url") or "").strip()
    if not full_name or not url:
        return None
    description = str(repo.get("description") or "Open-source AI agent project").strip()
    stars = int(repo.get("stargazers_count") or 0)
    language = str(repo.get("language") or "unknown")
    topics = [str(x) for x in (repo.get("topics") or []) if x]
    summary = (
        f"Open-source repository. Description: {description}. "
        f"Language: {language}. Stars: {stars}."
    )
    if topics:
        summary += " Topics: " + ", ".join(topics[:10]) + "."
    return {
        "title": f"{full_name}: {description}",
        "url": url,
        "published": _api_datetime(repo.get("created_at")),
        "summary": summary[:700],
        "upvotes": stars,
    }


def _save_discovery_stories(conn, existing, stats, source, stories, max_age_days=30):
    """Save normalized public-project discoveries using the normal de-dupe rules."""
    new_count = 0
    for story in stories:
        if not story or _too_old(story.get("published"), max_age_days):
            continue
        title, link = story["title"], story["url"]
        if database.url_exists(conn, link) or database.agent_discovery_exists(conn, link):
            continue
        dup_id = filters.find_duplicate(title, existing)
        if dup_id is not None:
            stats["grouped"] += 1
            continue
        database.add_agent_discovery(
            conn, title, link, source,
            story["published"].isoformat() if story.get("published") else None,
            story.get("summary", ""), story.get("upvotes", 0),
        )
        stats["new"] += 1
        new_count += 1
    conn.commit()
    if new_count:
        print(f"  [+] {source}: {new_count} new")
    return new_count


def fetch_hf_agent_spaces(conn, existing, stats):
    """Discover fresh, runnable agent demos from the public HF Spaces API."""
    source = "Hugging Face Agent Spaces"
    try:
        resp = requests.get("https://huggingface.co/api/spaces", params={
            "search": "agent", "sort": "trendingScore", "direction": "-1",
            "limit": 30, "full": "true",
        }, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            raise ValueError("unexpected response")
    except Exception as e:
        print(f"  [!] {source}: failed ({type(e).__name__})")
        stats["failed_feeds"].append(source)
        return False, type(e).__name__
    _save_discovery_stories(
        conn, existing, stats, source,
        [_hf_space_story(space) for space in data],
    )
    return True, ""


def fetch_github_agent_repos(conn, existing, stats):
    """Run a bounded family of public repository searches independently."""
    since = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
    headers = dict(HEADERS)
    headers.update({
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    })
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = "Bearer " + token
    results = {}
    for query in getattr(config, "AGENT_GITHUB_QUERIES", []):
        source = query["name"]
        try:
            resp = requests.get("https://api.github.com/search/repositories", params={
                "q": query["query"].format(since=since),
                "sort": "stars", "order": "desc", "per_page": int(query.get("limit", 10)),
            }, headers=headers, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            payload = resp.json()
            data = payload.get("items") or []
            if not isinstance(data, list):
                raise ValueError("unexpected response")
            _save_discovery_stories(
                conn, existing, stats, source,
                [_github_repo_story(repo) for repo in data],
            )
            results[source] = (True, "partial search results" if payload.get("incomplete_results") else "")
        except Exception as e:
            print(f"  [!] {source}: failed ({type(e).__name__})")
            stats["failed_feeds"].append(source)
            results[source] = (False, type(e).__name__)
    return results


def seed_curated_agent_use_cases(conn, stats):
    """Add a tiny, attributed first-party use-case pack idempotently."""
    added = 0
    for story in getattr(config, "AGENT_CURATED_USE_CASES", []):
        if database.agent_discovery_exists(conn, story["url"]):
            conn.execute(
                "UPDATE agent_discoveries SET title=?, source=?, published=?, summary=? WHERE url=?",
                (story["title"], story["source"], story.get("published"),
                 story.get("summary", ""), story["url"]),
            )
            continue
        database.add_agent_discovery(
            conn,
            story["title"],
            story["url"],
            story["source"],
            story.get("published"),
            story.get("summary", ""),
            0,
        )
        stats["new"] = stats.get("new", 0) + 1
        added += 1
    if added:
        print(f"  [+] Curated official AI uses: {added} new")
    return added


def run_fetch():
    """One full fetch cycle over all sources. Returns the stats dict."""
    conn = database.connect()
    existing = [dict(r) for r in
                database.recent_items(conn, config.DUPLICATE_WINDOW_HOURS)]
    stats = {"new": 0, "grouped": 0, "junk": 0, "not_ai": 0,
             "failed_feeds": [], "alerts": []}
    try:
        source_health = json.loads(database.get_meta(conn, "agent_source_health", "{}") or "{}")
    except (TypeError, ValueError):
        source_health = {}

    seed_curated_agent_use_cases(conn, stats)

    print(f"Fetching {len(config.FEEDS)} feeds in parallel (x{MAX_WORKERS}) + project discovery + NewsData ...")
    t0 = time.time()
    # 1) download + parse every feed concurrently (network-bound, no DB here)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        downloaded = list(ex.map(_download_feed, config.FEEDS))
    # 2) save serially on the main thread (SQLite + de-dup ordering)
    for feed_cfg, parsed, reddit_map in downloaded:
        if feed_cfg.get("agent_only"):
            ok = parsed is not None and bool(parsed.entries)
            _health_update(source_health, feed_cfg["name"], ok, "" if ok else "feed unavailable or empty")
        if parsed is None or not parsed.entries:
            stats["failed_feeds"].append(feed_cfg["name"])
            continue
        _process_feed(conn, feed_cfg, parsed, reddit_map, existing, stats)
    print(f"  Feeds fetched in {time.time() - t0:.0f}s")
    fetch_hf_papers(conn, existing, stats)
    hf_ok, hf_detail = fetch_hf_agent_spaces(conn, existing, stats)
    _health_update(source_health, "Hugging Face Agent Spaces", hf_ok, hf_detail)
    for source, (ok, detail) in fetch_github_agent_repos(conn, existing, stats).items():
        _health_update(source_health, source, ok, detail)
    database.set_meta(conn, "agent_source_health", json.dumps(source_health, sort_keys=True))
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
    purged_agents = database.purge_agent_discoveries(
        conn, getattr(config, "NEWS_RETENTION_DAYS", 7)
    )
    if purged:
        print(f"  Purged {purged} story(ies) older than "
              f"{getattr(config, 'NEWS_RETENTION_DAYS', 7)} days")
    if purged_agents:
        print(f"  Purged {purged_agents} Agent discovery item(s) older than "
              f"{getattr(config, 'NEWS_RETENTION_DAYS', 7)} days")
    stats["purged"] = purged
    stats["purged_agents"] = purged_agents

    print(f"  Total stories in archive: {database.total_count(conn)}")
    print("=" * 52)

    conn.close()
    return stats
