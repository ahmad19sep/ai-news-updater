"""Hacker News collector via the free Algolia API (no key). Recent AI stories
with their points + comment counts as an interest signal. Fails gracefully."""

from datetime import datetime, timezone, timedelta

import requests


def collect():
    since = int((datetime.now(timezone.utc) - timedelta(days=2)).timestamp())
    url = ("https://hn.algolia.com/api/v1/search_by_date"
           "?tags=story&query=AI"
           f"&numericFilters=points%3E20,created_at_i%3E{since}&hitsPerPage=50")
    try:
        r = requests.get(url, timeout=15)
        hits = r.json().get("hits", []) if r.status_code == 200 else []
    except Exception:
        hits = []

    signals = []
    for h in hits:
        title = (h.get("title") or "").strip()
        if not title:
            continue
        oid = h.get("objectID")
        signals.append({
            "platform": "hackernews",
            "type": "story",
            "text": title,
            "url": h.get("url") or f"https://news.ycombinator.com/item?id={oid}",
            "metric": (h.get("points", 0) or 0) + (h.get("num_comments", 0) or 0),
            "captured_at": datetime.now(timezone.utc).isoformat(),
        })
    return signals


if __name__ == "__main__":
    got = collect()
    print(f"hackernews: {len(got)} signals")
    for s in got[:10]:
        print(f"  ({s['metric']}) {s['text'][:70]}")
