"""Private, versioned Creator Studio state with the legacy Store API.

Local state belongs outside the published docs tree. Local writes merge
independent records and use a file lock plus record revisions to reject stale
edits. Legacy Firebase REST remains available for compatibility; it has no
server-side revision transaction or new authentication guarantees.
"""

import copy
import hashlib
import json
import os
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone

import requests

from creator.contracts import ValidationError, loads_strict, validate_json_value

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_PATH = os.path.join(ROOT, "docs")
LOCAL_PATH = os.path.join(ROOT, ".studio-private", "pipeline.json")
COLLECTIONS = ("candidates", "sources", "drafts", "settings", "runs")
SCHEMA_VERSION = 1
TIMEOUT = 20


def default_local_path():
    """Resolve the shared owner-state override at call time, never at import time."""
    return os.environ.get("STUDIO_STATE_PATH", "").strip() or LOCAL_PATH


class SchemaError(ValueError):
    """A snapshot is malformed or uses an unsupported schema version."""


class PublicStatePathError(ValueError):
    """Private Studio state cannot be written to the published site tree."""


class RevisionConflict(Exception):
    """An edit was made against a record which has since changed."""

    def __init__(self, coll, record_id, expected_revision, actual_revision):
        self.coll = coll
        self.record_id = record_id
        self.expected_revision = expected_revision
        self.actual_revision = actual_revision
        super().__init__(f"{coll}/{record_id} changed: expected revision "
                         f"{expected_revision}, found {actual_revision}")


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
    """Legacy Firebase board key; it is a namespace, not authentication."""
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


def _revise_draft(previous, document):
    from creator.contracts import content_fingerprint, invalidate_approval
    changed = bool(previous) and content_fingerprint(previous) != content_fingerprint(document)
    artifact_revision = previous.get("revision", 1)
    if type(artifact_revision) is not int or artifact_revision < 1:
        artifact_revision = 1
    document["revision"] = artifact_revision + int(changed)
    return invalidate_approval(previous, document)


def assert_private_path(path):
    """Reject public destinations, including symlinks into the docs directory."""
    resolved = os.path.normcase(os.path.realpath(os.path.abspath(path)))
    public = os.path.normcase(os.path.realpath(PUBLIC_PATH))
    try:
        in_public = os.path.commonpath((public, resolved)) == public
    except ValueError:
        in_public = False
    if in_public:
        raise PublicStatePathError("Studio state belongs outside docs/. Use "
                                   "migrate_studio_state.py for an explicit migration.")
    return resolved


