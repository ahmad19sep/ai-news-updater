"""Authenticated, loopback-only Studio backed by private local state.

Run: STUDIO_LOCAL_PASSCODE=<configure in your terminal> python studio_server.py
This development/local-owner bridge neither connects to Firebase nor publishes.
"""

import argparse
import hashlib
import hmac
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from flask import Flask, abort, jsonify, redirect, request, session, send_from_directory

from agents.store import LOCAL_PATH, RevisionConflict, SchemaError, Store, now_iso
from agents import verify
from creator.contracts import approval_matches, content_fingerprint, loads_strict, validate_json_value

ROOT = Path(__file__).resolve().parent
ID = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
RESERVED = {"id", "_revision", "revision", "schema_version", "approval", "approved_at", "published_at", "owner_uid", "credentials", "automation_enabled"}
FIELDS = {
    "candidates": set("title url resolved_url source category published summary score topic urgency reason angle_hint status manual created source_ok source_chars skip skip_reason".split()),
    "sources": set("url original_url title source published feed_summary excerpt chars quotes thin ok note fetched_at numbers retrieval_state content_hash documents evidence_ids".split()),
    "drafts": set("candidate_id title url source topic score angle angles format channel language post edited_post first_comment edited_comment hashtags claims review_notes verify status created thin_source manual facts summary visual scheduled_for scheduling_timezone rating stats notes asset_ids claim_refs creator_note_refs".split()),
    "settings": set("personal_note audience postsPerWeek slots timezone language".split()),
}


