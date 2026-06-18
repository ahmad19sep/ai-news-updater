"""
AI News Radar - Main entry point

Usage:
  python main.py            -> fetch once, send instant alerts, exit
  python main.py --loop     -> run forever: fetch hourly + digests at 8:00, 14:00, 21:00
  python main.py --latest   -> show the 20 newest stories in the terminal
  python main.py --digest   -> send the digest to your phone right now
  python main.py --test     -> send a test notification to your phone
"""

import json
import sys
import time
from datetime import datetime

import config
import database
import fetcher
import notifier

FETCH_INTERVAL_MINUTES = 60

# Print emoji/special characters safely on the Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def fetch_and_alert():
    """One fetch cycle + instant phone alerts for official lab news."""
    stats = fetcher.run_fetch()
    if not stats["alerts"]:
        return
    conn = database.connect()
    for item in stats["alerts"][:5]:  # safety cap: max 5 instant alerts per cycle
        if notifier.send_instant_alert(item):
            database.mark_notified(conn, item["id"])
            print(f"  [>] Instant alert sent: {item['title'][:60]}")
    conn.close()


def maybe_send_digest():
    """Send the digest if we passed a digest hour and have not sent that
    slot today. Also catches up if the PC was off at the exact hour."""
    now = datetime.now()
    due_slots = [h for h in config.DIGEST_HOURS if now.hour >= h]
    if not due_slots:
        return
    slot_key = f"{now.date()}-{max(due_slots):02d}"
    conn = database.connect()
    # Once per day (first slot of the morning): Top 5 video picks
    if database.get_meta(conn, "last_picks") != str(now.date()):
        print("\nSending Top 5 video picks...")
        notifier.send_top_picks(conn)
        database.set_meta(conn, "last_picks", str(now.date()))
    if database.get_meta(conn, "last_digest") != slot_key:
        print(f"\nDigest time ({max(due_slots)}:00 slot)...")
        notifier.send_digest(conn)
        database.set_meta(conn, "last_digest", slot_key)
    conn.close()


def maybe_send_nudge():
    """'Post this' nudge: every NUDGE_EVERY_HOURS (instantly for a big story),
    push the top video-worthy story you haven't been nudged about. Tapping it
    opens the Studio. Never repeats a story; silent overnight (PK time)."""
    if not getattr(config, "NUDGE_ENABLED", False):
        return
    import scoring
    conn = database.connect()
    try:
        picks = scoring.score_items(conn)
        nudged = set(json.loads(database.get_meta(conn, "nudged_urls", "[]") or "[]"))
        cands = [p for p in picks
                 if p.get("pillar") != 9                       # never research papers
                 and p["score"] >= config.NUDGE_MIN_SCORE
                 and p["url"] not in nudged]
        if not cands:
            return
        top = cands[0]
        now = datetime.now()
        urgent = top["score"] >= config.NUDGE_URGENT_SCORE
        # quiet hours (your local time)
        local_hour = (now.hour + config.NUDGE_TZ_OFFSET) % 24
        if not urgent and config.NUDGE_QUIET_START <= local_hour < config.NUDGE_QUIET_END:
            return
        # routine gap throttle (urgent stories skip the wait)
        last = database.get_meta(conn, "last_nudge", "")
        if last and not urgent:
            try:
                if (now - datetime.fromisoformat(last)).total_seconds() / 3600 < config.NUDGE_EVERY_HOURS:
                    return
            except ValueError:
                pass
        if notifier.send_post_nudge(top):
            print(f"  [>] Post-this nudge sent ({top['score']}): {top['title'][:60]}")
            nudged.add(top["url"])
            database.set_meta(conn, "nudged_urls", json.dumps(list(nudged)[-80:]))
            database.set_meta(conn, "last_nudge", now.isoformat())
    finally:
        conn.close()


def show_latest(limit=20):
    conn = database.connect()
    rows = conn.execute(
        "SELECT title, source, pillar, url, fetched FROM items "
        "ORDER BY fetched DESC LIMIT ?", (limit,)
    ).fetchall()
    if not rows:
        print("No stories yet. Run:  python main.py")
        return
    print(f"\n--- {len(rows)} newest stories ---\n")
    for r in rows:
        cat = config.CATEGORIES.get(r["pillar"], "?")
        print(f"[{cat}] {r['title']}")
        print(f"    {r['source']}  |  {r['url']}\n")
    conn.close()


def loop_forever():
    print("AI News Radar running.")
    print(f"  Fetch every {FETCH_INTERVAL_MINUTES} min | Instant alerts: on | "
          f"Digests at {', '.join(f'{h}:00' for h in config.DIGEST_HOURS)}")
    print("  Press Ctrl+C to stop.\n")
    while True:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Starting fetch cycle...")
        try:
            fetch_and_alert()
            maybe_send_nudge()
            maybe_send_digest()
        except Exception as e:
            print(f"Cycle error: {e}")  # never let one bad cycle kill the loop
        time.sleep(FETCH_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    if "--loop" in sys.argv:
        loop_forever()
    elif "--latest" in sys.argv:
        show_latest()
    elif "--digest" in sys.argv:
        conn = database.connect()
        notifier.send_digest(conn)
        conn.close()
    elif "--test" in sys.argv:
        ok = notifier.send(
            "AI News Radar - Test",
            "Your phone is connected! Instant AI alerts will arrive here.",
            tags="white_check_mark",
        )
        print("Test notification sent." if ok else "Test FAILED - check internet.")
        print(f"Topic: {config.NTFY_TOPIC}")
    elif "--nudge" in sys.argv:
        maybe_send_nudge()
    else:
        fetch_and_alert()
        maybe_send_nudge()   # "post this" nudge (throttled to every NUDGE_EVERY_HOURS)
        maybe_send_digest()  # cloud server runs once per hour, so check here too
