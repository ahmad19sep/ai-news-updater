"""
AI News Radar - YouTube channel analytics (Step C)

Uses the FREE official YouTube Data API v3 (10,000 units/day - we use ~10
per refresh). You need a one-time API key, see README "Analytics setup".

What it computes:
  - channel stats (subscribers, total views, video count) + daily snapshots
  - recent videos with views/likes, short vs long
  - consistency: uploads per week, gap since last upload, best weekday
  - simple insights in plain language
"""

import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import requests

API = "https://www.googleapis.com/youtube/v3"
TIMEOUT = 20


class YTError(Exception):
    pass


def _get(path, **params):
    try:
        resp = requests.get(f"{API}/{path}", params=params, timeout=TIMEOUT)
        data = resp.json()
    except Exception as e:
        raise YTError(f"Network problem: {type(e).__name__}")
    if "error" in data:
        msg = data["error"].get("message", "unknown error")
        raise YTError(f"YouTube API said: {msg}")
    return data


def resolve_channel(key, handle):
    """Accepts @handle, channel URL, or channel ID -> (channel_id, title)."""
    handle = handle.strip()
    m = re.search(r"(UC[\w-]{22})", handle)
    if m:
        cid = m.group(1)
        data = _get("channels", part="snippet", id=cid, key=key)
        items = data.get("items", [])
        if items:
            return cid, items[0]["snippet"]["title"]
        raise YTError("Channel ID not found.")
    m = re.search(r"@([\w.-]+)", handle)
    name = m.group(1) if m else handle
    data = _get("channels", part="snippet", forHandle="@" + name, key=key)
    items = data.get("items", [])
    if not items:
        raise YTError(f'Channel "@{name}" not found. Check the handle.')
    return items[0]["id"], items[0]["snippet"]["title"]


def channel_stats(key, channel_id):
    data = _get("channels", part="statistics,contentDetails,snippet",
                id=channel_id, key=key)
    items = data.get("items", [])
    if not items:
        raise YTError("Channel not found.")
    it = items[0]
    st = it["statistics"]
    return {
        "title": it["snippet"]["title"],
        "subs": int(st.get("subscriberCount", 0)),
        "views": int(st.get("viewCount", 0)),
        "videos": int(st.get("videoCount", 0)),
        "uploads_playlist": it["contentDetails"]["relatedPlaylists"]["uploads"],
    }


def _parse_duration(iso):
    """PT1M30S -> seconds."""
    h = re.search(r"(\d+)H", iso)
    m = re.search(r"(\d+)M", iso)
    s = re.search(r"(\d+)S", iso)
    return (int(h.group(1)) * 3600 if h else 0) + \
           (int(m.group(1)) * 60 if m else 0) + (int(s.group(1)) if s else 0)


def recent_videos(key, uploads_playlist, n=15):
    data = _get("playlistItems", part="contentDetails", playlistId=uploads_playlist,
                maxResults=min(n, 50), key=key)
    ids = [it["contentDetails"]["videoId"] for it in data.get("items", [])]
    if not ids:
        return []
    data = _get("videos", part="snippet,statistics,contentDetails",
                id=",".join(ids), key=key)
    videos = []
    for it in data.get("items", []):
        secs = _parse_duration(it["contentDetails"]["duration"])
        st = it["statistics"]
        videos.append({
            "title": it["snippet"]["title"],
            "published": it["snippet"]["publishedAt"],
            "views": int(st.get("viewCount", 0)),
            "likes": int(st.get("likeCount", 0)),
            "comments": int(st.get("commentCount", 0)),
            "secs": secs,
            "is_short": secs <= 65,
            "url": "https://youtu.be/" + it["id"],
        })
    videos.sort(key=lambda v: v["published"], reverse=True)
    return videos


def consistency(videos, weeks=8):
    """Uploads per week (latest first), days since last upload, best weekday."""
    now = datetime.now(timezone.utc)
    per_week = [0] * weeks
    weekday_views = defaultdict(list)
    for v in videos:
        dt = datetime.fromisoformat(v["published"].replace("Z", "+00:00"))
        age_days = (now - dt).days
        wk = age_days // 7
        if wk < weeks:
            per_week[wk] += 1
        weekday_views[dt.strftime("%A")].append(v["views"])
    days_since = None
    if videos:
        last = datetime.fromisoformat(videos[0]["published"].replace("Z", "+00:00"))
        days_since = (now - last).days
    best_day = ""
    if weekday_views:
        best_day = max(weekday_views, key=lambda d: sum(weekday_views[d]) / len(weekday_views[d]))
    return {"per_week": per_week, "days_since": days_since, "best_day": best_day}


def insights(videos, cons):
    """Plain-language observations."""
    out = []
    if not videos:
        return ["No videos yet - upload your first one and stats will appear here!"]
    shorts = [v for v in videos if v["is_short"]]
    longs = [v for v in videos if not v["is_short"]]
    if shorts and longs:
        avg_s = sum(v["views"] for v in shorts) / len(shorts)
        avg_l = sum(v["views"] for v in longs) / len(longs)
        if avg_s > avg_l * 1.5:
            out.append(f"Shorts get {avg_s / max(avg_l, 1):.1f}x more views than long videos - keep making both, Shorts pull new people in.")
        elif avg_l > avg_s * 1.5:
            out.append(f"Long videos get {avg_l / max(avg_s, 1):.1f}x more views than Shorts - your audience likes depth.")
    best = max(videos, key=lambda v: v["views"])
    out.append(f'Best recent video: "{best["title"][:60]}" ({best["views"]:,} views) - make more on this topic.')
    if cons["days_since"] is not None and cons["days_since"] >= 7:
        out.append(f"⚠ {cons['days_since']} days since your last upload - consistency is the #1 growth factor.")
    elif cons["days_since"] is not None and cons["days_since"] <= 2:
        out.append("Good consistency - last upload was very recent. Keep the rhythm!")
    recent4 = sum(cons["per_week"][:4])
    if recent4 and recent4 < 4:
        out.append(f"Only {recent4} uploads in the last 4 weeks - aim for at least 2 per week (1 long + 1 short).")
    if cons["best_day"]:
        out.append(f"Your {cons['best_day']} videos get the most views on average - schedule big stories for that day.")
    likes_rate = [v["likes"] / v["views"] for v in videos if v["views"] > 100]
    if likes_rate and sum(likes_rate) / len(likes_rate) > 0.04:
        out.append("Your like-rate is above 4% - viewers really enjoy your style.")
    return out
