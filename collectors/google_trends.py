"""Google Trends collector via pytrends (UNOFFICIAL).

IMPORTANT: pytrends is unofficial and frequently rate-limits or breaks —
especially from datacenter IPs like GitHub Actions (Google blocks those; it's
the same reason the news pipeline falls back from Google News to Bing). Treat
this as BEST-EFFORT only.

Optional dependency: if pytrends isn't installed, this collector is skipped
silently (returns []). To enable: pip install -r requirements-pulse.txt.
A paid/official Google Trends source can be swapped in here later.
"""

from datetime import datetime, timezone

import config


def collect():
    try:
        from pytrends.request import TrendReq
    except Exception:
        return []  # pytrends not installed -> skip

    try:
        py = TrendReq(hl="en-US", tz=0, timeout=(10, 25))
    except Exception:
        return []

    now = datetime.now(timezone.utc).isoformat()
    signals = []
    for geo in config.PULSE_GEOS:
        for term in config.PULSE_SEED_TERMS[:5]:  # cap to reduce rate-limiting
            try:
                py.build_payload([term], timeframe="now 7-d", geo=geo)
                rq = py.related_queries()
                rising = (rq.get(term, {}) or {}).get("rising")
                if rising is None:
                    continue
                for _, row in rising.iterrows():
                    q = str(row.get("query", "")).strip()
                    if not q:
                        continue
                    signals.append({
                        "platform": "google", "type": "rising_query", "text": q,
                        "url": "https://www.google.com/search?q=" + q.replace(" ", "+"),
                        "metric": int(row.get("value", 0) or 0),
                        "geo": geo, "seed": term, "captured_at": now,
                    })
            except Exception:
                continue
    return signals


if __name__ == "__main__":
    got = collect()
    print(f"google_trends: {len(got)} signals")
    for s in got[:10]:
        print(f"  [{s['geo']}] ({s['metric']}) {s['text'][:60]}")
