"""Momentum from real history. Persists each run's trend signal strengths to
pulse_history/YYYY-MM-DD.json and labels a trend rising / hot / cooling by
comparing today's strength to the trailing few days. Used by BOTH synthesizers.
"""

import json
import os
from datetime import datetime, timezone, timedelta

import config

HIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "pulse_history")


def _key(name):
    return (name or "").strip().lower()


def record(strengths):
    """strengths: {trend_name: numeric}. Merge into today's snapshot (max wins)."""
    os.makedirs(HIST_DIR, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(HIST_DIR, day + ".json")
    snap = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                snap = json.load(f)
        except Exception:
            snap = {}
    for name, val in strengths.items():
        k = _key(name)
        snap[k] = max(snap.get(k, 0), round(float(val), 2))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False)


def _trailing(days=4):
    """Average strength per trend over the previous `days` days (excludes today)."""
    total, counts = {}, {}
    today = datetime.now(timezone.utc).date()
    for i in range(1, days + 1):
        path = os.path.join(HIST_DIR, (today - timedelta(days=i)).strftime("%Y-%m-%d") + ".json")
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                snap = json.load(f)
        except Exception:
            continue
        for k, v in snap.items():
            total[k] = total.get(k, 0) + v
            counts[k] = counts.get(k, 0) + 1
    return {k: total[k] / counts[k] for k in total if counts.get(k)}


def label(name, today_strength):
    """'rising' | 'hot' | 'cooling' for a trend given today's strength."""
    prev = _trailing().get(_key(name))
    if not prev:
        return "rising"  # brand-new signal with no history -> treat as rising
    ratio = today_strength / prev if prev else 1.0
    if ratio >= config.PULSE_MOMENTUM["rising"]:
        return "rising"
    if ratio <= config.PULSE_MOMENTUM["cooling"]:
        return "cooling"
    return "hot"
