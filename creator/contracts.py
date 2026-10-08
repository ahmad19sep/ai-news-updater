"""Versioned creator records and pure revision rules.

These contracts describe provenance, not a claim that evidence has been fact
checked. Legacy import retains the original records and explicitly starts
source/evidence assessment at ``not_checked``. Nothing here fetches, writes,
publishes, or enables automation.
"""

from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime
import hashlib
import ipaddress
import json
import math
import re
from urllib.parse import urlsplit


SCHEMA_VERSION = 1
UNSAFE_KEYS = frozenset({"__proto__", "prototype", "constructor"})


class ValidationError(ValueError):
    """An input cannot be represented faithfully by the supported contract."""


def validate_json_value(value, path="$", _depth=0):
    """Reject non-JSON values and prototype keys, including in nested objects."""
    if _depth > 64:
        raise ValidationError(f"{path}: JSON nesting exceeds 64 levels")
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is list:
        for i, item in enumerate(value):
            validate_json_value(item, f"{path}[{i}]", _depth + 1)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str or key in UNSAFE_KEYS:
                raise ValidationError(f"{path}: unsafe or non-string object key")
            validate_json_value(item, f"{path}.{key}", _depth + 1)
        return
    raise ValidationError(f"{path}: expected a finite JSON value")


def loads_strict(value):
    """Decode JSON without duplicate fields, NaN, coercion, or repair."""
    def pairs(items):
        out = {}
        for key, item in items:
            if key in out:
                raise ValidationError(f"duplicate field: {key}")
            out[key] = item
        return out

    def invalid_constant(value):
        raise ValidationError(f"invalid JSON constant: {value}")

    try:
        parsed = json.loads(value, object_pairs_hook=pairs,
                            parse_constant=invalid_constant)
    except (ValueError, TypeError) as exc:
        raise ValidationError(str(exc)) from exc
    validate_json_value(parsed)
    return parsed


def text_hash(text):
    if type(text) is not str:
        raise ValidationError("content text must be a string")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _string(value, name, allow_empty=True):
    if type(value) is not str or (not allow_empty and not value.strip()):
        raise ValidationError(f"{name}: expected {'nonempty ' if not allow_empty else ''}string")


def _positive(value, name):
    if type(value) is not int or value < 1:
        raise ValidationError(f"{name}: expected positive integer")


def _strings(value, name):
    if type(value) is not tuple or any(type(v) is not str for v in value):
        raise ValidationError(f"{name}: expected an array of strings")


def _choice(value, name, choices):
    if type(value) is not str or value not in choices:
        raise ValidationError(f"{name}: unsupported value")


def _digest(value, name):
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValidationError(f"{name}: expected lowercase SHA-256")


def validate_url(value, allow_empty=False):
    """Validate a public HTTP(S) link without requesting it or resolving DNS.

    This is a record/link check. Retrieval still needs redirect and DNS/SSRF
    controls at the fetcher's network boundary.
    """
    if allow_empty and value == "":
        return value
    _string(value, "URL", False)
    if any(c.isspace() or ord(c) < 32 for c in value) or "\\" in value:
        raise ValidationError("URL: whitespace, controls and backslashes are forbidden")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ValidationError("URL: invalid host or port") from exc
    if (parsed.scheme not in ("http", "https") or not hostname
            or parsed.username is not None or parsed.password is not None
            or (port is not None and port < 1)):
        raise ValidationError("URL: expected HTTP(S) host without credentials")
    host = hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise ValidationError("URL: local hosts are forbidden")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        try:
            ascii_host = host.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise ValidationError("URL: invalid hostname") from exc
        if (len(ascii_host) > 253 or "." not in ascii_host
                or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", part)
                       for part in ascii_host.split("."))):
            raise ValidationError("URL: invalid public hostname")
    else:
        if not address.is_global:
            raise ValidationError("URL: private or reserved addresses are forbidden")
    return value


def _instant(value, name, allow_date=False):
    if value is None:
        return
    _string(value, name, False)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{name}: expected ISO timestamp") from exc
    if allow_date and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValidationError(f"{name}: timezone required")


