"""Explicit file-only migration into private Studio state; dry-run by default.

python migrate_studio_state.py --source docs/pipeline.json
python migrate_studio_state.py --source docs/pipeline.json --apply

No Firebase requests are made. Public source files remain in place unless the
operator also supplies --remove-source. Backups live beside the private target.
"""

import argparse
import copy
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone

from agents.store import (COLLECTIONS, ROOT, SchemaError,
                          assert_private_path, default_local_path, normalize_snapshot, now_iso,
                          read_snapshot, snapshot_lock, write_snapshot)
from creator.contracts import loads_strict


class MigrationConflict(ValueError):
    """A source record collides with different private data."""


class MigrationFailure(RuntimeError):
    """Migration stopped after backups; retain concrete recovery instructions."""

    def __init__(self, error, report):
        self.report = report
        super().__init__(f"Migration stopped: {error}. See backup paths and rollback instructions in the report.")


def _counts(snapshot):
    return {coll: len(snapshot[coll]) for coll in COLLECTIONS}


def _merge(source, target):
    merged = copy.deepcopy(target)
    added = {coll: 0 for coll in COLLECTIONS}
    conflicts = []
    for coll in COLLECTIONS:
        for record_id, document in source[coll].items():
            if record_id in target.get("_deleted_revisions", {}).get(coll, {}):
                conflicts.append(f"{coll}/{record_id} (deleted in private state)")
            elif record_id in target[coll]:
                if target[coll][record_id] != document:
                    conflicts.append(f"{coll}/{record_id}")
            else:
                merged[coll][record_id] = copy.deepcopy(document)
                added[coll] += 1
    for coll, records in source.get("_deleted_revisions", {}).items():
        for record_id, revision in records.items():
            current = target.get("_deleted_revisions", {}).get(coll, {}).get(record_id)
            if record_id in target[coll] or (current is not None and current != revision):
                conflicts.append(f"{coll}/{record_id} (deletion revision conflict)")
            elif current is None:
                merged.setdefault("_deleted_revisions", {}).setdefault(coll, {})[record_id] = revision
    if conflicts:
        raise MigrationConflict("Migration aborted; conflicting records: " + ", ".join(conflicts))
    return merged, added


def _read_source(path):
    with open(path, "rb") as f:
        original = f.read()
    try:
        snapshot = normalize_snapshot(loads_strict(original.decode("utf-8")))
    except (UnicodeError, ValueError) as exc:
        raise SchemaError(f"Cannot migrate Studio source {path}: {exc}") from exc
    return original, snapshot


def _backup(directory, label, payload):
    os.makedirs(directory, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(directory, f"{label}-{stamp}-{uuid.uuid4().hex[:8]}.json.bak")
    assert_private_path(path)
    with open(path, "xb") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    return path


def migrate(source, target=None, *, apply=False, remove_source=False):
    """Inspect or migrate a file while preserving IDs and unrelated target records."""
    source = os.path.realpath(os.path.abspath(os.fspath(source)))
    target = assert_private_path(os.fspath(target if target is not None else default_local_path()))
    if os.path.normcase(source) == os.path.normcase(target):
        raise ValueError("Source and target must be different files")
    if remove_source and not apply:
        raise ValueError("--remove-source requires --apply")
    original, source_snapshot = _read_source(source)
    target_snapshot = read_snapshot(target)
    merged, added = _merge(source_snapshot, target_snapshot)
    report = {
        "mode": "apply" if apply else "dry-run",
        "source": source, "target": target,
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "source_counts": _counts(source_snapshot),
        "target_counts_before": _counts(target_snapshot),
        "target_counts_after": _counts(merged), "records_to_import": added,
        "source_deletion_counts": {coll: len(source_snapshot.get("_deleted_revisions", {}).get(coll, {}))
                                   for coll in COLLECTIONS},
        "source_ids_preserved": True, "source_removed": False,
        "changed": False, "backups": {},
        "rollback": [],
    }
    if not apply:
        return report
    with snapshot_lock(target):
        current_source, source_snapshot = _read_source(source)
        if current_source != original:
            raise MigrationConflict("Source changed during inspection; rerun the migration")
        target_existed = os.path.exists(target)
        target_snapshot = read_snapshot(target)
        merged, added = _merge(source_snapshot, target_snapshot)
        report.update(target_counts_before=_counts(target_snapshot),
                      target_counts_after=_counts(merged), records_to_import=added)
        changed = (any(added.values()) or not target_existed
                   or merged.get("_deleted_revisions", {}) != target_snapshot.get("_deleted_revisions", {}))
        if changed or remove_source:
            backups = os.path.join(os.path.dirname(target), "backups")
            source_backup = _backup(backups, "source", original)
            report["backups"]["source"] = source_backup
            report["rollback"].append(f"Restore the source by copying {source_backup} to {source}.")
            if target_existed:
                with open(target, "rb") as f:
                    target_original = f.read()
                target_backup = _backup(backups, "target", target_original)
                report["backups"]["target"] = target_backup
                report["rollback"].append(f"Stop Studio and copy {target_backup} to {target}.")
            else:
                report["rollback"].append(f"Stop Studio and remove the newly created target {target}.")
        try:
            if changed:
                merged["updated"] = now_iso()
                write_snapshot(target, merged)
                persisted = read_snapshot(target)
                for coll in COLLECTIONS:
                    for record_id, document in source_snapshot[coll].items():
                        if persisted[coll].get(record_id) != document:
                            raise MigrationConflict(f"Verification failed for {coll}/{record_id}; "
                                                    "restore the target backup before continuing")
                if _counts(persisted) != _counts(merged):
                    raise MigrationConflict("Migration count verification failed; restore the target backup")
                for coll, records in source_snapshot.get("_deleted_revisions", {}).items():
                    for record_id, revision in records.items():
                        if persisted.get("_deleted_revisions", {}).get(coll, {}).get(record_id) != revision:
                            raise MigrationConflict("Migration deletion revision verification failed; restore the target backup")
                report["changed"] = True
            if remove_source:
                with open(source, "rb") as f:
                    if f.read() != original:
                        raise MigrationConflict("Source changed after migration; it has not been removed")
                os.unlink(source)
                report["source_removed"] = True
        except (OSError, ValueError) as exc:
            raise MigrationFailure(exc, report) from exc
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=os.path.join(ROOT, "docs", "pipeline.json"))
    parser.add_argument("--target", default=default_local_path())
    parser.add_argument("--apply", action="store_true", help="Write the inspected migration with private backups")
    parser.add_argument("--remove-source", action="store_true", help="Explicitly remove the source after verified migration")
    args = parser.parse_args(argv)
    try:
        report = migrate(args.source, args.target, apply=args.apply, remove_source=args.remove_source)
    except MigrationFailure as exc:
        print(str(exc), file=sys.stderr)
        print(json.dumps(exc.report, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    except (OSError, ValueError, TimeoutError) as exc:
        print(f"Migration failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not args.apply:
        print("Dry-run only; no files changed. Use --apply to create private state and backups.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
