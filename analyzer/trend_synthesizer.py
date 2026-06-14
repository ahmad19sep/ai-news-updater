"""LLM analyzer (PULSE_USE_LLM = True). Clusters + enriches raw signals via
Groq or Anthropic (plain REST, no SDK). Keys come from env / GitHub Secrets.

Guardrails: must return ONLY JSON; must ground every item in real signals;
on any failure returns {} so the caller falls back to the raw synthesizer.
"""

import json
import os
import re

import requests

import config

PROMPT = r"""You are a trend analyst for "AI x Ahmad", an AI-education content brand for
Urdu/Hindi-speaking audiences in Pakistan and India (tagline: "AI Ki Duniya, Simple Urdu Mein").
The audience cares about PRACTICAL use and EARNING with AI, framed as "what this means for YOU" —
not technical specs.

Below are real signals collected in the last 48 hours from Google Trends, YouTube, Reddit, and
Hacker News. Identify 6 to 12 distinct, real trends. STRONGLY PREFER specific named tools,
models, or techniques (e.g. a named app/model like "Nano Banana", "Veo 3", "Sora") over broad
generic themes — only fall back to a broad theme when the signals are genuinely generic. Use ONLY
what the signals support — never invent a tool or trend. Attach the supporting source URLs to each item.

Return ONLY a JSON object (no prose, no code fences) matching this schema:
{
  "trends": [
    {
      "name": "<short name, e.g. 'Nano Banana image generation'>",
      "category": "tool_launch | technique | use_case | debate",
      "momentum": "rising | hot | cooling",
      "platforms": ["google","youtube","reddit","hackernews","instagram_inferred","facebook_inferred","linkedin_inferred"],
      "what_it_is": "<one plain sentence, simple language>",
      "audience_angle": "<why an Urdu/Hindi viewer should care - the 'what this means for you' hook>",
      "linkedin_angle": "<if this trend has a professional/career/productivity framing, the LinkedIn-post angle in one line; else empty>",
      "local_relevance": 0,
      "pillar": "practical_earning | explainer | discovery | news",
      "best_format": "long_form | short | reel | carousel",
      "video_worthy": 0,
      "monetization": { "affiliate_likely": true, "note": "<e.g. tool has an affiliate program>" },
      "sources": [ { "platform": "...", "url": "...", "signal": "<the raw text/metric>" } ],
      "content_ideas": [ "<concrete Urdu video/Reel title idea 1>", "<idea 2>", "<idea 3>" ]
    }
  ],
  "pain_points": [
    {
      "problem": "<e.g. 'Claude usage/token limits hitting users hard'>",
      "who_affected": "<who is complaining>",
      "signal_strength": 0,
      "sources": [ { "platform": "...", "url": "..." } ],
      "content_opportunity": "<the explainer/workaround/tutorial angle for AI x Ahmad, in one line>"
    }
  ],
  "tool_of_week_candidate": "<the single best trend to anchor a weekly signature video, with one line why>"
}

Scoring guidance: prioritize trends that are practical/earning-focused, visually demonstrable, and
locally relevant (PK/IN, Urdu/Hindi). A real problem people face is HIGH value because it makes
great tutorial/explainer content. For trends with a clear work/career/productivity angle, fill
linkedin_angle. Be honest about momentum - only mark "rising" if recent signals genuinely outweigh
older ones. Use category "tool_launch" whenever a trend centers on a specific named AI tool or
model (these feed the Rising Tools list, so don't lump tools as "use_case"). Write every
content_idea in ROMAN URDU (Urdu written in English letters) with light English — for example
"ChatGPT se paisay kaise kamayein" or "Ye naya AI tool sab kuch badal dega". Aim for at least
3 content_ideas per trend. local_relevance and video_worthy are 0-10; signal_strength is 0-10.

SIGNALS:
__SIGNALS__"""

_MOMENTUM = {"rising", "hot", "cooling"}