class _Record:
    """Small shared strict codec; field types are validated by each record."""
    _arrays = ()
    _records = {}

    @classmethod
    def from_dict(cls, raw):
        validate_json_value(raw)
        if type(raw) is not dict:
            raise ValidationError(f"{cls.__name__}: expected object")
        allowed = {f.name for f in fields(cls)}
        unknown = set(raw) - allowed
        if unknown:
            raise ValidationError(f"{cls.__name__}: unknown fields {sorted(unknown)}")
        if type(raw.get("schema_version")) is not int or raw["schema_version"] != SCHEMA_VERSION:
            raise ValidationError(f"{cls.__name__}: unsupported or missing schema_version")
        values = dict(raw)
        for key in cls._arrays:
            if key in values:
                if type(values[key]) is not list:
                    raise ValidationError(f"{key}: expected array")
                values[key] = tuple(values[key])
        for key, model in cls._records.items():
            if key not in values:
                continue
            if key in cls._arrays:
                values[key] = tuple(model.from_dict(v) for v in values[key])
            elif values[key] is not None:
                values[key] = model.from_dict(values[key])
        try:
            return cls(**values)
        except TypeError as exc:
            raise ValidationError(f"{cls.__name__}: missing or invalid fields") from exc

    def to_dict(self):
        return json.loads(json.dumps(asdict(self), ensure_ascii=False, allow_nan=False))

    def _base(self):
        if type(self.schema_version) is not int or self.schema_version != SCHEMA_VERSION:
            raise ValidationError("unsupported schema_version")
        _string(self.id, "id", False)
        _positive(self.revision, "revision")


@dataclass(frozen=True)
class SourceDocument(_Record):
    id: str
    original_url: str
    canonical_url: str
    publisher: str
    content_hash: str
    text: str = ""
    revision: int = 1
    source_type: str = "unknown"
    language: str = "und"
    publication_time: str | None = None
    modification_time: str | None = None
    retrieval_time: str | None = None
    extraction_method: str = "unknown"
    truncated: bool | None = False
    retrieval_outcome: str = "not_checked"
    usage_restrictions: tuple[str, ...] = ()
    schema_version: int = SCHEMA_VERSION
    _arrays = ("usage_restrictions",)

    def __post_init__(self):
        self._base()
        validate_url(self.original_url, allow_empty=True)
        validate_url(self.canonical_url, allow_empty=True)
        for name in ("publisher", "language", "extraction_method", "text"):
            _string(getattr(self, name), name)
        _choice(self.source_type, "source_type", {"unknown", "official", "paper", "documentation",
                                                "reporting", "discussion", "owner_note"})
        _choice(self.retrieval_outcome, "retrieval_outcome", {"not_checked", "retrieved", "failed", "restricted"})
        if self.truncated is not None and type(self.truncated) is not bool:
            raise ValidationError("truncated: expected boolean or unknown (null)")
        _strings(self.usage_restrictions, "usage_restrictions")
        for name in ("publication_time", "modification_time"):
            _instant(getattr(self, name), name, allow_date=True)
        _instant(self.retrieval_time, "retrieval_time")
        _digest(self.content_hash, "content_hash")
        if self.content_hash != text_hash(self.text):
            raise ValidationError("source content_hash does not match available text")


@dataclass(frozen=True)
class DocumentRevision(_Record):
    id: str
    content_hash: str
    revision: int = 1
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self):
        self._base()
        _digest(self.content_hash, "content_hash")


@dataclass(frozen=True)
class EvidenceSpan(_Record):
    id: str
    document_id: str
    document_revision: int
    content_hash: str
    start: int
    end: int
    quote: str
    revision: int = 1
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self):
        self._base()
        _string(self.document_id, "document_id", False)
        _positive(self.document_revision, "document_revision")
        _digest(self.content_hash, "content_hash")
        if type(self.start) is not int or type(self.end) is not int or not 0 <= self.start < self.end:
            raise ValidationError("evidence span needs nonempty integer offsets")
        _string(self.quote, "quote", False)
        if self.end - self.start != len(self.quote):
            raise ValidationError("evidence quote length does not match offsets")

    def validate_provenance(self, document):
        if not isinstance(document, SourceDocument):
            raise ValidationError("span requires SourceDocument")
        if (document.id != self.document_id or document.revision != self.document_revision
                or document.content_hash != self.content_hash):
            raise ValidationError("evidence references a different source revision")
        if self.end > len(document.text) or document.text[self.start:self.end] != self.quote:
            raise ValidationError("evidence quote does not match source text")
        return self


@dataclass(frozen=True)
class EvidenceClaim(_Record):
    id: str
    text: str
    span_ids: tuple[str, ...] = ()
    assessment: str = "not_checked"
    attribution: str = ""
    caveat: str = ""
    revision: int = 1
    schema_version: int = SCHEMA_VERSION
    _arrays = ("span_ids",)

    def __post_init__(self):
        self._base()
        _string(self.text, "claim text", False)
        _strings(self.span_ids, "span_ids")
        _string(self.attribution, "attribution")
        _string(self.caveat, "caveat")
        _choice(self.assessment, "assessment", {"not_checked", "supported", "attributed", "disputed", "unresolved"})
        if self.assessment in ("supported", "attributed") and not self.span_ids:
            raise ValidationError("supported or attributed claim requires evidence spans")
        if self.assessment == "attributed" and not self.attribution:
            raise ValidationError("attributed claim requires attribution")


