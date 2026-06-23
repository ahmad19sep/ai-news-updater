"""
AI Radar -> Caira dispatch.

When a fresh story scores high enough, automatically create a task in Caira
(your worker app), assigned to whichever editor has the fewest pending tasks.
Also drains a manual queue that the studio's "Send to Caira" button writes to
Firebase, so you can push any story by hand too.

Caira must expose TWO simple endpoints (auth: Bearer CAIRA_API_KEY):

  GET  {CAIRA_API_URL}/pending-counts
       -> JSON {"<editorId>": <number of open tasks>, ...}   (for load balancing)

  POST {CAIRA_API_URL}/tasks      (JSON body below) -> any 2xx = created
       {
         "external_id": "<stable id, so Caira can ignore duplicates>",
         "title":   "...",
         "url":     "https://original-source",
         "source":  "TechCrunch",
         "summary": "",
         "category":"AI General News",
         "score":   14,
         "assignee":"boy1",
         "status":  "assigned",
         "prompt":  "<the full master prompt the worker pastes into GPT/Claude>"
       }

If your real Caira API differs, only `pending_counts()` and `create_task()`
below need editing — everything else stays the same.
"""

import difflib
import hashlib
import json
import os
import re

import requests

import config

TIMEOUT = 15


# ----- credentials / config (keys come from env or gitignored files) -----
def _key():
    k = os.environ.get("CAIRA_API_KEY", "").strip()
    if not k:
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "caira_key.txt")) as f:
                k = f.read().strip()
        except FileNotFoundError:
            pass
    return k


def _base():
    url = os.environ.get("CAIRA_API_URL", "").strip() or getattr(config, "CAIRA_API_URL", "")
    return url.rstrip("/")


def _headers():
    return {"Authorization": "Bearer " + _key(), "Content-Type": "application/json"}


def enabled():
    return getattr(config, "CAIRA_ENABLED", False) and bool(_key()) and bool(_base())


def _firebase():
    url = os.environ.get("FIREBASE_URL", "").strip()
    if not url:
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "firebase_url.txt")) as f:
                url = f.read().strip()
        except FileNotFoundError:
            pass
    return url.rstrip("/")


# ----- Caira API (the only two functions tied to Caira's shape) -----
def pending_counts():
    """{editorId: openTaskCount}. Empty on any failure (-> everyone treated as 0)."""
    try:
        r = requests.get(_base() + "/pending-counts", headers=_headers(), timeout=TIMEOUT)
        r.raise_for_status()
        return {str(k): int(v) for k, v in (r.json() or {}).items()}
    except Exception:
        return {}


def create_task(item, prompt, assignee):
    """Create one Caira task. Returns True on success."""
    body = {
        "external_id": hashlib.sha1((item.get("url") or item.get("title", "")).encode("utf-8")).hexdigest()[:16],
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "source": item.get("source", ""),
        "summary": item.get("summary", ""),
        "category": item.get("category", ""),
        "score": item.get("score", 0),
        "assignee": assignee,
        "status": "assigned",
        "prompt": prompt,
    }
    try:
        r = requests.post(_base() + "/tasks", headers=_headers(),
                          data=json.dumps(body), timeout=TIMEOUT)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"  [!] Caira create_task failed: {type(e).__name__}")
        return False


# ----- load balancing -----
def pick_editor(counts=None):
    """The editor with the fewest pending tasks (unknown counts treated as 0)."""
    counts = pending_counts() if counts is None else counts
    editors = getattr(config, "CAIRA_EDITORS", None) or list(counts.keys())
    if not editors:
        return None
    return min(editors, key=lambda e: counts.get(e, 0))


