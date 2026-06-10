"""
AI News Radar - Notifier (Phase 2)
Sends news to your phone through ntfy.sh (free, no account, works in Pakistan).

Two levels:
  1. Instant alert  -> official lab announcements, the moment they appear
  2. Digest         -> everything else, grouped by pillar, 3 times a day
"""

import requests

import config

SEND_TIMEOUT = 15


def send(title, message, priority="default", click=None, tags=None):
    """Push one notification to your phone. Returns True if delivered."""
    headers = {
        "Title": title.encode("ascii", "replace").decode(),  # headers must be ASCII
        "Priority": priority,
    }
    if click:
        headers["Click"] = click
    if tags:
        headers["Tags"] = tags
    try:
        resp = requests.post(
            f"{config.NTFY_SERVER}/{config.NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers=headers,
            timeout=SEND_TIMEOUT,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"  [!] notification failed: {type(e).__name__}")
        return False


def send_instant_alert(item):
    """item = {'title', 'url', 'source'} - high priority, opens the link on tap."""
    return send(
        title=f"{item['source']} - NEW",
        message=item["title"],
        priority="high",
        click=item["url"],
        tags="rotating_light",
    )


def send_top_picks(conn):
    """Morning message: the 5 most video-worthy stories with reasons."""
    import scoring
    picks = [p for p in scoring.score_items(conn) if p["score"] >= 5][:5]
    if not picks:
        return False
    lines = []
    for i, p in enumerate(picks, 1):
        why = ", ".join(p["reasons"]) or "solid story"
        lines.append(f"{i}. {p['title']}\n   ({why})\n   {p['url']}")
    return send(
        title="Top 5 video picks today",
        message="\n\n".join(lines),
        priority="high",
        tags="star",
        click=config.DASHBOARD_URL,
    )


def send_digest(conn):
    """Send all unsent items as one grouped digest (one message per pillar),
    then mark everything as notified so it is never sent twice."""
    rows = conn.execute(
        "SELECT id, title, url, source, pillar FROM items "
        "WHERE notified = 0 ORDER BY pillar, fetched DESC"
    ).fetchall()
    if not rows:
        print("Digest: nothing new to send.")
        return 0

    by_pillar = {}
    for r in rows:
        by_pillar.setdefault(r["pillar"], []).append(r)

    sent = 0
    for pillar_num in sorted(by_pillar):
        items = by_pillar[pillar_num][: config.DIGEST_MAX_PER_PILLAR]
        skipped = len(by_pillar[pillar_num]) - len(items)
        lines = []
        for it in items:
            lines.append(f"- {it['title']}  ({it['source']})\n  {it['url']}")
        if skipped > 0:
            lines.append(f"...and {skipped} more on the dashboard")
        ok = send(
            title=f"Digest - {config.CATEGORIES[pillar_num]} ({len(items)})",
            message="\n\n".join(lines),
            tags="newspaper",
            click=config.DASHBOARD_URL,  # tap the notification -> dashboard opens
        )
        if ok:
            sent += 1

    # Mark ALL as notified (even the skipped extras) so backlog never piles up.
    conn.execute("UPDATE items SET notified = 1 WHERE notified = 0")
    conn.commit()
    print(f"Digest: {sent} pillar message(s) sent, {len(rows)} stories marked as delivered.")
    return sent