@dataclass(frozen=True)
class EvidencePack(_Record):
    id: str
    documents: tuple[DocumentRevision, ...] = ()
    spans: tuple[EvidenceSpan, ...] = ()
    claims: tuple[EvidenceClaim, ...] = ()
    caveats: tuple[str, ...] = ()
    unresolved_questions: tuple[str, ...] = ()
    assessment: str = "not_checked"
    freshness: str = "unknown"
    revision: int = 1
    schema_version: int = SCHEMA_VERSION
    _arrays = ("documents", "spans", "claims", "caveats", "unresolved_questions")
    _records = {"documents": DocumentRevision, "spans": EvidenceSpan, "claims": EvidenceClaim}

    def __post_init__(self):
        self._base()
        _choice(self.assessment, "assessment", {"not_checked", "checked", "disputed"})
        _choice(self.freshness, "freshness", {"unknown", "current", "stale"})
        for name in ("caveats", "unresolved_questions"):
            _strings(getattr(self, name), name)
        for name, model in self._records.items():
            values = getattr(self, name)
            if type(values) is not tuple or any(not isinstance(v, model) for v in values):
                raise ValidationError(f"{name}: expected {model.__name__} records")
            if len({v.id for v in values}) != len(values):
                raise ValidationError(f"{name}: duplicate IDs")
        refs = {d.id: d for d in self.documents}
        for span in self.spans:
            ref = refs.get(span.document_id)
            if ref is None or ref.revision != span.document_revision or ref.content_hash != span.content_hash:
                raise ValidationError("span references a missing or different document revision")
        span_ids = {s.id for s in self.spans}
        if any(set(c.span_ids) - span_ids for c in self.claims):
            raise ValidationError("claim references unknown evidence spans")
        if self.assessment == "checked" and not self.documents:
            raise ValidationError("checked evidence pack requires documents")

    def validate_provenance(self, documents):
        for ref in self.documents:
            source = documents.get(ref.id)
            if (not isinstance(source, SourceDocument) or source.revision != ref.revision
                    or source.content_hash != ref.content_hash):
                raise ValidationError("missing or mismatched source revision")
        for span in self.spans:
            span.validate_provenance(documents[span.document_id])
        return self


@dataclass(frozen=True)
class StoryBrief(_Record):
    id: str
    evidence_pack_id: str
    evidence_pack_revision: int
    title: str
    summary: str
    reader_relevance: str = ""
    claim_ids: tuple[str, ...] = ()
    caveats: tuple[str, ...] = ()
    unresolved_questions: tuple[str, ...] = ()
    revision: int = 1
    schema_version: int = SCHEMA_VERSION
    _arrays = ("claim_ids", "caveats", "unresolved_questions")

    def __post_init__(self):
        self._base()
        _string(self.evidence_pack_id, "evidence_pack_id", False)
        _positive(self.evidence_pack_revision, "evidence_pack_revision")
        for name in ("title", "summary", "reader_relevance"):
            _string(getattr(self, name), name)
        for name in self._arrays:
            _strings(getattr(self, name), name)

    def validate_evidence(self, pack):
        if (not isinstance(pack, EvidencePack) or pack.id != self.evidence_pack_id
                or pack.revision != self.evidence_pack_revision
                or set(self.claim_ids) - {c.id for c in pack.claims}):
            raise ValidationError("brief references missing or different evidence")
        return self


@dataclass(frozen=True)
class Approval(_Record):
    revision: int
    content_hash: str
    approved_at: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self):
        if type(self.schema_version) is not int or self.schema_version != SCHEMA_VERSION:
            raise ValidationError("unsupported approval schema_version")
        _positive(self.revision, "approval revision")
        _digest(self.content_hash, "approval content_hash")
        _instant(self.approved_at, "approved_at")


