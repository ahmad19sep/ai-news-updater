"""Reddit collector — the PRIMARY source for 'problems people face'. No API key.

Reddit's public JSON endpoints now 403 from most IPs, but the RSS feeds still
work (that's what the news fetcher uses). So we use RSS by default and fall
back-UP to JSON when it happens to be reachable (JSON adds real score/comment
counts). RSS has no scores, so we use the feed's own ordering as a strength
proxy (top/hot feeds are already ranked). Fails gracefully.
"""

import time
from datetime import datetime, timezone

import feedparser
import requests

import config

UA = "ai-x-ahmad-pulse/1.0 (AI news content tool; contact @aixahmad)"


def _from_json(sub, sort):
    url = f"https://www.reddit.com/r/{sub}/{sort}.json?t=day&limit=25"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
        if r.status_code != 200:
            return None  # signal "JSON unavailable" -> caller uses RSS
        children = r.json().get("data", {}).get("children", [])
    except Exception:
        return None
    out = []
    for c in children:
        d = c.get("data", {})
        title = (d.get("title") or "").strip()
        if not title or d.get("stickied"):
            continue
        out.append(_sig(sub, title, "https://www.reddit.com" + (d.get("permalink") or ""),
                        (d.get("score", 0) or 0) + (d.get("num_comments", 0) or 0)))
    return out


def _from_rss(sub, sort):
    url = f"https://www.reddit.com/r/{sub}/{sort}/.rss?t=day"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
        if r.status_code != 200:
            return []
        entries = feedparser.parse(r.text).entries
    except Exception:
        return []
    out = []
    for i, e in enumerate(entries[:25]):
        title = (getattr(e, "title", "") or "").strip()
        if not title:
            continue
        # no score in RSS -> use feed position as a strength proxy (top is ranked)
        out.append(_sig(sub, title, getattr(e, "link", ""), max(0, 40 - i)))
    return out


def _sig(sub, title, url, metric):
    return {"platform": "reddit", "type": "post", "text": title, "url": url,
            "metric": metric, "subreddit": sub,
            "captured_at": datetime.now(timezone.utc).isoformat()}


def collect():
    signals = []
    for sub in config.PULSE_SUBREDDITS:
        for sort in ("hot", "top"):
            got = _from_json(sub, sort)
            if got is None:        # JSON blocked -> reliable RSS fallback
                got = _from_rss(sub, sort)
            signals.extend(got)
            time.sleep(0.4)
    # dedupe by url
    seen, out = set(), []
    for s in signals:
        if not s["url"] or s["url"] in seen:
            continue
        seen.add(s["url"])
        out.append(s)
    return out


if __name__ == "__main__":
    got = collect()
    print(f"reddit_pulse: {len(got)} signals")
    for s in got[:10]:
        print(f"  [{s['subreddit']}] ({s['metric']}) {s['text'][:70]}")
