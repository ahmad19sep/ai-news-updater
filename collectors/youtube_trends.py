"""YouTube collector via the Data API v3 (plain REST + requests, no SDK).

Needs a free YOUTUBE_API_KEY (GitHub Secret, or youtube_key.txt locally).
Returns [] if the key is missing or quota is exhausted — fully optional.

Two signals: (1) recent high-view AI uploads per seed term (interest proxy),
(2) the unofficial autocomplete/suggest endpoint (what people are searching).
"""

import json
import os
import re
from datetime import datetime, timezone, timedelta

import requests

import config

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _key():
    k = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if k:
        return k
    try:
        with open(os.path.join(_ROOT, "youtube_key.txt")) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def collect():
    key = _key()
    signals = []
    now = datetime.now(timezone.utc).isoformat()

    if key:
        after = (datetime.now(timezone.utc)
                 - timedelta(days=config.PULSE_YT_LOOKBACK_DAYS)
                 ).strftime("%Y-%m-%dT%H:%M:%SZ")
        for term in config.PULSE_SEED_TERMS:
            try:
                r = requests.get("https://www.googleapis.com/youtube/v3/search",
                                 params={"part": "snippet", "q": term, "type": "video",
                                         "order": "viewCount", "publishedAfter": after,
                                         "maxResults": config.PULSE_YT_MAX_RESULTS,
                                         "relevanceLanguage": "en", "key": key},
                                 timeout=15)
                if r.status_code != 200:
                    continue
                for it in r.json().get("items", []):
                    sn = it.get("snippet", {})
                    vid = (it.get("id", {}) or {}).get("videoId")
                    title = (sn.get("title") or "").strip()
                    if not title or not vid:
                        continue
                    signals.append({
                        "platform": "youtube", "type": "video", "text": title,
                        "url": "https://www.youtube.com/watch?v=" + vid,
                        "metric": 0, "channel": sn.get("channelTitle", ""),
                        "seed": term, "captured_at": now,
                    })
            except Exception:
                continue

    # Autocomplete = "what people search" (works without a key; best-effort).
    for prefix in ("ai ", "chatgpt ", "how to use ai "):
        try:
            r = requests.get("https://suggestqueries.google.com/complete/search",
                             params={"client": "youtube", "ds": "yt", "q": prefix},
                             timeout=10)
            m = re.search(r"\[.*\]", r.text)
            if not m:
                continue
            arr = json.loads(m.group(0))
            for s in (arr[1] if len(arr) > 1 else []):
                term = s[0] if isinstance(s, list) else s
                if isinstance(term, str) and term.strip():
                    signals.append({
                        "platform": "youtube", "type": "search_suggest",
                        "text": term.strip(),
                        "url": "https://www.youtube.com/results?search_query="
                               + requests.utils.quote(term),
                        "metric": 0, "captured_at": now,
                    })
        except Exception:
            continue
    return signals


if __name__ == "__main__":
    got = collect()
    print(f"youtube_trends: {len(got)} signals (key {'set' if _key() else 'MISSING'})")
    for s in got[:10]:
        print(f"  [{s['type']}] {s['text'][:70]}")