@dataclass(frozen=True)
class ContentVariant(_Record):
    id: str
    story_id: str
    body: str
    story_revision: int = 1
    source_comment: str = ""
    platform: str = "linkedin"
    content_type: str = "text"
    language: str = "en"
    angle: str = ""
    hashtags: tuple[str, ...] = ()
    claim_refs: tuple[str, ...] = ()
    creator_note_refs: tuple[str, ...] = ()
    asset_refs: tuple[str, ...] = ()
    evidence_pack_id: str = ""
    evidence_pack_revision: int = 1
    review_state: str = "draft"
    prompt_version: str = ""
    generation_run_id: str = ""
    scheduled_for: str | None = None
    scheduling_timezone: str | None = None
    published_at: str | None = None
    approval: Approval | None = None
    revision: int = 1
    schema_version: int = SCHEMA_VERSION
    _arrays = ("hashtags", "claim_refs", "creator_note_refs", "asset_refs")
    _records = {"approval": Approval}

    def __post_init__(self):
        self._base()
        for name in ("story_id", "platform", "content_type", "language"):
            _string(getattr(self, name), name, False)
        _positive(self.story_revision, "story_revision")
        for name in ("body", "source_comment", "angle", "evidence_pack_id", "prompt_version", "generation_run_id"):
            _string(getattr(self, name), name)
        _positive(self.evidence_pack_revision, "evidence_pack_revision")
        for name in self._arrays:
            _strings(getattr(self, name), name)
        _choice(self.review_state, "review_state", {"draft", "approved", "scheduled", "published", "rejected", "skip"})
        _instant(self.scheduled_for, "scheduled_for")
        _instant(self.published_at, "published_at")
        if self.scheduling_timezone is not None:
            _string(self.scheduling_timezone, "scheduling_timezone", False)
        if self.approval is not None and not isinstance(self.approval, Approval):
            raise ValidationError("approval: expected Approval record")
        if self.approval is not None and not approval_matches(self.to_dict()):
            raise ValidationError("approval does not match content revision")

    def validate_story(self, brief):
        if (not isinstance(brief, StoryBrief) or brief.id != self.story_id
                or brief.revision != self.story_revision
                or brief.evidence_pack_id != self.evidence_pack_id
                or brief.evidence_pack_revision != self.evidence_pack_revision
                or set(self.claim_refs) - set(brief.claim_ids)):
            raise ValidationError("variant references missing or different shared brief")
        return self


def _effective(record, override, original, fallback):
    if record.get(override) is not None:
        return record[override]
    return record.get(original, record.get(fallback, ""))


def content_fingerprint(record):
    """Hash material artifact inputs, excluding status and storage CAS metadata.

    Legacy edits override generated text. ``revision`` is the content revision;
    storage can independently increment ``_revision`` for every conditional write.
    """
    validate_json_value(record)
    if type(record) is not dict:
        raise ValidationError("artifact must be an object")
    material = {
        "body": _effective(record, "edited_post", "body", "post"),
        "comment": _effective(record, "edited_comment", "source_comment", "first_comment"),
        "hashtags": record.get("hashtags", []),
        "platform": record.get("platform", record.get("channel", "linkedin")),
        "content_type": record.get("content_type", record.get("format", "text")),
        "language": record.get("language", "en"),
    }
    for key in ("title", "url", "source", "candidate_id", "facts", "angle", "claims", "claim_refs", "creator_note_refs",
                "story_id", "story_revision", "evidence", "evidence_revision", "evidence_pack_id", "evidence_pack_revision", "evidence_refs",
                "source_pack", "source_revision", "source_hash", "asset_refs", "asset_ids", "assets", "visual", "image_prompt"):
        material[key] = record.get(key)
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    return text_hash(encoded)


def approval_matches(record):
    """True only for an approval of this exact immutable content revision."""
    approval = record.get("approval")
    revision = record.get("revision")
    if (type(approval) is not dict or type(revision) is not int or revision < 1
            or type(approval.get("revision")) is not int):
        return False
    return approval.get("revision") == revision and approval.get("content_hash") == content_fingerprint(record)


def invalidate_approval(previous, updated):
    """Clear approval on a material edit without altering historical publication."""
    result = dict(updated)
    if content_fingerprint(previous) == content_fingerprint(updated):
        return result
    result["approval"] = None
    for field in ("approved_revision", "approved_hash", "approved_at"):
        result.pop(field, None)
    status_key = "review_state" if "review_state" in result else "status"
    if result.get(status_key) in ("approved", "scheduled"):
        result[status_key] = "draft"
    return result


def revise_variant(variant, **changes):
    """Produce a new revision; status-only changes keep the content approval."""
    if not isinstance(variant, ContentVariant):
        raise ValidationError("expected ContentVariant")
    if set(changes) & {"id", "revision", "schema_version", "approval"}:
        raise ValidationError("identity, revision and approval cannot be edited directly")
    candidate = replace(variant, approval=None, **changes)
    if content_fingerprint(candidate.to_dict()) == content_fingerprint(variant.to_dict()):
        return replace(candidate, approval=variant.approval)
    state = "draft" if candidate.review_state in ("approved", "scheduled") else candidate.review_state
    return replace(candidate, revision=variant.revision + 1, approval=None, review_state=state)