def validate_fields(collection, fields):
    """Validate the compatibility editing surface without coercing model output."""
    nullable = {"edited_post", "edited_comment", "scheduled_for", "rating", "angle"}
    booleans = {"manual", "source_ok", "skip", "thin", "ok", "thin_source"}
    integers = {"source_chars", "chars", "postsPerWeek", "rating"}
    arrays = {"quotes", "numbers", "documents", "evidence_ids", "angles", "hashtags", "claims", "slots", "asset_ids", "claim_refs", "creator_note_refs"}
    objects = {"angle", "verify", "stats"}
    for name, value in fields.items():
        if value is None and name in nullable:
            continue
        if name in booleans:
            valid = type(value) is bool
        elif name in integers:
            valid = type(value) is int and value >= 0
        elif name == "score":
            valid = type(value) in (int, float) and 0 <= value <= 10
        elif name in arrays:
            valid = isinstance(value, list)
            if valid:
                if name in {"claims", "angles", "documents"}:
                    valid = all(isinstance(item, dict) for item in value)
                else:
                    valid = all(isinstance(item, str) for item in value)
        elif name in objects:
            valid = isinstance(value, dict)
        else:
            valid = isinstance(value, str)
        if not valid:
            raise ValueError(f"Invalid type or value for {name}")
    if "postsPerWeek" in fields and not 1 <= fields["postsPerWeek"] <= 14:
        raise ValueError("Choose a weekly goal from 1 to 14 posts")
    if fields.get("rating") is not None and "rating" in fields and not 1 <= fields["rating"] <= 10:
        raise ValueError("Rating must be from 1 to 10")
    if "slots" in fields:
        if not fields["slots"] or any(not re.fullmatch(r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) (?:[01]\d|2[0-3]):[0-5]\d", value) for value in fields["slots"]):
            raise ValueError("Slots must use a day and time such as Tue 09:00")
    if "stats" in fields and any(value is not None and (type(value) not in (int, float) or value < 0) for value in fields["stats"].values()):
        raise ValueError("Stats must contain nonnegative numbers or null")
    if collection == "drafts" and "channel" in fields and fields["channel"] != "linkedin":
        raise ValueError("Only the manual LinkedIn channel is active")
    for name in {"url", "resolved_url", "original_url"} & fields.keys():
        value = fields[name]
        if not value:  # An owner-written story can have facts without a URL.
            continue
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username is not None or parsed.password is not None:
            raise ValueError("Source links must be http(s) addresses without credentials")


def scheduled_time(value):
    try:
        when = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValueError("Choose a future schedule with an explicit timezone") from None
    if when.tzinfo is None or when.utcoffset() is None:
        raise ValueError("Choose a future schedule with an explicit timezone")
    return when


def _configured_passcode():
    value = os.environ.get("STUDIO_LOCAL_PASSCODE") or os.environ.get("SITE_PASSCODE")
    if value:
        return value.strip()
    secret_file = ROOT / "site_passcode.txt"
    return secret_file.read_text(encoding="utf-8").strip() if secret_file.is_file() else ""


def create_app(state_path=None, passcode=None, secret_key=None, docs_dir=None):
    passcode = _configured_passcode() if passcode is None else passcode
    if not isinstance(passcode, str) or len(passcode) < 8:
        raise ValueError("Configure STUDIO_LOCAL_PASSCODE with at least 8 characters in your terminal before starting the private Studio.")
    state_path = str(Path(state_path or os.environ.get("STUDIO_STATE_PATH") or LOCAL_PATH).resolve())
    docs_dir = Path(docs_dir or ROOT / "docs").resolve()
    # Fail before serving when the store is corrupt or configured under public docs.
    if Path(state_path).is_relative_to(ROOT / "docs") or Path(state_path).is_relative_to(docs_dir):
        raise ValueError("Private state must be outside the public docs directory.")
    Store(backend="local", local_path=state_path)
    signing_key = secret_key or os.environ.get("STUDIO_SESSION_SECRET") or secrets.token_hex(32)
    if not isinstance(signing_key, str) or len(signing_key) < 32:
        raise ValueError("STUDIO_SESSION_SECRET must contain at least 32 characters, or omit it for an automatically generated key.")
    app = Flask(__name__, static_folder=None)
    app.config.update(
        SECRET_KEY=signing_key,
        MAX_CONTENT_LENGTH=96 * 1024,
        SESSION_COOKIE_NAME="creator_studio_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    )
    passcode_hash = hashlib.sha256(passcode.encode()).digest()

    @app.before_request
    def enforce_local_origin():
        host = urlsplit(request.host_url).hostname
        try:
            loopback = ipaddress.ip_address(request.remote_addr or "").is_loopback
        except ValueError:
            loopback = False
        if host not in {"localhost", "127.0.0.1", "::1"} or not loopback:
            abort(403)
        if request.method in {"POST", "PATCH", "PUT", "DELETE"}:
            origin = request.headers.get("Origin")
            if origin and origin.rstrip("/") != request.host_url.rstrip("/"):
                abort(403)
            if request.headers.get("Sec-Fetch-Site") in {"cross-site", "same-site"}:
                abort(403)

    @app.after_request
    def protect_response(response):
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def request_error(error):
        return jsonify(error="Request rejected", code=error.code), error.code

    def authenticated():
        if not session.get("owner"):
            return False
        return True

    def require_owner(write=False):
        if not authenticated():
            abort(401)
        if write:
            token = request.headers.get("X-Studio-CSRF", "")
            if not token or not hmac.compare_digest(token, session.get("csrf", "")):
                abort(403)

    @app.errorhandler(401)
    def login_required(error):
        return jsonify(error="Sign in to the private Studio", code=401), 401

    @app.errorhandler(ValueError)
    def invalid_input(error):
        return jsonify(error=str(error), code=422), 422

    def json_body():
        if not request.is_json:
            abort(400)
        value = loads_strict(request.get_data(as_text=True))
        if not isinstance(value, dict):
            abort(400)
        validate_json_value(value)
        return value

    @app.route("/api/session", methods=["GET", "POST", "DELETE"])
    def owner_session():
        if request.method == "POST":
            data = json_body()
            if set(data) != {"passcode"} or not isinstance(data["passcode"], str):
                abort(400)
            supplied = hashlib.sha256(data["passcode"].encode()).digest()
            if not hmac.compare_digest(supplied, passcode_hash):
                return jsonify(error="That access code is not right", code=401), 401
            session.clear()
            session.update(owner=True, csrf=secrets.token_hex(24))
            session.permanent = True
        elif request.method == "DELETE":
            require_owner(write=True)
            session.clear()
        return jsonify(authenticated=authenticated(), csrf_token=session.get("csrf") if authenticated() else None)

    @app.get("/api/state")
    def get_state():
        require_owner()
        try:
            return jsonify(Store(backend="local", local_path=state_path).export_snapshot())
        except SchemaError:
            return jsonify(error="The private state needs recovery. No records were replaced.", code=503), 503

    def revision_response(store, collection, record_id, message="This record changed in another session"):
        current = store.get(collection, record_id) or {}
        deleted = store.export_snapshot().get("_deleted_revisions", {}).get(collection, {}).get(record_id, 0)
        return jsonify(error=message, code=409, current=current, deleted_revision=deleted), 409

    @app.patch("/api/records/<collection>/<record_id>")
    def patch_record(collection, record_id):
        require_owner(write=True)
        if collection not in FIELDS or not ID.fullmatch(record_id):
            abort(404)
        try:
            data = json_body()
            if set(data) != {"expected_revision", "fields"}:
                raise ValueError("Expected expected_revision and fields")
            expected, fields = data["expected_revision"], data["fields"]
            if type(expected) is not int or expected < 0 or not isinstance(fields, dict) or not fields:
                raise ValueError("A nonnegative revision and nonempty fields object are required")
            if set(fields) - FIELDS[collection] or set(fields) & RESERVED:
                raise ValueError("Unexpected or protected record fields")
            validate_fields(collection, fields)
            store = Store(backend="local", local_path=state_path)
            previous = store.get(collection, record_id) or {}
            deleted = store.export_snapshot().get("_deleted_revisions", {}).get(collection, {}).get(record_id, 0)
            if previous.get("_revision", deleted) != expected:
                return revision_response(store, collection, record_id)
            if collection == "drafts" and not previous:
                fields = {"status": "draft", **fields}
            if collection == "drafts":
                fields = guard_draft(store, record_id, previous, fields)
            draft_revisions = {draft_id: draft.get("_revision", 0) for draft_id, draft in store.all("drafts").items()}
            updated = store.patch_if_revision(collection, record_id, fields, expected)
            def validate_latest(snapshot):
                # Recheck against the merged state under the repository's write lock.
                # Two owners scheduling different records cannot reserve one instant.
                if collection != "drafts" or updated.get("status") != "scheduled" or "scheduled_for" not in fields and fields.get("status") != "scheduled":
                    return
                when = scheduled_time(updated.get("scheduled_for"))
                if when <= datetime.now(timezone.utc):
                    raise ValueError("Choose a future schedule with an explicit timezone")
                for other_id, other in snapshot["drafts"].items():
                    if other_id == record_id or other.get("status") != "scheduled":
                        continue
                    try:
                        occupied = scheduled_time(other.get("scheduled_for"))
                    except ValueError:
                        continue
                    if occupied == when:
                        raise ValueError("That scheduling slot is occupied")
            store.flush(validator=validate_latest)
            related = {draft_id: draft for draft_id, draft in store.all("drafts").items()
                       if collection == "sources" and draft.get("candidate_id", draft_id) == record_id
                       and draft.get("_revision", 0) != draft_revisions.get(draft_id, 0)}
            return jsonify(record=store.get(collection, record_id), related_drafts=related)
        except RevisionConflict as conflict:
            latest = Store(backend="local", local_path=state_path)
            message = "Source evidence changed. Review the current source before retrying this edit." if conflict.coll == "sources" and collection != "sources" else "This record changed in another session"
            return revision_response(latest, collection, record_id, message)
        except (ValueError, TypeError) as error:
            return jsonify(error=str(error), code=422), 422

    def guard_draft(store, record_id, previous, fields):
        proposed = dict(previous, **fields)
        status = fields.get("status", previous.get("status", "draft"))
        known = {"draft", "approved", "scheduled", "published", "rejected"}
        if status not in known:
            raise ValueError("Unsupported editorial status")
        old_status = previous.get("status", "draft")
        transitions = {
            "draft": {"draft", "approved", "rejected"},
            "approved": {"approved", "draft", "scheduled", "published", "rejected"},
            "scheduled": {"scheduled", "approved", "draft", "published", "rejected"},
            "published": {"published"},
            "rejected": {"rejected", "draft"},
        }
        if status not in transitions.get(old_status, {"draft"}):
            raise ValueError("Return the draft to review before changing its editorial state")
        changed = bool(previous) and content_fingerprint(previous) != content_fingerprint(proposed)
        if status == "approved" and fields.get("status") == "approved":
            # An authenticated owner request is a manual approval, never publishing authority.
            if changed:
                raise ValueError("Save the edited draft before approving its current revision")
            post = proposed.get("edited_post") if proposed.get("edited_post") is not None else proposed.get("post", "")
            if not isinstance(post, str) or not post.strip():
                raise ValueError("Write a post before approval")
            pack = store.get("sources", proposed.get("candidate_id", record_id)) or {}
            if pack and proposed.get("evidence_revision") != pack.get("_revision", 0):
                raise ValueError("Save the draft with its current source revision before approval")
            if not pack.get("excerpt") and not proposed.get("facts"):
                raise ValueError("Add source text or story-scoped facts before approval")
            checks = verify.checks(post, dict(pack, excerpt=pack.get("excerpt") or proposed.get("facts", "")), hashtags=proposed.get("hashtags", []))
            if checks["verdict"] == "fail":
                raise ValueError("Resolve blocking checks before approval: " + "; ".join(issue["msg"] for issue in checks["issues"] if issue["level"] == "fail")[:500])
            fields = dict(fields, approval={
                "revision": previous.get("revision", 1), "content_hash": content_fingerprint(proposed),
                "approved_at": now_iso(), "kind": "owner_manual", "verification_state": "deterministic_screen",
            })
        elif (fields.get("status") in {"scheduled", "published"}
              or status == "scheduled" and "scheduled_for" in fields and not changed):
            if changed or not approval_matches(previous):
                raise ValueError("Review and approve the current content revision first")
            if status == "scheduled":
                when = scheduled_time(proposed.get("scheduled_for"))
                if when <= datetime.now(timezone.utc):
                    raise ValueError("Choose a future schedule with an explicit timezone")
                for other_id, other in store.all("drafts").items():
                    if other_id != record_id and other.get("status") == "scheduled":
                        try:
                            occupied = scheduled_time(other.get("scheduled_for"))
                        except ValueError:
                            continue  # Preserve imported history; it cannot occupy a valid slot.
                        if occupied == when:
                            raise ValueError("That scheduling slot is occupied")
            elif old_status != "published":
                fields = dict(fields, published_at=now_iso(), publication_confirmation="owner_manual")
        if status == "draft" and fields.get("status") == "draft":
            fields = dict(fields, approval=None)
        return fields

    @app.get("/")
    def home():
        return redirect("/studio.html")

    @app.get("/studio.html")
    def studio_page():
        file = docs_dir / "studio.html"
        if not file.is_file():
            return "Build the Studio with python generate_studio.py first.", 503
        html = file.read_text(encoding="utf-8")
        def inject(match):
            data = json.loads(match.group(1))
            data.update(privateApi="/api", lockHash="", fbUrl="")
            return "window.STUDIO_DATA = " + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + ";"
        html, count = re.subn(r"window\.STUDIO_DATA = ([^\n]*);", inject, html, count=1)
        if count != 1:
            return "Rebuild the Studio before using private mode.", 503
        return app.response_class(html, mimetype="text/html")

    @app.get("/<path:asset>")
    def public_asset(asset):
        if asset not in {"favicon.svg", "pulse.json", "digests/latest.html", "digests/latest.md"}:
            abort(404)
        return send_from_directory(docs_dir, asset)

    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--state", help="Private state file outside public docs")
    args = parser.parse_args()
    try:
        app = create_app(state_path=args.state)
    except (ValueError, SchemaError) as error:
        parser.error(str(error))
    app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
