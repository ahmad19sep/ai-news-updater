"""
AI News Radar - Main entry point

Usage:
  python main.py            -> fetch once and exit (good for testing)
  python main.py --loop     -> fetch every 60 minutes, forever
  python main.py --latest   -> show the 20 newest stories in the terminal
"""

import sys
import time
from datetime import datetime

import config
import database
import fetcher

FETCH_INTERVAL_MINUTES = 60


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
        pillar = config.PILLARS.get(r["pillar"], "?")
        print(f"[{pillar}] {r['title']}")
        print(f"    {r['source']}  |  {r['url']}\n")
    conn.close()


def loop_forever():
    print(f"AI News Radar running. Fetching every {FETCH_INTERVAL_MINUTES} minutes.")
    print("Press Ctrl+C to stop.\n")
    while True:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Starting fetch cycle...")
        try:
            fetcher.run_fetch()
        except Exception as e:
            print(f"Fetch cycle error: {e}")  # never let one bad cycle kill the loop
        time.sleep(FETCH_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    if "--loop" in sys.argv:
        loop_forever()
    elif "--latest" in sys.argv:
        show_latest()
    else:
        fetcher.run_fetch()
