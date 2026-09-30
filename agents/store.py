"""Shared pipeline state: what the agents produce and what you decide in the
Studio (shortlist, approve, mark posted, rate).

Two backends, same API:
  * Firebase Realtime Database (when FIREBASE_URL / firebase_url.txt exists):
    everything lives under  /studio/<key>/  where <key> is derived from the
    Studio access code exactly like the Studio does, so every device and the
    cloud see one state.
  * Local JSON file (docs/pipeline.json) otherwise: the Studio loads that file
    from the site, so committing it publishes the pipeline output.

Collections: candidates, sources, drafts, settings, runs. Documents are plain
dicts keyed by a short id. Writes are buffered and flushed by the orchestrator
after each stage.
"""

import hashlib
import json
import os
from datetime import datetime, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_PATH = os.path.join(ROOT, "docs", "pipeline.json")
COLLECTIONS = ("candidates", "sources", "drafts", "settings", "runs")
TIMEOUT = 20


def _read_secret(env_name, file_name):
    value = os.environ.get(env_name, "").strip()
    if value:
        return value
    try:
        with open(os.path.join(ROOT, file_name), encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def studio_key():
    """Same derivation as the Studio's BOARDKEY: sha256('aixboard:' + code)[:40]."""
    override = os.environ.get("STUDIO_KEY", "").strip()
    if override:
        return override
    code = _read_secret("SITE_PASSCODE", "site_passcode.txt")
    if not code:
        return "local"
    return hashlib.sha256(("aixboard:" + code).encode()).hexdigest()[:40]


def doc_id(url):
    return hashlib.sha1((url or "").strip().encode()).hexdigest()[:12]


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Store:
    def __init__(self, backend=None, fb_url=None, key=None, local_path=None):
        self.local_path = local_path or LOCAL_PATH
        self.fb_url = (fb_url if fb_url is not None
                       else _read_secret("FIREBASE_URL", "firebase_url.txt")).rstrip("/")
        self.key = key or studio_key()
        self.backend = backend or ("firebase" if self.fb_url else "local")
        self.data = {c: {} for c in COLLECTIONS}
        self._dirty = {}          # (collection, id) -> doc or None (deleted)
        self.load()

    # ---- backend I/O -------------------------------------------------
    def _root(self):
        return f"{self.fb_url}/studio/{self.key}"

    def load(self):
        raw = None
        if self.backend == "firebase":
            r = requests.get(self._root() + ".json", timeout=TIMEOUT)
            r.raise_for_status()
            raw = r.json()
        else:
            try:
                with open(self.local_path, encoding="utf-8") as f:
                    raw = json.load(f)
            except (FileNotFoundError, ValueError):
                raw = None
        raw = raw or {}
        for c in COLLECTIONS:
            coll = raw.get(c) or {}
            self.data[c] = dict(coll) if isinstance(coll, dict) else {}
        return self

    def flush(self):
        """Write buffered changes. Firebase: one PATCH per collection with
        multi-path semantics; local: rewrite the file."""
        if not self._dirty:
            return 0
        n = len(self._dirty)
        if self.backend == "firebase":
            by_coll = {}
            for (c, i), doc in self._dirty.items():
                by_coll.setdefault(c, {})[i] = doc
            for c, docs in by_coll.items():
                r = requests.patch(f"{self._root()}/{c}.json", data=json.dumps(docs),
                                   headers={"Content-Type": "application/json"}, timeout=TIMEOUT)
                r.raise_for_status()
        else:
            os.makedirs(os.path.dirname(self.local_path), exist_ok=True)
            out = {c: self.data[c] for c in COLLECTIONS}
            out["updated"] = now_iso()
            tmp = self.local_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=1)
            os.replace(tmp, self.local_path)
        self._dirty = {}
        return n

    # ---- document API ------------------------------------------------
    def all(self, coll):
        return self.data[coll]

    def get(self, coll, i, default=None):
        return self.data[coll].get(i, default)

    def put(self, coll, i, doc):
        doc = dict(doc)
        doc.setdefault("id", i)
        doc["updated"] = now_iso()
        self.data[coll][i] = doc
        self._dirty[(coll, i)] = doc
        return doc

    def patch(self, coll, i, **fields):
        doc = dict(self.data[coll].get(i) or {"id": i})
        doc.update(fields)
        return self.put(coll, i, doc)

    def delete(self, coll, i):
        self.data[coll].pop(i, None)
        self._dirty[(coll, i)] = None

    def add_run(self, run):
        i = now_iso().replace(":", "-")
        run = dict(run, ts=now_iso())
        self.put("runs", i, run)
        # keep the ledger short
        for old in sorted(self.data["runs"])[:-60]:
            self.delete("runs", old)
        return run

    # ---- history the writer must not repeat ----------------------------
    def published_history(self, limit=40):
        """Titles/urls of what was actually posted: pipeline drafts marked
        published, plus the legacy Studio 'posted' signatures if on Firebase."""
        out = []
        for d in self.data["drafts"].values():
            if d.get("status") == "published":
                out.append({"title": d.get("title", ""), "url": d.get("url", ""),
                            "when": d.get("published_at") or d.get("updated", ""),
                            "hook": (d.get("post") or "").split("\n")[0][:160]})
        if self.backend == "firebase":
            for path in ("news_posted", "published"):
                try:
                    r = requests.get(f"{self.fb_url}/{path}.json", timeout=TIMEOUT)
                    raw = r.json() if r.ok else None
                except (requests.RequestException, ValueError):
                    raw = None
                items = raw if isinstance(raw, list) else list((raw or {}).values())
                for sig in items:
                    if isinstance(sig, dict):
                        out.append({"title": sig.get("t") or sig.get("title", ""),
                                    "url": sig.get("u") or sig.get("url", ""), "when": "", "hook": ""})
        out.sort(key=lambda x: x["when"], reverse=True)
        return out[:limit]
