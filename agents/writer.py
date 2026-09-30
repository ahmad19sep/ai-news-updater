"""Writer agent: one story + one angle + your voice -> one LinkedIn draft,
a first comment (with the source link) and up to 3 hashtags. Every claim is
tagged with the source fact it rests on so the verifier can check it."""

from agents import content

SCHEMA = {
    "type": "object",
    "properties": {
        "post": {"type": "string"},
        "first_comment": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "support": {"type": "string"},
                    "kind": {"type": "string", "enum": ["reported_fact", "attributed_claim", "my_interpretation", "unsupported"]},
                },
                "required": ["claim", "support", "kind"],
                "additionalProperties": False,
            },
        },
        "review_notes": {"type": "string"},
        "status": {"type": "string", "enum": ["draft", "skip"]},
    },
    "required": ["post", "first_comment", "hashtags", "claims", "review_notes", "status"],
    "additionalProperties": False,
}

SYSTEM_HEAD = """You write ONE LinkedIn post for the creator described below, in
their voice, from the supplied source text and the chosen angle. You are an
editorial assistant, not a publisher: the creator will edit and post it.

THE POST:
- Line 1 is the hook. It must carry the point in under 140 characters, then a
  blank line. Use the supplied hook or improve it — same idea, sharper.
- Body: natural short paragraphs, 900-1600 characters total for a normal post,
  shorter when the idea is small. One idea. Concrete details from the source.
  Say what it means for the reader; end when the idea is complete.
- Plain text only: no markdown, no bold markers, no bullet symbols unless the
  angle is a genuine list. 0-2 emojis. No links inside the post.
- Do not put "link in comments" or any engagement bait in the post.
- Never invent a number, name, date, quote, price, feature or result. A
  vendor's claim stays attributed ("OpenAI says", "according to the paper").
- First-person experience ("I tested", "my client") ONLY if the PERSONAL NOTE
  supplies it. Otherwise write as someone who reads this space and thinks
  carefully about it.
- Opinions are welcome and should be marked my_interpretation in claims.

FIRST COMMENT: one or two lines — the source name and the link, plus at most
one extra useful line (a caveat, or the one detail that did not fit). This is
where the link lives.

HASHTAGS: 0-3, specific to the topic, lowercase-friendly (e.g. #ai #healthcare).

CLAIMS: list every factual statement in the post with the sentence from the
source it rests on. If you cannot point to support, mark it 'unsupported' and
remove it from the post. Numbers must appear in the source verbatim.

STATUS: 'skip' only when the source truly cannot support a useful post; then
say why in review_notes and leave post empty.

REVIEW NOTES (private, never posted): what is interpretation vs reported, any
opinion needing the creator's approval, anything you deliberately left out."""


def system_prompt():
    voice = content.voice()
    return "\n\n".join([
        SYSTEM_HEAD,
        "CREATOR:\n" + voice["who"],
        "AUDIENCE:\n" + voice["audience"],
        "TONE:\n" + voice["tone"],
        "NEVER:\n" + voice["never"],
        "LINKEDIN RULES:\n" + content.rules(),
        "EXAMPLES OF THE CREATOR'S BEST POSTS (match the voice, never reuse the content):\n" + content.examples(),
    ])


def user_prompt(pack, angle, note="", recent=None, fix_issues=None, previous=None):
    parts = [
        "STORY: " + (pack.get("title") or ""),
        f"SOURCE: {pack.get('source')}  ({pack.get('url')})  published {(pack.get('published') or '')[:10]}",
        ("SOURCE WARNING: the article could not be fetched or is very short. Write only what the "
         "material below supports and keep it short and honest. " + (pack.get("note") or ""))
        if pack.get("thin") else "",
        "SOURCE TEXT:\n" + (pack.get("excerpt") or pack.get("feed_summary") or "(headline only)"),
        ("QUOTES:\n" + "\n".join("- " + q for q in pack.get("quotes", [])[:8])) if pack.get("quotes") else "",
        "ANGLE: " + angle.get("angle", "") + "\nHOOK: " + angle.get("hook", "")
        + f"\nMODE: {angle.get('mode', 'insight')}   FORMAT: {angle.get('format', 'text')}",
        "PERSONAL NOTE (owner-supplied, real): " + note if note else
        "PERSONAL NOTE: none — do not write any firsthand experience claim.",
        ("RECENTLY POSTED (do not repeat these angles or openings):\n"
         + "\n".join(f"- {r.get('title', '')} | {r.get('hook', '')}" for r in recent)) if recent else "",
        ("YOUR PREVIOUS DRAFT FAILED VERIFICATION. Fix these issues and return a corrected post:\n"
         + "\n".join("- " + x for x in fix_issues) + "\n\nPREVIOUS DRAFT:\n" + (previous or ""))
        if fix_issues else "",
    ]
    return "\n\n".join(p for p in parts if p)


def run(llm, store, cand_id, angle_index=None, note="", recent=None, log=print,
        fix_issues=None, previous=None):
    cand = store.get("candidates", cand_id)
    pack = store.get("sources", cand_id) or {"title": cand.get("title"), "url": cand.get("url"),
                                              "source": cand.get("source"), "thin": True}
    angles = cand.get("angles") or [{"angle": cand.get("angle_hint", ""), "hook": "", "mode": "insight", "format": "text"}]
    idx = cand.get("recommended", 0) if angle_index is None else angle_index
    angle = angles[min(idx, len(angles) - 1)]
    result = llm.json("writer", system_prompt(),
                      user_prompt(pack, angle, note=note, recent=recent, fix_issues=fix_issues, previous=previous),
                      SCHEMA, max_tokens=6000, cache_system=True)
    result["angle"] = angle
    result["angle_index"] = idx
    log(f"  writer: {result.get('status')}  {len(result.get('post', ''))} chars")
    return result
