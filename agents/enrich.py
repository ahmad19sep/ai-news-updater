"""Enrich agent: fetches the actual article for a candidate and builds a
SOURCE PACK (clean text excerpt, every number, every quote). No LLM. A draft
is never written from a headline alone: if this fails, the pack is marked
thin and the writer is told so.

Google News feed links are JS redirects with no article text; `resolve_url`
turns them into the publisher's URL first (Google's internal batchexecute
call, the same trick the googlenewsdecoder library uses)."""

import html as htmlmod
import json
import re
from urllib.parse import quote

import requests

import config

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 20
MAX_CHARS = 7000

_DROP = re.compile(r"<(script|style|noscript|svg|nav|footer|header|aside|form|iframe)\b.*?</\1>",
                   re.I | re.S)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t\r\f\v]+")
_NUM = re.compile(r"(?<![\w.])(\$?\d[\d,]*(?:\.\d+)?)\s?(%|percent|million|billion|trillion|k\b|x\b|bn\b|m\b|b\b)?", re.I)
_QUOTE = re.compile(r"[\"“]([^\"”]{25,320})[\"”]")
_GN = re.compile(r"news\.google\.com/(?:rss/)?articles/([^/?#]+)")


# ---- URL resolution ----------------------------------------------------
def resolve_url(url):
    """Publisher URL for a Google News link; any other URL is returned as is."""
    m = _GN.search(url or "")
    if not m:
        return url
    gn_id = m.group(1)
    page = requests.get(f"https://news.google.com/articles/{gn_id}", headers=HEADERS, timeout=TIMEOUT)
    sig = re.search(r'data-n-a-sg="([^"]+)"', page.text)
    ts = re.search(r'data-n-a-ts="([^"]+)"', page.text)
    if not (sig and ts):
        raise ValueError("google news: no decode signature on the page")
    req = ["Fbv4je", ('["garturlreq",[["en-US","US",["FINANCE_TOP_INDICES","WEB_TEST_1_0_0"],null,null,1,1,'
                      '"US:en",null,180,null,null,null,null,null,0,null,null,[1608992183,723341000]],"en-US","US",1,'
                      f'[2,3,4,8],1,0,"655674124",0,0,null,0],"{gn_id}",{ts.group(1)},"{sig.group(1)}"]')]
    r = requests.post("https://news.google.com/_/DotsSplashUi/data/batchexecute",
                      headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
                      data="f.req=" + quote(json.dumps([[req]])), timeout=TIMEOUT)
    body = r.text.split("\n\n", 1)[-1]
    real = json.loads(json.loads(body)[0][2])[1]
    if not isinstance(real, str) or not real.startswith("http"):
        raise ValueError("google news: decode returned no URL")
    return real


# ---- text extraction -----------------------------------------------------
def extract_text(html):
    """Main readable text from an HTML page, as paragraphs."""
    if not html:
        return ""
    html = _DROP.sub(" ", html)
    for tag in ("article", "main"):
        m = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}>", html, re.I | re.S)
        if m and len(_TAG.sub("", m.group(1))) > 400:
            html = m.group(1)
            break
    html = re.sub(r"</(p|div|li|h[1-6]|blockquote|tr|section|br)\s*>|<br\s*/?>", "\n", html, flags=re.I)
    text = htmlmod.unescape(_TAG.sub(" ", html))
    paras = []
    for line in text.split("\n"):
        line = _WS.sub(" ", line).strip()
        if len(line) >= 40 and not re.match(r"^(cookie|subscribe|sign in|share|advertisement)", line, re.I):
            paras.append(line)
    out = "\n\n".join(paras)
    return out[:MAX_CHARS]


def numbers_in(text):
    """Set of normalised numeric tokens ('3.5', '40%', '2 billion' -> '2billion')."""
    out = set()
    for m in _NUM.finditer(text or ""):
        num = m.group(1).replace(",", "").lstrip("$")
        unit = (m.group(2) or "").lower().rstrip(".")
        unit = {"percent": "%", "bn": "billion", "m": "million", "b": "billion"}.get(unit, unit)
        out.add(num + unit)
        out.add(num)
    return out


def quotes_in(text):
    return [q.strip() for q in _QUOTE.findall(text or "")][:12]


def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
    r.raise_for_status()
    ctype = r.headers.get("Content-Type", "")
    if "html" not in ctype and "xml" not in ctype and "text" not in ctype:
        raise ValueError(f"not a web page ({ctype.split(';')[0] or 'unknown type'})")
    return r.text


def build_pack(cand, page_text, note="", url=None):
    excerpt = page_text or ""
    base = " ".join([cand.get("title", ""), cand.get("summary", ""), excerpt])
    thin = len(excerpt) < config.PIPELINE_ENRICH_MIN_CHARS
    return {
        "url": url or cand.get("url", ""), "original_url": cand.get("url", ""),
        "title": cand.get("title", ""),
        "source": cand.get("source", ""), "published": cand.get("published", ""),
        "feed_summary": cand.get("summary", ""),
        "excerpt": excerpt, "chars": len(excerpt),
        "numbers": sorted(numbers_in(base)), "quotes": quotes_in(excerpt),
        "ok": bool(excerpt) and not thin, "thin": thin, "note": note,
    }


def _attempt(url, fetcher, resolver):
    """(text, final_url, note) for one URL; never raises."""
    try:
        final = resolver(url)
    except Exception as e:                          # keep going with the raw link
        final, note = url, f"resolve failed: {type(e).__name__}"
    else:
        note = ""
    try:
        return extract_text(fetcher(final)), final, note
    except Exception as e:                          # paywall, 403, timeout, PDF...
        return "", final, (note + "; " if note else "") + f"fetch failed: {type(e).__name__}: {str(e)[:100]}"


def run(store, candidate_ids, log=print, fetcher=fetch, resolver=resolve_url):
    done, thin = 0, 0
    for i in candidate_ids:
        cand = store.get("candidates", i)
        if not cand:
            continue
        best_text, best_url, notes = "", cand["url"], []
        # the feed link first, then other sites that covered the same story
        for url in [cand["url"]] + [u for u in (cand.get("links") or []) if u != cand["url"]][:3]:
            text, final, note = _attempt(url, fetcher, resolver)
            if note:
                notes.append(note)
            if len(text) > len(best_text):
                best_text, best_url = text, final
            if len(best_text) >= config.PIPELINE_ENRICH_MIN_CHARS:
                break
        pack = build_pack(cand, best_text, "; ".join(notes)[:300], url=best_url)
        from agents.store import now_iso
        pack["fetched_at"] = now_iso()
        store.put("sources", i, pack)
        store.patch("candidates", i, source_ok=pack["ok"], source_chars=pack["chars"], resolved_url=best_url)
        done += 1
        thin += int(pack["thin"])
        log(f"  {'ok  ' if pack['ok'] else 'thin'} {pack['chars']:>5} chars  {cand['title'][:70]}")
    return {"enriched": done, "thin": thin}