def normalize_snapshot(raw):
    """Validate without dropping malformed collections; normalize legacy records."""
    try:
        validate_json_value(raw)
    except ValidationError as exc:
        raise SchemaError(f"Invalid Studio JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise SchemaError("Studio snapshot must be a JSON object")
    version = raw.get("schema_version", 0)
    if type(version) is not int or version not in (0, SCHEMA_VERSION):
        raise SchemaError(f"Unsupported Studio schema_version: {version!r}")
    updated = raw.get("updated", "")
    if not isinstance(updated, str):
        raise SchemaError("Studio updated timestamp must be a string")
    out = copy.deepcopy(raw)
    out["schema_version"] = SCHEMA_VERSION
    out["updated"] = updated
    for coll in COLLECTIONS:
        records = raw.get(coll)
        if records is None:  # Firebase represents empty collections as null.
            records = {}
        if not isinstance(records, dict):
            raise SchemaError(f"Studio {coll} collection must be an object")
        out[coll] = {}
        for record_id, document in records.items():
            if not isinstance(record_id, str) or not record_id:
                raise SchemaError(f"Studio {coll} record ID must be a nonempty string")
            if not isinstance(document, dict):
                raise SchemaError(f"Studio {coll}/{record_id} must be an object")
            revision = document.get("_revision", 0)
            if type(revision) is not int or revision < 0:
                raise SchemaError(f"Studio {coll}/{record_id} has an invalid _revision")
            if "id" in document and document["id"] != record_id:
                raise SchemaError(f"Studio {coll}/{record_id} has a mismatched id")
            out[coll][record_id] = copy.deepcopy(document)
            out[coll][record_id]["id"] = record_id
            out[coll][record_id]["_revision"] = revision
    deleted = raw.get("_deleted_revisions", {})
    if not isinstance(deleted, dict):
        raise SchemaError("Studio deletion revisions must be an object")
    for coll, records in deleted.items():
        if coll not in COLLECTIONS or not isinstance(records, dict):
            raise SchemaError("Studio deletion revisions have an invalid collection")
        for record_id, revision in records.items():
            if not record_id or type(revision) is not int or revision < 1:
                raise SchemaError("Studio deletion revision must be a positive integer")
            if record_id in out[coll]:
                raise SchemaError(f"Studio {coll}/{record_id} cannot also be deleted")
    return out


def read_snapshot(path):
    """Read a local snapshot. Missing files are empty; corruption is an error."""
    try:
        with open(path, encoding="utf-8") as f:
            raw = loads_strict(f.read())
    except FileNotFoundError:
        raw = {}
    except (ValueError, UnicodeError) as exc:
        raise SchemaError(f"Cannot read Studio snapshot {path}: {exc}") from exc
    return normalize_snapshot(raw)


@contextmanager
def snapshot_lock(path, timeout=20):
    """Advisory lock shared by local writers and the explicit migration CLI."""
    path = assert_private_path(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".lock", "a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if not lock.tell():
            lock.write(b"\0")
            lock.flush()
        if os.name == "nt":
            import msvcrt
            deadline = time.monotonic() + timeout
            while True:
                try:
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"Timed out locking Studio snapshot {path}")
                    time.sleep(0.05)
            try:
                yield
            finally:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            deadline = time.monotonic() + timeout
            while True:
                try:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"Timed out locking Studio snapshot {path}")
                    time.sleep(0.05)
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def write_snapshot(path, snapshot):
    """Atomically replace a private snapshot. Caller must hold snapshot_lock."""
    path = assert_private_path(path)
    snapshot = normalize_snapshot(snapshot)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=os.path.dirname(path),
                                         prefix=".pipeline-", suffix=".tmp", delete=False) as f:
            temp_path = f.name
            json.dump(snapshot, f, ensure_ascii=False, indent=1, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


class Store:
    def __init__(self, backend=None, fb_url=None, key=None, local_path=None):
        self.local_path = os.path.abspath(os.fspath(local_path if local_path is not None else default_local_path()))
        self.fb_url = (fb_url if fb_url is not None
                       else _read_secret("FIREBASE_URL", "firebase_url.txt")).rstrip("/")
        self.key = key or studio_key()
        self.backend = backend or ("firebase" if self.fb_url else "local")
        if self.backend not in ("local", "firebase"):
            raise ValueError("Unknown Studio backend")
        self.data = {c: {} for c in COLLECTIONS}
        self._dirty = {}
        self._pending_revisions = {}
        self._snapshot = normalize_snapshot({})
        self._base = {}
        self.load()

    def _root(self):
        return f"{self.fb_url}/studio/{self.key}"

    def _adopt_snapshot(self, snapshot):
        self._snapshot = copy.deepcopy(snapshot)
        self.data = {c: copy.deepcopy(snapshot[c]) for c in COLLECTIONS}
        self._base = {c: copy.deepcopy(snapshot[c]) for c in COLLECTIONS}

    def load(self):
        if self._dirty:
            raise RuntimeError("Flush or discard pending Studio edits before reloading")
        if self.backend == "firebase":
            r = requests.get(self._root() + ".json", timeout=TIMEOUT)
            r.raise_for_status()
            raw = r.json()
            snapshot = normalize_snapshot({} if raw is None else raw)
        else:
            snapshot = read_snapshot(self.local_path)
        self._adopt_snapshot(snapshot)
        return self

    def export_snapshot(self):
        """Return an independent schema-versioned copy, including pending edits."""
        out = copy.deepcopy(self._snapshot)
        out.update({c: copy.deepcopy(self.data[c]) for c in COLLECTIONS})
        for (coll, record_id), document in self._dirty.items():
            if document is None:
                out.setdefault("_deleted_revisions", {}).setdefault(coll, {})[record_id] = self._pending_revisions[(coll, record_id)]
            else:
                out.get("_deleted_revisions", {}).get(coll, {}).pop(record_id, None)
        out["schema_version"] = SCHEMA_VERSION
        return out

    def flush(self, *, validator=None):
        """Persist buffered records; local conflicts leave every pending edit intact."""
        if not self._dirty:
            return 0
        if validator is not None and not callable(validator):
            raise ValueError("Snapshot validator must be callable")
        n = len(self._dirty)
        if self.backend == "firebase":
            if validator is not None:
                raise ValueError("Snapshot validators require the authoritative local backend")
            # Legacy compatibility only: Firebase PATCH does not provide local CAS.
            by_coll = {}
            for (c, i), doc in self._dirty.items():
                by_coll.setdefault(c, {})[i] = doc
            for c, docs in by_coll.items():
                r = requests.patch(f"{self._root()}/{c}.json", data=json.dumps(docs),
                                   headers={"Content-Type": "application/json"}, timeout=TIMEOUT)
                r.raise_for_status()
            snapshot = self.export_snapshot()
            snapshot["updated"] = now_iso()
        else:
            with snapshot_lock(self.local_path):
                snapshot = read_snapshot(self.local_path)
                for c, i in self._dirty:
                    before = self._base[c].get(i)
                    actual = snapshot[c].get(i)
                    before_deleted = self._snapshot.get("_deleted_revisions", {}).get(c, {}).get(i, 0)
                    actual_deleted = snapshot.get("_deleted_revisions", {}).get(c, {}).get(i, 0)
                    if actual != before or before_deleted != actual_deleted:
                        raise RevisionConflict(c, i, (before or {}).get("_revision", before_deleted),
                                               (actual or {}).get("_revision", actual_deleted))
                # A new draft has no previous record to conflict with. Its source
                # is still a dependency: refuse content based on a stale read.
                for (coll, draft_id), draft in self._dirty.items():
                    if coll != "drafts" or draft is None:
                        continue
                    source_id = draft.get("candidate_id", draft_id)
                    if ("sources", source_id) in self._dirty:
                        continue
                    before = self._base["sources"].get(source_id)
                    actual = snapshot["sources"].get(source_id)
                    before_deleted = self._snapshot.get("_deleted_revisions", {}).get("sources", {}).get(source_id, 0)
                    actual_deleted = snapshot.get("_deleted_revisions", {}).get("sources", {}).get(source_id, 0)
                    if before != actual or before_deleted != actual_deleted:
                        raise RevisionConflict("sources", source_id,
                                               (before or {}).get("_revision", before_deleted),
                                               (actual or {}).get("_revision", actual_deleted))
                for (c, i), doc in self._dirty.items():
                    if doc is None:
                        snapshot[c].pop(i, None)
                        snapshot.setdefault("_deleted_revisions", {}).setdefault(c, {})[i] = self._pending_revisions[(c, i)]
                    else:
                        snapshot[c][i] = copy.deepcopy(doc)
                        snapshot.get("_deleted_revisions", {}).get(c, {}).pop(i, None)
                # A linked draft may have been created after this writer loaded
                # its snapshot. Invalidate it using its latest fields, too.
                for (coll, source_id), source in self._dirty.items():
                    if coll != "sources":
                        continue
                    evidence_revision = (source["_revision"] if source is not None
                                         else self._pending_revisions[(coll, source_id)])
                    for draft_id, draft in list(snapshot["drafts"].items()):
                        if (draft.get("candidate_id", draft_id) != source_id
                                or draft.get("evidence_revision") == evidence_revision):
                            continue
                        revised = copy.deepcopy(draft)
                        revised.update(evidence_revision=evidence_revision,
                                       _revision=draft["_revision"] + 1, updated=now_iso())
                        snapshot["drafts"][draft_id] = _revise_draft(draft, revised)
                        if ("drafts", draft_id) not in self._dirty:
                            n += 1
                snapshot["updated"] = now_iso()
                if validator is not None:
                    validator(snapshot)
                write_snapshot(self.local_path, snapshot)
        self._dirty = {}
        self._pending_revisions = {}
        self._adopt_snapshot(snapshot)
        return n

    def all(self, coll):
        return self.data[coll]

    def get(self, coll, i, default=None):
        return self.data[coll].get(i, default)

    def put(self, coll, i, doc):
        previous = self.data[coll].get(i) or {}
        doc = copy.deepcopy(dict(doc))
        doc["id"] = i
        deleted_revision = self._snapshot.get("_deleted_revisions", {}).get(coll, {}).get(i, 0)
        previous_revision = previous.get("_revision", self._pending_revisions.get((coll, i), deleted_revision))
        doc["_revision"] = previous_revision + 1
        if coll == "drafts":
            source_id = doc.get("candidate_id", i)
            source = self.data["sources"].get(source_id)
            deleted_source = self._pending_revisions.get(("sources", source_id),
                self._snapshot.get("_deleted_revisions", {}).get("sources", {}).get(source_id, 0))
            if source:
                doc["evidence_revision"] = source["_revision"]
            elif deleted_source:
                doc["evidence_revision"] = deleted_source
            elif previous.get("candidate_id", i) != source_id:
                doc.pop("evidence_revision", None)
            doc = _revise_draft(previous, doc)
        doc["updated"] = now_iso()
        self.data[coll][i] = doc
        self._dirty[(coll, i)] = copy.deepcopy(doc)
        self._pending_revisions[(coll, i)] = doc["_revision"]
        if coll == "sources":
            self._invalidate_source_dependents(i, doc["_revision"])
        return doc

    def _invalidate_source_dependents(self, source_id, evidence_revision):
        for draft_id, draft in list(self.data["drafts"].items()):
            if draft.get("candidate_id", draft_id) == source_id:
                self.patch("drafts", draft_id, evidence_revision=evidence_revision)

    def patch(self, coll, i, **fields):
        doc = copy.deepcopy(self.data[coll].get(i) or {"id": i})
        doc.update(fields)
        return self.put(coll, i, doc)

    def patch_if_revision(self, coll, i, fields, expected_revision):
        """Buffer a conditional edit, with zero identifying a new/legacy record."""
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError("expected_revision must be a nonnegative integer")
        if not isinstance(fields, dict):
            raise ValueError("fields must be an object")
        if {"id", "_revision", "updated", "revision"}.intersection(fields):
            raise ValueError("Record identity and revisions are managed by the Store")
        deleted_revision = self._snapshot.get("_deleted_revisions", {}).get(coll, {}).get(i, 0)
        absent_revision = self._pending_revisions.get((coll, i), deleted_revision)
        actual_revision = (self.data[coll].get(i) or {}).get("_revision", absent_revision)
        if expected_revision != actual_revision:
            raise RevisionConflict(coll, i, expected_revision, actual_revision)
        return self.patch(coll, i, **fields)

    def delete(self, coll, i):
        previous = self.data[coll].get(i) or {}
        deleted_revision = self._snapshot.get("_deleted_revisions", {}).get(coll, {}).get(i, 0)
        previous_revision = previous.get("_revision", self._pending_revisions.get((coll, i), deleted_revision))
        self._pending_revisions[(coll, i)] = previous_revision + 1
        self.data[coll].pop(i, None)
        self._dirty[(coll, i)] = None
        if coll == "sources":
            self._invalidate_source_dependents(i, self._pending_revisions[(coll, i)])

    def add_run(self, run):
        i = now_iso().replace(":", "-")
        run = dict(run, ts=now_iso())
        self.put("runs", i, run)
        for old in sorted(self.data["runs"])[:-60]:
            self.delete("runs", old)
        return run

    def published_history(self, limit=40):
        """Published draft history plus signatures from the legacy Firebase board."""
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