# ----- the master prompt the worker copies (PDF [[MARKER]] format) -----
def build_master_prompt(item):
    title = item.get("title", "")
    src = item.get("url", "")
    return (
        'You are a world-class senior journalist (Reuters, BBC, AP, NYT). Read the source story '
        'and produce professional, accurate journalism plus ready-to-post social content for a '
        'GLOBAL audience, in clear simple English.\n\n'
        f'SOURCE STORY: {title}\n'
        + (f'SOURCE LINK: {src}\nFIRST open and read the source carefully.\n' if src else '')
        + '\nRules: accuracy and neutrality. Use ONLY facts from the source — never invent quotes, '
        'numbers, names or events. No sensationalism. Plain text (no markdown).\n\n'
        'Output EXACTLY in this format, each [[MARKER]] on its own line, nothing before [[HEADLINE]] '
        'or after [[RISK_LEVEL]]. Where a social post needs the article link, write the literal '
        'token [ARTICLE LINK].\n\n'
        '[[HEADLINE]]\n(compelling, accurate headline)\n'
        '[[ARTICLE]]\n(500-700 word article: strong lede, short paragraphs, context, significance, attribution)\n'
        '[[X_POST]]\n(substantial single X post: scroll-stopping hook, 3-5 short point lines with why it '
        'matters, one engagement line, then the link on its own final line)\n'
        '[[LINKEDIN_POST]]\n(professional: hook, key insight + implications, a discussion prompt; end "Read more:\\n[ARTICLE LINK]")\n'
        '[[FACEBOOK_POST]]\n(engaging hook, easy short paragraphs, a question to spark comments, 2-3 hashtags; end "Read the full story:\\n[ARTICLE LINK]")\n'
        '[[INSTAGRAM_CAPTION]]\n(hook first line, short engaging lines, tasteful emojis, then "Full story — link in bio", 6-10 hashtags)\n'
        '[[WHATSAPP_POST]]\n(very concise, key facts first, mobile-friendly, few emojis; end "Read more:\\n[ARTICLE LINK]")\n'
        '[[YOUTUBE_SHORT_SCRIPT]]\n(45-60 sec spoken script: hook, the key development, a CTA to follow)\n'
        '[[IMAGE_PROMPT]]\n(a vertical 4:5 news-poster image-generation prompt: photorealistic cinematic scene '
        'relevant to the story, with the headline beautifully rendered ON the image in bold modern type; spell it exactly; no logos/watermarks)\n'
        '[[FACT_CHECK_NOTES]]\n(the key source facts + any caution/uncertainty)\n'
        '[[RISK_LEVEL]]\nlow / medium / high\n'
    )


# ----- dispatch -----
def _normalize_pick(p):
    return {
        "title": p.get("title", ""),
        "url": p.get("url", ""),
        "source": p.get("source", ""),
        "summary": p.get("summary", ""),
        "category": config.CATEGORIES.get(p.get("category"), "") if isinstance(p.get("category"), int)
                    else p.get("category", ""),
        "score": p.get("score", 0),
    }


def _norm_title(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower())).strip()


def _fb_get(path):
    base = _firebase()
    if not base:
        return None
    try:
        return requests.get(base + path, timeout=TIMEOUT).json()
    except Exception:
        return None


def _handled(conn):
    """Everything already handled ANYWHERE -> (set of urls, list of normalized
    titles). Sources: tasks already sent to Caira (caira_sent), stories marked
    done in the studio (Firebase news_done), published articles + their
    duplicate signatures (news_posted / published). Used so a done story — and
    any similar-topic story — is never auto-picked again."""
    import database
    urls, titles = set(), []

    def add_sig(u=None, t=None, links=None):
        if u:
            urls.add(u)
        for l in (links or []):
            if l:
                urls.add(l)
        if t:
            titles.append(_norm_title(t))

    for s in json.loads(database.get_meta(conn, "caira_sent", "[]") or "[]"):
        if isinstance(s, dict):
            add_sig(s.get("u"), s.get("t"))
        elif isinstance(s, str):
            urls.add(s)

    d = _fb_get("/news_done.json")
    for u in (d if isinstance(d, list) else []):
        if u:
            urls.add(u)

    p = _fb_get("/news_posted.json")
    for s in (p if isinstance(p, list) else (list(p.values()) if isinstance(p, dict) else [])):
        if s:
            add_sig(s.get("u"), s.get("t"), s.get("l"))

    pub = _fb_get("/published.json")
    for a in (pub.values() if isinstance(pub, dict) else []):
        if a:
            add_sig(a.get("url"), a.get("title"))

    return urls, titles


def _blocked(pick, urls, titles, threshold=0.72):
    """True if this story is already handled or is the same topic as one."""
    if pick.get("url") in urls:
        return True
    nt = _norm_title(pick.get("title"))
    if not nt:
        return False
    if nt in titles:
        return True
    for t in titles:                       # similar-topic (reworded headline)
        if t and difflib.SequenceMatcher(None, nt, t).ratio() >= threshold:
            return True
    return False


