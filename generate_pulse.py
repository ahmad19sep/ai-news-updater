"""AI Pulse generator.

Collectors -> dedupe -> synthesizer (LLM or raw, per config.PULSE_USE_LLM) ->
writes docs/pulse.json (read live by the Pulse tab) + a daily momentum snapshot
in pulse_history/. Standalone:  python generate_pulse.py

Fail-soft: if PULSE_USE_LLM is True but no key/LLM works, it falls back to raw
mode and records meta.mode = "raw" so the UI degrades gracefully.
"""

import json
import os
import sys
from datetime import datetime, timezone

import config
from collectors import (google_trends, hackernews, reddit_pulse, social_trends,
                        youtube_trends)
from analyzer import momentum, raw_synthesizer, trend_synthesizer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

COLLECTORS = [
    ("reddit", reddit_pulse),
    ("hackernews", hackernews),
    ("youtube", youtube_trends),
    ("google", google_trends),
    ("social", social_trends),
]


def collect_all():
    signals, used, counts = [], [], {}
    for name, mod in COLLECTORS:
        try:
            got = mod.collect() or []
        except Exception as e:
            print(f"  [{name}] failed: {e}")
            got = []
        if got:
            used.append(name)
            counts[name] = len(got)
            signals.extend(got)
        print(f"  [{name}] {len(got)} signals")
    # dedupe by (platform, normalized text)
    seen, dedup = set(), []
    for s in signals:
        k = (s.get("platform"), (s.get("text") or "").strip().lower())
        if k in seen:
            continue
        seen.add(k)
        dedup.append(s)
    return dedup, used, counts


def generate():
    print("AI Pulse: collecting free signals...")
    signals, used, counts = collect_all()
    print(f"  -> {len(signals)} unique signals from {used}")

    mode, provider, result = "raw", None, {}
    if config.PULSE_USE_LLM:
        print("  PULSE_USE_LLM=True -> trying LLM synthesizer...")
        result = trend_synthesizer.synthesize(signals)
        if result and result.get("trends"):
            mode, provider = "llm", config.PULSE_LLM_PROVIDER
        else:
            print("  LLM unavailable/failed -> falling back to raw mode")
    if mode == "raw":
        result = raw_synthesizer.synthesize(signals)

    # record momentum history, then strip the private strength field
    try:
        momentum.record({t["name"]: t.get("_strength", t.get("video_worthy", 1))
                         for t in result.get("trends", [])})
    except Exception as e:
        print(f"  history save failed: {e}")
    for t in result.get("trends", []):
        t.pop("_strength", None)

    rising_tools = sorted(
        [t for t in result.get("trends", []) if t.get("category") == "tool_launch"],
        key=lambda t: (t.get("momentum") == "rising", t.get("video_worthy", 0)),
        reverse=True)

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "meta": {"mode": mode, "sources_used": used, "signal_counts": counts,
                 "llm_provider": provider},
        "trends": result.get("trends", []),
        "rising_tools": rising_tools,
        "pain_points": result.get("pain_points", []),
        "tool_of_week_candidate": result.get("tool_of_week_candidate", ""),
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "pulse.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"docs/pulse.json written: mode={mode}, {len(out['trends'])} trends, "
          f"{len(out['rising_tools'])} rising tools, {len(out['pain_points'])} pain points.")


if __name__ == "__main__":
    generate()