def convert_legacy_state(state):
    """Return an additive migration preview, retaining the exact legacy JSON.

    No file or provider is touched. IDs, original links and all old metadata
    remain under ``legacy_state``; new records never inherit old verification or
    approval badges. Unsupported/invalid source links fail rather than being
    silently repaired. A store-level migration performs backup and integrity
    checks before writing this preview anywhere.
    """
    validate_json_value(state)
    if type(state) is not dict:
        raise ValidationError("legacy state must be an object")
    legacy = json.loads(json.dumps(state, ensure_ascii=False, allow_nan=False))
    sources, packs, briefs, variants = {}, {}, {}, {}
    id_map = {"sources": {}, "drafts": {}}
    old_sources = state.get("sources") or {}
    old_drafts = state.get("drafts") or {}
    if type(old_sources) is not dict or type(old_drafts) is not dict:
        raise ValidationError("legacy sources and drafts must be objects")
    for source_id, old in old_sources.items():
        if type(old) is not dict:
            raise ValidationError(f"legacy source {source_id}: expected object")
        text = old.get("excerpt", "")
        publication_time = old.get("published") or None
        try:
            _instant(publication_time, "legacy publication time", allow_date=True)
        except ValidationError:
            # Retain unparseable values verbatim in legacy_state; unknown time
            # must not be inferred from a collector/storage timestamp.
            publication_time = None
        document = SourceDocument(id=source_id, original_url=old.get("original_url") or old.get("url", ""),
                                  canonical_url=old.get("url", ""), publisher=old.get("source", ""),
                                  text=text, content_hash=text_hash(text), extraction_method="legacy_excerpt",
                                  publication_time=publication_time,
                                  truncated=None, retrieval_outcome="not_checked")
        # Old excerpts had a length cap, but did not retain whether the original
        # source was complete. Retain an unknown truncation indicator.
        pack = EvidencePack(id=source_id, documents=(DocumentRevision(source_id, document.content_hash),),
                            caveats=("Legacy source coverage and claims have not been checked.",))
        sources[source_id], packs[source_id] = document.to_dict(), pack.to_dict()
        id_map["sources"][source_id] = source_id
    for draft_id, old in old_drafts.items():
        if type(old) is not dict:
            raise ValidationError(f"legacy draft {draft_id}: expected object")
        source_id = old.get("candidate_id") or draft_id
        if source_id not in packs:
            packs[source_id] = EvidencePack(id=source_id, caveats=("No imported source text; research required.",)).to_dict()
        brief = StoryBrief(id=source_id, evidence_pack_id=source_id, evidence_pack_revision=1,
                           title=old.get("title", ""), summary="",
                           caveats=("Imported draft is an editorial output, not factual evidence.",))
        briefs.setdefault(source_id, brief.to_dict())
        variant = ContentVariant(id=draft_id, story_id=source_id, body=_effective(old, "edited_post", "body", "post"),
                                 source_comment=_effective(old, "edited_comment", "source_comment", "first_comment"),
                                 platform=old.get("channel") or "linkedin", content_type=old.get("format") or "text",
                                 language=old.get("language") or "en", hashtags=tuple(old.get("hashtags") or ()),
                                 evidence_pack_id=source_id, review_state=old.get("status") or "draft",
                                 scheduled_for=old.get("scheduled_for"), published_at=old.get("published_at"),
                                 scheduling_timezone=old.get("scheduling_timezone"))
        variants[draft_id] = variant.to_dict()
        id_map["drafts"][draft_id] = draft_id
    return {"schema_version": SCHEMA_VERSION, "legacy_state": legacy, "source_documents": sources,
            "evidence_packs": packs, "story_briefs": briefs, "content_variants": variants,
            "id_map": id_map, "automation_enabled": False}


def preview_caption(brief):
    """Nonproduction adapter proving a format can draw from the shared brief."""
    if not isinstance(brief, StoryBrief):
        raise ValidationError("preview adapter accepts StoryBrief only")
    return ContentVariant(id=f"{brief.id}:preview-caption", story_id=brief.id,
                          story_revision=brief.revision, body=brief.summary,
                          platform="test_caption", claim_refs=brief.claim_ids,
                          evidence_pack_id=brief.evidence_pack_id,
                          evidence_pack_revision=brief.evidence_pack_revision,
                          prompt_version="nonproduction-preview-v1")
