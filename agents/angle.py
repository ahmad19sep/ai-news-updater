"""Angle agent: for one shortlisted story, propose 2-3 honest angles with a
hook line and the best LinkedIn format, then recommend one. Reads the real
source pack, never just the headline."""

from agents import content

SCHEMA = {
    "type": "object",
    "properties": {
        "angles": {
            "type": "array", "minItems": 1, "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "angle": {"type": "string"},
                    "hook": {"type": "string"},
                    "format": {"type": "string", "enum": ["text", "carousel", "image"]},
                    "mode": {"type": "string", "enum": ["insight", "practical", "story", "question"]},
                    "why": {"type": "string"},
                    "supported_by": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["angle", "hook", "format", "mode", "why", "supported_by"],
                "additionalProperties": False,
            },
        },
        "recommended": {"type": "integer", "minimum": 0, "maximum": 2},
        "skip": {"type": "boolean"},
        "skip_reason": {"type": "string"},
    },
    "required": ["angles", "recommended", "skip", "skip_reason"],
    "additionalProperties": False,
}

SYSTEM = """You are the angle editor for a LinkedIn creator who posts about AI.
Given ONE story with its actual source text, propose the 2-3 most useful
angles for the audience below, each with a hook line, then recommend one.

An angle is a specific claim about what this means for the reader: a decision
it forces, a consequence most people will miss, a practical thing to try or to
avoid, an honest comparison. It is NOT a summary of the news.

Hook rules: the hook is the first line of the post and must survive on its
own — LinkedIn cuts the preview at about 140 characters on mobile. Specific
beats clever. No questions-as-bait, no "Big news", no "Thread", no emoji walls.
Draw on the hook library patterns below when useful but never copy one.

Format: 'carousel' when the source supports 4-8 concrete steps/points/comparisons
that would read well as slides; 'image' when one number or one line carries
the post; otherwise 'text'.

Honesty: every angle lists the source facts it rests on (quote or paraphrase
from SOURCE TEXT). If the source is thin, propose fewer angles and say so in
'why'. If nothing here is useful for this audience, set skip=true with a
one-line reason — no post is a fine outcome."""


def _pack_text(pack):
    parts = [f"TITLE: {pack.get('title')}", f"SOURCE: {pack.get('source')}  ({pack.get('url')})",
             f"PUBLISHED: {(pack.get('published') or '')[:10]}"]
    if pack.get("feed_summary"):
        parts.append("FEED SUMMARY: " + pack["feed_summary"])
    if pack.get("thin"):
        parts.append("WARNING: the article could not be fetched or is very short — "
                     "work only with what is here and say so. " + (pack.get("note") or ""))
    parts.append("SOURCE TEXT:\n" + (pack.get("excerpt") or "(none)"))
    if pack.get("quotes"):
        parts.append("QUOTES FOUND:\n" + "\n".join("- " + q for q in pack["quotes"][:8]))
    return "\n\n".join(parts)


def run(llm, store, cand_id, log=print):
    cand = store.get("candidates", cand_id)
    pack = store.get("sources", cand_id) or {}
    voice = content.voice()
    system = (SYSTEM + "\n\nAUDIENCE:\n" + voice["audience"] + "\n\nCREATOR:\n" + voice["who"]
              + "\n\nHOOK LIBRARY (patterns, not templates):\n" + content.hooks_text())
    user = (_pack_text(pack) + "\n\nTRIAGE NOTE: " + (cand.get("angle_hint") or "")
            + f"\nTOPIC: {cand.get('topic')}  SCORE: {cand.get('score')}")
    result = llm.json("angle", system, user, SCHEMA, max_tokens=4000)
    angles = result.get("angles") or []
    rec = min(int(result.get("recommended", 0)), max(len(angles) - 1, 0))
    store.patch("candidates", cand_id, angles=angles, recommended=rec,
                skip=bool(result.get("skip")), skip_reason=result.get("skip_reason", ""))
    if result.get("skip"):
        log(f"  skip: {result.get('skip_reason', '')[:90]}")
    else:
        log(f"  angle: {angles[rec]['angle'][:90]}" if angles else "  (no angles)")
    return result
