"""Verify agent: two layers.

1. `checks()` — deterministic, no LLM, unit-tested: every number in the post
   must exist in the source pack; banned phrases and AI sentence patterns;
   hook length vs LinkedIn's preview cut; length, hashtags, links, markdown.
2. `judge()` — a model reads post + source and flags unsupported claims and
   generic "AI voice".

`run()` combines them into pass / warn / fail with a list of issues the
writer can act on for one rewrite.
"""

import re

from agents import content
from agents.enrich import numbers_in

HOOK_MOBILE = 140       # chars before "...see more" on the LinkedIn mobile feed
HOOK_DESKTOP = 210
MAX_CHARS = 3000        # LinkedIn hard limit
MIN_CHARS = 400
MAX_HASHTAGS = 3

BANNED_PHRASES = [
    "game changer", "game-changer", "gamechanger", "revolutionise", "revolutionize",
    "unlock the power", "unlock value", "next big thing", "cutting-edge", "cutting edge",
    "seamless", "transformative", "in today's world", "the future is here",
    "ai is changing everything", "disrupt every industry", "paradigm shift", "landscape",
    "delve", "dive in", "deep dive", "supercharge", "elevate", "testament", "underscore",
    "leverage", "harness", "robust", "buckle up", "let that sink in", "mind-blowing",
    "follow me for more", "repost ♻", "comment yes", "tag someone", "agree?",
]
BANNED_PATTERNS = [
    (r"\bit'?s not (just|only) [^.\n]{2,60}, it'?s\b", "'It's not just X, it's Y' pattern"),
    (r"\bthe real [^.\n]{2,40} isn'?t [^.\n]{2,60}, it'?s\b", "'The real X isn't Y, it's Z' pattern"),
    (r"\bhere'?s the thing\b", "'Here's the thing' opener"),
    (r"\bat the end of the day\b", "'At the end of the day' closer"),
    (r"\bultimately,", "'Ultimately,' closer"),
    (r"\blink in (the )?(comments|bio)\b", "'link in comments' bait"),
    (r"\bin a (major|significant|big) (development|move|step)\b", "press-release opener"),
]
_URL = re.compile(r"https?://\S+|www\.\S+", re.I)
_MD = re.compile(r"(\*\*|__|^#{1,6}\s|^\s*[-*]\s{1}\S)", re.M)
_YEAR = re.compile(r"^(19|20)\d\d$")


def _first_line(post):
    return (post or "").strip().split("\n")[0].strip()


def checks(post, pack, allowed_text="", hashtags=None):
    """Deterministic checks. Returns {'issues': [...], 'verdict', 'hook', 'chars'}."""
    issues = []
    post = post or ""
    hook = _first_line(post)

    def add(level, code, msg):
        issues.append({"level": level, "code": code, "msg": msg})

    # numbers must come from the source (title, summary, excerpt, quotes) or the angle
    source_text = " ".join([pack.get("title", ""), pack.get("feed_summary", ""),
                            pack.get("excerpt", ""), " ".join(pack.get("quotes", [])), allowed_text or ""])
    allowed = numbers_in(source_text)
    for tok in sorted(numbers_in(post)):
        base = re.sub(r"[^\d.]", "", tok)
        if tok in allowed or base in allowed or _YEAR.match(base) or base in ("1", "2", "3", "one"):
            continue
        add("fail", "number", f"'{tok}' is not in the source material")

    low = post.lower()
    for ph in BANNED_PHRASES:
        if ph in low:
            add("fail", "banned", f"banned phrase: '{ph}'")
    for pat, label in BANNED_PATTERNS:
        if re.search(pat, post, re.I):
            add("fail" if "bait" in label else "warn", "pattern", label)

    if len(hook) > HOOK_DESKTOP:
        add("fail", "hook", f"hook is {len(hook)} chars; it gets cut at ~{HOOK_DESKTOP} on desktop")
    elif len(hook) > HOOK_MOBILE:
        add("warn", "hook", f"hook is {len(hook)} chars; mobile preview cuts at ~{HOOK_MOBILE}")
    if len(post) > MAX_CHARS:
        add("fail", "length", f"{len(post)} chars exceeds LinkedIn's {MAX_CHARS} limit")
    elif len(post) < MIN_CHARS:
        add("warn", "length", f"only {len(post)} chars — short for a LinkedIn post")
    tags = hashtags if hashtags is not None else re.findall(r"#\w+", post)
    if len(tags) > MAX_HASHTAGS:
        add("fail", "hashtags", f"{len(tags)} hashtags (max {MAX_HASHTAGS})")
    if _URL.search(post):
        add("warn", "link", "a link inside the post body reduces reach — move it to the first comment")
    if _MD.search(post):
        add("fail", "markdown", "markdown formatting (**, #, - lists) does not render on LinkedIn")

    verdict = ("fail" if any(i["level"] == "fail" for i in issues)
               else "warn" if issues else "pass")
    return {"issues": issues, "verdict": verdict, "hook": hook, "hook_len": len(hook), "chars": len(post)}


JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "unsupported_claims": {"type": "array", "items": {"type": "string"}},
        "misattributed": {"type": "array", "items": {"type": "string"}},
        "ai_smell": {"type": "integer", "minimum": 1, "maximum": 5},
        "specificity": {"type": "integer", "minimum": 1, "maximum": 5},
        "fixes": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": ["unsupported_claims", "misattributed", "ai_smell", "specificity", "fixes", "summary"],
    "additionalProperties": False,
}

JUDGE_SYSTEM = """You are a strict fact-checker and editor for LinkedIn posts about AI.
You get a POST and the SOURCE TEXT it was written from.

1. unsupported_claims: every statement of fact in the post that the source
   text does not support (numbers, names, dates, features, results, quotes,
   causes). Quote the offending phrase. Interpretation clearly framed as the
   author's opinion is fine; a vendor claim presented as established fact is
   'misattributed', not unsupported.
2. ai_smell 1-5: 1 = reads like a specific person with a view; 5 = generic
   AI-generated LinkedIn text (vague, symmetrical sentences, rule-of-three,
   motivational closer, nothing a competitor could not have written).
3. specificity 1-5: 5 = concrete details, named things, a clear position.
4. fixes: the shortest list of concrete edits that would make it pass.
Be precise and brief."""


def judge(llm, post, pack):
    user = ("POST:\n" + post + "\n\nSOURCE TEXT:\n" + (pack.get("excerpt") or pack.get("feed_summary") or "(none)")
            + "\n\nTITLE: " + pack.get("title", "") + "\nSOURCE: " + pack.get("source", ""))
    return llm.json("verify", JUDGE_SYSTEM, user, JUDGE_SCHEMA, max_tokens=2500)


def run(llm, draft, pack, log=print, use_llm=True):
    """Combine deterministic checks + judge. Returns the verification dict."""
    angle_text = " ".join([draft.get("angle", {}).get("angle", ""), draft.get("angle", {}).get("hook", "")])
    result = checks(draft.get("post", ""), pack, allowed_text=angle_text, hashtags=draft.get("hashtags"))
    if use_llm and draft.get("post"):
        try:
            j = judge(llm, draft["post"], pack)
        except Exception as e:
            j = {"summary": f"judge failed: {e}", "unsupported_claims": [], "misattributed": [],
                 "ai_smell": 0, "specificity": 0, "fixes": []}
            result["issues"].append({"level": "warn", "code": "judge", "msg": str(e)[:160]})
        result["judge"] = j
        for c in j.get("unsupported_claims") or []:
            result["issues"].append({"level": "fail", "code": "unsupported", "msg": c})
        for c in j.get("misattributed") or []:
            result["issues"].append({"level": "warn", "code": "attribution", "msg": c})
        if (j.get("ai_smell") or 0) >= 4:
            result["issues"].append({"level": "warn", "code": "ai_smell", "msg": f"reads generic (ai_smell {j['ai_smell']}/5)"})
        if (j.get("specificity") or 5) <= 2:
            result["issues"].append({"level": "warn", "code": "vague", "msg": f"low specificity ({j['specificity']}/5)"})
    result["verdict"] = ("fail" if any(i["level"] == "fail" for i in result["issues"])
                         else "warn" if result["issues"] else "pass")
    log(f"  verify: {result['verdict']}  ({len(result['issues'])} issues)")
    return result


def fix_list(result):
    out = [i["msg"] for i in result.get("issues", []) if i["level"] == "fail"]
    out += list((result.get("judge") or {}).get("fixes") or [])
    return out[:12]