def _drain_manual_queue(conn):
    """Send anything the studio's 'Send to Caira' button queued to Firebase."""
    base = _firebase()
    if not base:
        return 0
    try:
        data = requests.get(base + "/caira_queue.json", timeout=TIMEOUT).json() or {}
    except Exception:
        return 0
    if not isinstance(data, dict):
        return 0
    import database
    counts = pending_counts()
    sigs = json.loads(database.get_meta(conn, "caira_sent", "[]") or "[]")
    n = 0
    for key, it in data.items():
        if not it or not it.get("url"):
            continue
        item = _normalize_pick(it)
        # blank assignee -> Caira load-balances across ALL its workers itself
        ed = it.get("assignee") or pick_editor(counts) or ""
        if create_task(item, build_master_prompt(item), ed):
            if ed:
                counts[ed] = counts.get(ed, 0) + 1   # keep balancing within this run
            sigs.append({"u": it.get("url"), "t": it.get("title", "")})
            n += 1
            print(f"  [>] Caira (manual) -> {ed or 'auto'}: {item['title'][:55]}")
        try:
            requests.delete(base + "/caira_queue/" + key + ".json", timeout=TIMEOUT)
        except Exception:
            pass
    if n:
        database.set_meta(conn, "caira_sent", json.dumps(sigs[-500:]))
    return n


def dispatch(conn):
    """Auto-create Caira tasks for high-scoring fresh stories (load-balanced),
    plus drain the manual queue. Returns how many tasks were created."""
    if not enabled():
        return 0
    import database
    import scoring

    total = _drain_manual_queue(conn)

    target = getattr(config, "CAIRA_SCORE_TARGET", 10)
    cap = getattr(config, "CAIRA_MAX_PER_RUN", 6)
    counts = pending_counts()
    urls, htitles = _handled(conn)   # everything already handled, anywhere

    # stored signatures of what we've sent (kept so similar-topic dedup persists)
    sigs = []
    for s in json.loads(database.get_meta(conn, "caira_sent", "[]") or "[]"):
        sigs.append(s if isinstance(s, dict) else {"u": s, "t": ""})

    # skip anything already handled OR a similar-topic story to one
    picks = [p for p in scoring.score_items(conn)
             if p["score"] >= target and not _blocked(p, urls, htitles)]
    made = 0
    for p in picks[:cap]:
        # If Caira tells us who's free, balance here; otherwise send blank and
        # let Caira distribute across all its workers (scales to any number).
        ed = pick_editor(counts) or ""
        item = _normalize_pick(p)
        if create_task(item, build_master_prompt(item), ed):
            if ed:
                counts[ed] = counts.get(ed, 0) + 1
            sigs.append({"u": p["url"], "t": p["title"]})
            urls.add(p["url"])
            htitles.append(_norm_title(p["title"]))   # block similar ones this run too
            made += 1
            print(f"  [>] Caira -> {ed or 'auto'} (score {p['score']}): {p['title'][:55]}")

    if made:
        database.set_meta(conn, "caira_sent", json.dumps(sigs[-500:]))
    return total + made


# fields Caira returns for an approved task -> staged for the studio Ready tab
_READY_FIELDS = ("title", "headline", "article", "x_post", "linkedin_post",
                 "facebook_post", "instagram_caption", "whatsapp_post",
                 "youtube_short_script", "image_prompt", "fact_check_notes",
                 "risk_level", "source", "source_url", "drive_url", "assignee")


def fetch_ready(conn):
    """Pull APPROVED tasks from Caira and stage them in Firebase /ready_to_post
    for the studio's Ready-to-Post tab. De-dupes by task id. Returns how many
    new ready items were staged.

    Needs a third Caira endpoint:
      GET {CAIRA_API_URL}/ready  (Bearer auth) -> JSON list of approved tasks,
      each with: id + the parsed sections in _READY_FIELDS.
    """
    if not enabled():
        return 0
    fb = _firebase()
    if not fb:
        return 0
    try:
        r = requests.get(_base() + "/ready", headers=_headers(), timeout=TIMEOUT)
        r.raise_for_status()
        items = r.json() or []
    except Exception:
        return 0
    if not isinstance(items, list):
        items = list(items.values()) if isinstance(items, dict) else []

    import time as _t
    import database
    seen = set(json.loads(database.get_meta(conn, "caira_ready_seen", "[]") or "[]"))
    n = 0
    for it in items:
        tid = str(it.get("id") or it.get("external_id") or "")
        if not tid or tid in seen:
            continue
        body = {k: it.get(k) for k in _READY_FIELDS if it.get(k) is not None}
        body["ts"] = int(_t.time() * 1000)
        try:
            requests.put(fb + "/ready_to_post/" + tid + ".json",
                         data=json.dumps(body), timeout=TIMEOUT)
            seen.add(tid)
            n += 1
        except Exception:
            pass
    if n:
        database.set_meta(conn, "caira_ready_seen", json.dumps(list(seen)[-400:]))
        print(f"  [<] Caira: {n} approved task(s) -> Ready to Post")
    return n