def _key(provider):
    return os.environ.get(
        {"groq": "GROQ_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}[provider], "").strip()


def _call_groq(key, model, prompt):
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers={"Authorization": "Bearer " + key,
                               "Content-Type": "application/json"},
                      json={"model": model, "temperature": 0.4,
                            "response_format": {"type": "json_object"},
                            "messages": [{"role": "user", "content": prompt}]},
                      timeout=90)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _call_anthropic(key, model, prompt):
    r = requests.post("https://api.anthropic.com/v1/messages",
                      headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                               "Content-Type": "application/json"},
                      json={"model": model, "max_tokens": 4096,
                            "messages": [{"role": "user", "content": prompt}]},
                      timeout=90)
    r.raise_for_status()
    return "".join(c.get("text", "") for c in r.json().get("content", []))


def _parse(text):
    if not text:
        return None
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _num(v, lo=0, hi=10):
    try:
        return max(lo, min(hi, int(round(float(v)))))
    except Exception:
        return 0


def _validate(obj):
    trends = []
    for t in obj.get("trends", []) or []:
        if not isinstance(t, dict) or not t.get("name") or not t.get("sources"):
            continue  # must be grounded in sources
        mon = t.get("monetization") or {}
        vw = _num(t.get("video_worthy"))
        trends.append({
            "name": str(t["name"])[:80],
            "category": t.get("category", "use_case"),
            "momentum": t.get("momentum") if t.get("momentum") in _MOMENTUM else "hot",
            "platforms": [p for p in (t.get("platforms") or []) if isinstance(p, str)],
            "what_it_is": str(t.get("what_it_is", ""))[:200],
            "audience_angle": str(t.get("audience_angle", ""))[:300],
            "linkedin_angle": str(t.get("linkedin_angle", ""))[:300],
            "local_relevance": _num(t.get("local_relevance")),
            "pillar": t.get("pillar", "discovery"),
            "best_format": t.get("best_format", "short"),
            "video_worthy": vw,
            "monetization": {"affiliate_likely": bool(mon.get("affiliate_likely")),
                             "note": str(mon.get("note", ""))[:160]},
            "sources": [{"platform": str(s.get("platform", "")), "url": str(s.get("url", "")),
                         "signal": str(s.get("signal", ""))[:200]}
                        for s in (t.get("sources") or []) if isinstance(s, dict) and s.get("url")][:6],
            "content_ideas": [str(i)[:160] for i in (t.get("content_ideas") or [])][:4],
            "_strength": vw or 1,
        })
    pains = []
    for p in obj.get("pain_points", []) or []:
        if not isinstance(p, dict) or not p.get("problem"):
            continue
        pains.append({
            "problem": str(p["problem"])[:200],
            "who_affected": str(p.get("who_affected", ""))[:120],
            "signal_strength": _num(p.get("signal_strength")),
            "sources": [{"platform": str(s.get("platform", "")), "url": str(s.get("url", ""))}
                        for s in (p.get("sources") or []) if isinstance(s, dict) and s.get("url")][:6],
            "content_opportunity": str(p.get("content_opportunity", ""))[:300],
        })
    return {"trends": trends[:config.PULSE_MAX_TRENDS],
            "pain_points": pains[:config.PULSE_MAX_PAIN_POINTS],
            "tool_of_week_candidate": str(obj.get("tool_of_week_candidate", ""))[:200]}


def synthesize(signals):
    provider = config.PULSE_LLM_PROVIDER
    key = _key(provider)
    if not key:
        return {}  # no key -> caller falls back to raw mode
    model = config.PULSE_LLM_MODELS.get(provider)

    # Feed the LLM the SPECIFIC signals first (real posts/video titles) and push
    # generic search-autocomplete to the back, so it forms specific named trends
    # instead of collapsing everything into a few broad themes.
    ordered = sorted(signals, key=lambda s: 1 if s.get("type") == "search_suggest" else 0)
    slim = [{"platform": s["platform"], "text": s["text"], "url": s["url"],
             "metric": s.get("metric", 0)} for s in ordered[:150]]
    prompt = PROMPT.replace("__SIGNALS__", json.dumps(slim, ensure_ascii=False))

    for _ in range(2):  # retry once, then give up (caller falls back)
        try:
            text = (_call_groq if provider == "groq" else _call_anthropic)(key, model, prompt)
            obj = _parse(text)
            if obj and isinstance(obj.get("trends"), list) and obj["trends"]:
                return _validate(obj)
        except Exception:
            continue
    return {}
