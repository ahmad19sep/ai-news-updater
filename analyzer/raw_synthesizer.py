"""Deterministic, NO-LLM synthesizer (PULSE_USE_LLM = False).

Produces the SAME JSON shape as the LLM path, with AI-generated fields
(what_it_is, audience_angle, linkedin_angle, content_ideas, content_opportunity)
left empty — the frontend hides them in raw mode. Needs no API key.
"""

import re
from collections import defaultdict

import config
from analyzer import momentum

_STOP = set("the a an of to in on for and or with is are was how what why ai new "
            "your you my this that it its from at by as be can will just".split())


def _has(text, words):
    t = text.lower()
    return any(re.search(r"\b" + re.escape(w) + r"\b", t) for w in words)


def _fallback_key(text):
    words = [w for w in re.findall(r"[a-z0-9]+", text.lower())
             if w not in _STOP and len(w) > 2]
    return " ".join(words[:4]) or text.lower()[:40]


def _local_score(text):
    t = text.lower()
    return min(10, sum(1 for w in config.PULSE_LOCAL_KEYWORDS if w in t) * 4)


def _pillar_format(text):
    t = text.lower()
    if _has(t, ["money", "earn", "income", "freelance", "fiverr", "upwork",
                "job", "jobs", "business", "side hustle"]):
        return "practical_earning", "long_form"
    if any(w in t for w in ["image", "video", "art", "photo", "reel", "meme",
                            "avatar", "design", "animation"]):
        return "discovery", "reel"
    if any(w in t for w in ["how", "tutorial", "guide", "explain", "what is",
                            "beginner", "step by step"]):
        return "explainer", "short"
    return "discovery", "short"


def _platforms_for(text, base):
    plats = list(base)
    t = text.lower()
    if any(w in t for w in ["image", "video", "art", "photo", "reel", "design",
                            "avatar", "meme", "animation"]):
        plats += ["instagram_inferred", "facebook_inferred"]
    if any(w in t for w in ["job", "jobs", "career", "business", "productivity",
                            "work", "resume", "linkedin", "hiring"]):
        plats.append("linkedin_inferred")
    return sorted(set(plats))


def _pain_points(signals):
    cands = [s for s in signals
             if s["platform"] == "reddit" and _has(s["text"], config.PULSE_PROBLEM_KEYWORDS)]
    cands.sort(key=lambda g: g.get("metric") or 0, reverse=True)
    out, seen = [], set()
    for s in cands:
        k = _fallback_key(s["text"])
        if k in seen:
            continue
        seen.add(k)
        out.append({
            "problem": s["text"][:140],
            "who_affected": ("r/" + s["subreddit"]) if s.get("subreddit") else "Reddit users",
            "signal_strength": min(10, round((s.get("metric") or 0) / 60) + 3),
            "sources": [{"platform": "reddit", "url": s["url"]}],
            "content_opportunity": "",  # raw mode
        })
        if len(out) >= config.PULSE_MAX_PAIN_POINTS:
            break
    return out


def synthesize(signals):
    clusters = defaultdict(list)
    for s in signals:
        text = s["text"].lower()
        matched = next((tool for tool in config.PULSE_TOOL_DICT if tool in text), None)
        clusters[matched or _fallback_key(s["text"])].append(s)

    trends = []
    for name, group in clusters.items():
        strength = sum(1 + (g.get("metric") or 0) / 50 for g in group)
        is_tool = name in config.PULSE_TOOL_DICT
        plats = sorted(set(g["platform"] for g in group))
        rep = max(group, key=lambda g: g.get("metric") or 0)
        blob = " ".join(g["text"] for g in group[:6])
        pillar, fmt = _pillar_format(blob)
        trends.append({
            "name": name.title() if is_tool else rep["text"][:70],
            "category": "tool_launch" if is_tool else "use_case",
            "momentum": momentum.label(name, strength),
            "platforms": _platforms_for(name + " " + blob, plats),
            "what_it_is": "",
            "audience_angle": "",
            "linkedin_angle": "",
            "local_relevance": max((_local_score(g["text"]) for g in group), default=0),
            "pillar": pillar,
            "best_format": fmt,
            "video_worthy": min(10, round(strength)),
            "monetization": {"affiliate_likely": is_tool, "note": ""},
            "sources": [{"platform": g["platform"], "url": g["url"], "signal": g["text"]}
                        for g in sorted(group, key=lambda g: g.get("metric") or 0, reverse=True)[:6]],
            "content_ideas": [],
            "_strength": round(strength, 2),
        })

    trends.sort(key=lambda x: (x["_strength"], x["video_worthy"]), reverse=True)
    trends = [t for t in trends if t["_strength"] >= 1.5][:config.PULSE_MAX_TRENDS]

    tow = trends[0]["name"] if trends else ""
    return {
        "trends": trends,
        "pain_points": _pain_points(signals),
        "tool_of_week_candidate": (tow + " — strongest signal this cycle") if tow else "",
    }
