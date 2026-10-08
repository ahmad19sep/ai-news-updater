"""Private persistence and migration tests; all state lives in temporary files."""

import json
import io
import os
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

from agents import store
from creator.contracts import approval_matches, content_fingerprint
from migrate_studio_state import MigrationConflict, MigrationFailure, main as migration_main, migrate


class PrivateStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.path = self.directory / "private" / "pipeline.json"

    def make_store(self):
        return store.Store(backend="local", local_path=self.path, fb_url="", key="test")

    def write_raw(self, value):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(value), encoding="utf-8")

    def test_new_draft_cannot_commit_against_source_changed_after_its_read(self):
        initial = self.make_store()
        initial.put("sources", "story", {"excerpt": "Original evidence"})
        initial.flush()
        writer, retrieval = self.make_store(), self.make_store()
        writer.put("drafts", "new_draft", {"candidate_id": "story", "post": "Owner text", "status": "draft"})
        draft = writer.get("drafts", "new_draft")
        writer.patch("drafts", "new_draft", status="approved", approval={"revision": draft["revision"], "content_hash": content_fingerprint(draft)})
        retrieval.patch("sources", "story", excerpt="New evidence")
        retrieval.flush()
        with self.assertRaises(store.RevisionConflict) as conflict:
            writer.flush()
        self.assertEqual(conflict.exception.coll, "sources")
        self.assertEqual(writer.get("drafts", "new_draft")["evidence_revision"], 1)
        self.assertTrue(writer._dirty)
        self.assertIsNone(self.make_store().get("drafts", "new_draft"))
        self.assertEqual(self.make_store().get("sources", "story")["excerpt"], "New evidence")

    def test_changing_source_association_binds_new_source_revision(self):
        state = self.make_store()
        state.put("sources", "first", {"excerpt": "First source"})
        state.put("sources", "second", {"excerpt": "Second source"})
        state.patch("sources", "second", excerpt="Updated second source")
        state.put("drafts", "draft", {"candidate_id": "first", "post": "Owner text", "status": "draft"})
        draft = state.get("drafts", "draft")
        state.patch("drafts", "draft", status="approved", approval={"revision": draft["revision"], "content_hash": content_fingerprint(draft)})
        state.flush()
        state.patch("drafts", "draft", candidate_id="second")
        state.flush()
        changed = self.make_store().get("drafts", "draft")
        self.assertEqual(changed["evidence_revision"], 2)
        self.assertEqual(changed["status"], "draft")
        self.assertIsNone(changed["approval"])

    def test_private_default_does_not_load_public_state(self):
        self.assertEqual(Path(store.LOCAL_PATH).parent.name, ".studio-private")
        public = self.directory / "docs"
        public.mkdir()
        (public / "pipeline.json").write_text('{"drafts":{"secret":{"post":"private"}}}', encoding="utf-8")
        with mock.patch.object(store, "LOCAL_PATH", str(self.path)), mock.patch.object(store, "PUBLIC_PATH", str(public)), mock.patch.dict(os.environ, {"STUDIO_STATE_PATH": ""}):
            private = store.Store(backend="local", fb_url="", key="test")
        self.assertEqual(private.all("drafts"), {})
        self.assertFalse(self.path.exists())

    def test_state_path_override_is_dynamic_and_explicit_path_wins(self):
        override = self.directory / "override" / "state.json"
        with mock.patch.dict(os.environ, {"STUDIO_STATE_PATH": str(override)}):
            state = store.Store(backend="local", fb_url="", key="test")
            self.assertEqual(Path(state.local_path), override)
            self.assertEqual(Path(self.make_store().local_path), self.path)
            state.put("settings", "owner", {"name": "Private owner"})
            state.flush()
        self.assertTrue(override.exists())
        self.assertFalse(self.path.exists())
        with mock.patch.object(store, "LOCAL_PATH", str(self.path)), mock.patch.dict(os.environ, {"STUDIO_STATE_PATH": "  "}):
            self.assertEqual(store.default_local_path(), str(self.path))

    def test_environment_override_does_not_bypass_public_write_guard(self):
        public = self.directory / "docs"
        destination = public / "pipeline.json"
        with mock.patch.object(store, "PUBLIC_PATH", str(public)), mock.patch.dict(os.environ, {"STUDIO_STATE_PATH": str(destination)}):
            state = store.Store(backend="local", fb_url="", key="test")
            state.put("settings", "owner", {"name": "Private owner"})
            with self.assertRaises(store.PublicStatePathError):
                state.flush()
        self.assertFalse(public.exists())

    def test_export_is_independent_and_legacy_revision_is_zero(self):
        self.write_raw({"candidates": {"original-id": {"title": "Story"}}, "custom_metadata": "keep"})
        state = self.make_store()
        self.assertEqual(state.get("candidates", "original-id")["_revision"], 0)
        snapshot = state.export_snapshot()
        self.assertEqual(snapshot["schema_version"], store.SCHEMA_VERSION)
        self.assertEqual(snapshot["custom_metadata"], "keep")
        snapshot["candidates"]["original-id"]["title"] = "Mutated copy"
        self.assertEqual(state.get("candidates", "original-id")["title"], "Story")
        state.patch_if_revision("candidates", "original-id", {"status": "shortlisted"}, 0)
        state.flush()
        self.assertEqual(self.make_store().get("candidates", "original-id")["_revision"], 1)

    def test_corruption_is_reported_without_wiping_original(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text('{"drafts":', encoding="utf-8")
        original = self.path.read_bytes()
        with self.assertRaises(store.SchemaError):
            self.make_store()
        self.assertEqual(self.path.read_bytes(), original)

    def test_unsafe_keys_duplicates_and_nonfinite_json_are_rejected(self):
        self.path.parent.mkdir(parents=True)
        for raw in ('{"drafts": {}, "drafts": {}}',
                    '{"settings":{"x":{"nested":{"__proto__":{}}}}}',
                    '{"candidates":{"x":{"score":NaN}}}',
                    '{"candidates":{"x":{"score":Infinity}}}'):
            with self.subTest(raw=raw):
                self.path.write_text(raw, encoding="utf-8")
                original = self.path.read_bytes()
                with self.assertRaises(store.SchemaError):
                    self.make_store()
                self.assertEqual(self.path.read_bytes(), original)

    def test_schema_rejects_invalid_collections_records_and_versions(self):
        cases = [[], {"drafts": []}, {"schema_version": 99}, {"schema_version": True},
                 {"updated": 7}, {"drafts": {"x": "broken"}},
                 {"candidates": {"x": {"id": "different"}}},
                 {"candidates": {"x": {"_revision": -1}}},
                 {"candidates": {"x": {"_revision": True}}}]
        for value in cases:
            with self.subTest(value=value):
                self.write_raw(value)
                with self.assertRaises(store.SchemaError):
                    self.make_store()

    def test_public_snapshot_readable_but_not_writable(self):
        public = self.directory / "docs"
        public.mkdir()
        path = public / "pipeline.json"
        path.write_text('{"candidates":{"x":{"title":"Keep"}}}', encoding="utf-8")
        original = path.read_bytes()
        with mock.patch.object(store, "PUBLIC_PATH", str(public)):
            state = store.Store(backend="local", local_path=path, fb_url="", key="test")
            state.patch("candidates", "x", title="Private edit")
            with self.assertRaises(store.PublicStatePathError):
                state.flush()
        self.assertEqual(path.read_bytes(), original)
        self.assertFalse(Path(str(path) + ".lock").exists())
        self.assertEqual(state.get("candidates", "x")["title"], "Private edit")

    def test_public_guard_resolves_symlinks(self):
        public = self.directory / "docs"
        public.mkdir()
        alias = self.directory / "alias"
        try:
            alias.symlink_to(public, target_is_directory=True)
        except OSError:
            self.skipTest("Symlinks are unavailable for this account")
        with mock.patch.object(store, "PUBLIC_PATH", str(public)):
            with self.assertRaises(store.PublicStatePathError):
                store.assert_private_path(alias / "pipeline.json")

    def test_unrelated_stale_writers_merge_without_losing_records(self):
        first, second = self.make_store(), self.make_store()
        first.put("candidates", "first", {"title": "One"})
        second.put("candidates", "second", {"title": "Two"})
        first.flush()
        second.flush()
        self.assertEqual(set(self.make_store().all("candidates")), {"first", "second"})
        self.assertIn("first", second.all("candidates"))

    def test_stale_conflict_preserves_every_pending_edit(self):
        initial = self.make_store()
        initial.put("candidates", "same", {"title": "Initial"})
        initial.flush()
        winner, stale = self.make_store(), self.make_store()
        winner.patch_if_revision("candidates", "same", {"title": "Winner"}, 1)
        stale.patch_if_revision("candidates", "same", {"title": "Pending"}, 1)
        stale.put("sources", "independent", {"excerpt": "Pending source"})
        winner.flush()
        with self.assertRaises(store.RevisionConflict) as conflict:
            stale.flush()
        self.assertEqual(conflict.exception.actual_revision, 2)
        self.assertEqual(stale.get("candidates", "same")["title"], "Pending")
        self.assertEqual(len(stale._dirty), 2)
        persisted = self.make_store()
        self.assertEqual(persisted.get("candidates", "same")["title"], "Winner")
        self.assertIsNone(persisted.get("sources", "independent"))

    def test_conditional_patch_rejects_stale_and_reserved_fields(self):
        state = self.make_store()
        state.patch_if_revision("settings", "owner", {"name": "One"}, 0)
        with self.assertRaises(store.RevisionConflict):
            state.patch_if_revision("settings", "owner", {"name": "Two"}, 0)
        for fields in ({"_revision": 100}, {"id": "x"}, {"revision": 2}, {"updated": "x"}):
            with self.assertRaises(ValueError):
                state.patch_if_revision("settings", "owner", fields, 1)
        self.assertEqual(state.get("settings", "owner")["name"], "One")

    def test_legacy_change_and_delete_are_detected_even_at_revision_zero(self):
        self.write_raw({"candidates": {"old-id": {"title": "Original"}}})
        stale = self.make_store()
        stale.patch_if_revision("candidates", "old-id", {"title": "Pending"}, 0)
        self.write_raw({"candidates": {"old-id": {"title": "Outside edit"}}})
        with self.assertRaises(store.RevisionConflict):
            stale.flush()
        self.write_raw({"candidates": {}})
        with self.assertRaises(store.RevisionConflict):
            stale.flush()

    def test_deletion_conflicts_with_concurrent_update(self):
        state = self.make_store()
        state.put("candidates", "x", {"title": "Original"})
        state.flush()
        deleting, updating = self.make_store(), self.make_store()
        deleting.delete("candidates", "x")
        updating.patch("candidates", "x", title="Keep newer")
        updating.flush()
        with self.assertRaises(store.RevisionConflict):
            deleting.flush()
        self.assertEqual(self.make_store().get("candidates", "x")["title"], "Keep newer")

    def test_recreated_id_continues_revision_and_rejects_old_client(self):
        state = self.make_store()
        state.put("candidates", "x", {"title": "Original"})
        state.flush()
        state.delete("candidates", "x")
        state.flush()
        with self.assertRaises(store.RevisionConflict):
            state.patch_if_revision("candidates", "x", {"title": "Accidental recreation"}, 0)
        state.patch_if_revision("candidates", "x", {"title": "Recreated"}, 2)
        state.flush()
        self.assertEqual(state.get("candidates", "x")["_revision"], 3)
        with self.assertRaises(store.RevisionConflict):
            self.make_store().patch_if_revision("candidates", "x", {"title": "Old client"}, 1)

    def test_create_delete_cycle_conflicts_with_stale_absent_snapshot(self):
        stale, current = self.make_store(), self.make_store()
        stale.patch_if_revision("candidates", "x", {"title": "Pending"}, 0)
        current.put("candidates", "x", {"title": "Temporary"})
        current.flush()
        current.delete("candidates", "x")
        current.flush()
        with self.assertRaises(store.RevisionConflict):
            stale.flush()
        self.assertIsNone(self.make_store().get("candidates", "x"))

    def test_pending_deletion_and_recreation_export_consistent_metadata(self):
        state = self.make_store()
        state.put("candidates", "x", {"title": "First"})
        state.delete("candidates", "x")
        snapshot = store.normalize_snapshot(state.export_snapshot())
        self.assertEqual(snapshot["_deleted_revisions"]["candidates"]["x"], 2)
        state.put("candidates", "x", {"title": "Recreated"})
        snapshot = store.normalize_snapshot(state.export_snapshot())
        self.assertEqual(snapshot["candidates"]["x"]["_revision"], 3)
        self.assertNotIn("x", snapshot.get("_deleted_revisions", {}).get("candidates", {}))

    def test_atomic_write_failure_retains_original_and_pending_changes(self):
        state = self.make_store()
        state.put("candidates", "x", {"title": "Original"})
        state.flush()
        original = self.path.read_bytes()
        state.patch("candidates", "x", title="Pending")
        with mock.patch("agents.store.os.replace", side_effect=OSError("simulated failure")):
            with self.assertRaises(OSError):
                state.flush()
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(len(state._dirty), 1)
        self.assertEqual(list(self.path.parent.glob(".pipeline-*.tmp")), [])

    def test_parallel_writers_are_serialized_and_same_record_has_one_winner(self):
        barrier = threading.Barrier(2)
        def write(record_id, title):
            state = self.make_store()
            state.put("candidates", record_id, {"title": title})
            barrier.wait(timeout=5)
            try:
                state.flush()
                return "saved"
            except store.RevisionConflict:
                return "conflict"
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda title: write("shared", title), ("One", "Two")))
        self.assertCountEqual(results, ["saved", "conflict"])
        self.assertEqual(self.make_store().get("candidates", "shared")["_revision"], 1)

    def test_validator_checks_merged_snapshot_under_lock_for_schedule_collision(self):
        state = self.make_store()
        for record_id in ("a", "b"):
            state.put("drafts", record_id, {"post": "Owner draft", "status": "draft"})
        state.flush()
        first, second = self.make_store(), self.make_store()
        when = "2026-10-12T09:00:00+05:00"
        first.patch("drafts", "a", status="scheduled", scheduled_for=when)
        second.patch("drafts", "b", status="scheduled", scheduled_for=when)
        def unique_slots(snapshot):
            used = set()
            for draft in snapshot["drafts"].values():
                if draft.get("status") == "scheduled":
                    slot = draft["scheduled_for"]
                    if slot in used:
                        raise ValueError("Scheduling slot is occupied")
                    used.add(slot)
        first.flush(validator=unique_slots)
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "occupied"):
            second.flush(validator=unique_slots)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(second.get("drafts", "b")["status"], "scheduled")
        self.assertIn(("drafts", "b"), second._dirty)
        self.assertEqual(self.make_store().get("drafts", "b")["status"], "draft")

    def test_content_revision_and_approval_survive_status_changes_only(self):
        state = self.make_store()
        state.put("drafts", "draft-id", {"post": "Reviewed body", "status": "draft"})
        draft = state.get("drafts", "draft-id")
        approval = {"revision": draft["revision"], "content_hash": content_fingerprint(draft),
                    "approved_at": "2026-10-08T10:00:00+00:00"}
        approved = state.patch("drafts", "draft-id", status="approved", approval=approval)
        self.assertTrue(approval_matches(approved))
        scheduled = state.patch("drafts", "draft-id", status="scheduled", scheduled_for="2026-10-09T10:00:00Z")
        self.assertEqual(scheduled["revision"], 1)
        self.assertTrue(approval_matches(scheduled))
        edited = state.patch("drafts", "draft-id", edited_post="A different body")
        self.assertEqual(edited["revision"], 2)
        self.assertEqual(edited["status"], "draft")
        self.assertIsNone(edited["approval"])
        self.assertFalse(approval_matches(edited))

    def approve_draft(self, state, record_id):
        draft = state.get("drafts", record_id)
        approval = {"revision": draft["revision"], "content_hash": content_fingerprint(draft),
                    "approved_at": "2026-10-08T10:00:00+00:00"}
        state.patch("drafts", record_id, status="approved", approval=approval)

    def test_direct_source_put_invalidates_linked_approval_atomically(self):
        state = self.make_store()
        state.put("sources", "story", {"excerpt": "Original source"})
        state.put("drafts", "variant", {"candidate_id": "story", "post": "Reviewed body", "status": "draft"})
        self.approve_draft(state, "variant")
        state.flush()
        source = state.put("sources", "story", {"excerpt": "Updated source"})
        draft = state.get("drafts", "variant")
        self.assertEqual(draft["evidence_revision"], source["_revision"])
        self.assertEqual(draft["status"], "draft")
        self.assertEqual(draft["revision"], 2)
        self.assertFalse(approval_matches(draft))
        self.assertEqual(state.flush(), 2)
        persisted = self.make_store()
        self.assertEqual(persisted.get("sources", "story")["excerpt"], "Updated source")
        self.assertFalse(approval_matches(persisted.get("drafts", "variant")))

    def test_source_cascade_conflict_keeps_both_source_and_draft_pending(self):
        state = self.make_store()
        state.put("sources", "story", {"excerpt": "Original source"})
        state.put("drafts", "variant", {"candidate_id": "story", "post": "Reviewed body", "status": "draft"})
        self.approve_draft(state, "variant")
        state.flush()
        source_writer, other = self.make_store(), self.make_store()
        source_writer.put("sources", "story", {"excerpt": "Pending source"})
        other.patch("drafts", "variant", rating=5)
        other.flush()
        with self.assertRaises(store.RevisionConflict):
            source_writer.flush()
        self.assertEqual(set(source_writer._dirty), {("sources", "story"), ("drafts", "variant")})
        self.assertFalse(approval_matches(source_writer.get("drafts", "variant")))
        self.assertEqual(source_writer.get("sources", "story")["excerpt"], "Pending source")
        persisted = self.make_store()
        self.assertEqual(persisted.get("sources", "story")["excerpt"], "Original source")
        self.assertTrue(approval_matches(persisted.get("drafts", "variant")))

    def test_source_flush_invalidates_linked_draft_created_after_load(self):
        state = self.make_store()
        state.put("sources", "story", {"excerpt": "Original source"})
        state.flush()
        source_writer, creator = self.make_store(), self.make_store()
        source_writer.put("sources", "story", {"excerpt": "Updated source"})
        creator.put("drafts", "variant", {"candidate_id": "story", "post": "Latest owner body", "status": "draft"})
        self.approve_draft(creator, "variant")
        creator.flush()
        self.assertEqual(source_writer.flush(), 2)
        draft = self.make_store().get("drafts", "variant")
        self.assertEqual(draft["post"], "Latest owner body")
        self.assertEqual(draft["evidence_revision"], 2)
        self.assertEqual(draft["status"], "draft")
        self.assertFalse(approval_matches(draft))

    def test_deleted_source_invalidates_approval_and_preserves_published_history(self):
        state = self.make_store()
        state.put("sources", "story", {"excerpt": "Original source"})
        state.put("drafts", "variant", {"candidate_id": "story", "post": "Reviewed body", "status": "draft"})
        self.approve_draft(state, "variant")
        published_at = "2026-10-08T09:00:00+00:00"
        state.put("drafts", "history", {"candidate_id": "story", "post": "Published hook", "status": "published", "published_at": published_at})
        state.flush()
        state.delete("sources", "story")
        self.assertEqual(state.flush(), 3)
        persisted = self.make_store()
        self.assertIsNone(persisted.get("sources", "story"))
        self.assertEqual(persisted.export_snapshot()["_deleted_revisions"]["sources"]["story"], 2)
        draft = persisted.get("drafts", "variant")
        self.assertEqual(draft["status"], "draft")
        self.assertEqual(draft["evidence_revision"], 2)
        self.assertFalse(approval_matches(draft))
        history = persisted.get("drafts", "history")
        self.assertEqual(history["status"], "published")
        self.assertEqual(history["published_at"], published_at)
        self.assertEqual(persisted.published_history()[0]["hook"], "Published hook")

    def test_source_deletion_invalidates_linked_draft_created_after_load(self):
        state = self.make_store()
        state.put("sources", "story", {"excerpt": "Original source"})
        state.flush()
        deleting, creator = self.make_store(), self.make_store()
        deleting.delete("sources", "story")
        creator.put("drafts", "variant", {"candidate_id": "story", "post": "Latest owner body", "status": "draft"})
        self.approve_draft(creator, "variant")
        creator.flush()
        self.assertEqual(deleting.flush(), 2)
        persisted = self.make_store()
        self.assertIsNone(persisted.get("sources", "story"))
        draft = persisted.get("drafts", "variant")
        self.assertEqual(draft["post"], "Latest owner body")
        self.assertEqual(draft["evidence_revision"], 2)
        self.assertEqual(draft["status"], "draft")
        self.assertFalse(approval_matches(draft))


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / "legacy.json"
        self.target = self.directory / "private" / "pipeline.json"
        self.legacy = {"candidates": {"candidate-original": {"title": "Story"}},
                       "sources": {"source-original": {"excerpt": "Evidence"}},
                       "drafts": {"draft-original": {"post": "Private draft", "status": "draft"}},
                       "settings": {"preferences": {"tone": "plain"}},
                       "runs": {"run-original": {"result": "ok"}}}
        self.source.write_text(json.dumps(self.legacy), encoding="utf-8")

    def test_dry_run_has_counts_ids_and_no_filesystem_writes(self):
        before = self.source.read_bytes()
        report = migrate(self.source, self.target)
        self.assertEqual(report["mode"], "dry-run")
        self.assertTrue(report["source_ids_preserved"])
        self.assertEqual(report["source_counts"], dict.fromkeys(store.COLLECTIONS, 1))
        self.assertEqual(report["records_to_import"], dict.fromkeys(store.COLLECTIONS, 1))
        self.assertFalse(self.target.parent.exists())
        self.assertEqual(self.source.read_bytes(), before)

    def test_migration_default_and_cli_share_env_override_and_explicit_target_wins(self):
        override = self.directory / "override" / "state.json"
        with mock.patch.dict(os.environ, {"STUDIO_STATE_PATH": str(override)}):
            report = migrate(self.source)
            self.assertEqual(Path(report["target"]), override)
            explicit = migrate(self.source, self.target)
            self.assertEqual(Path(explicit["target"]), self.target)
            output = io.StringIO()
            with mock.patch("sys.stdout", output):
                self.assertEqual(migration_main(["--source", str(self.source)]), 0)
            printed, _ = json.JSONDecoder().raw_decode(output.getvalue())
            self.assertEqual(Path(printed["target"]), override)
            with mock.patch("sys.stdout", io.StringIO()) as output:
                self.assertEqual(migration_main(["--source", str(self.source), "--target", str(self.target)]), 0)
                printed, _ = json.JSONDecoder().raw_decode(output.getvalue())
                self.assertEqual(Path(printed["target"]), self.target)
        self.assertFalse(override.parent.exists())
        self.assertFalse(self.target.parent.exists())

    def test_migration_environment_override_keeps_public_target_guard(self):
        public = self.directory / "docs"
        with mock.patch.object(store, "PUBLIC_PATH", str(public)), mock.patch.dict(os.environ, {"STUDIO_STATE_PATH": str(public / "pipeline.json")}):
            with self.assertRaises(store.PublicStatePathError):
                migrate(self.source, apply=True)
        self.assertFalse(public.exists())

    def test_apply_preserves_ids_source_and_exact_backup_then_is_idempotent(self):
        before = self.source.read_bytes()
        report = migrate(self.source, self.target, apply=True)
        self.assertTrue(report["changed"])
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(Path(report["backups"]["source"]).read_bytes(), before)
        snapshot = store.read_snapshot(self.target)
        for coll in store.COLLECTIONS:
            self.assertEqual(set(snapshot[coll]), set(self.legacy[coll]))
            for record in snapshot[coll].values():
                self.assertEqual(record["_revision"], 0)
        target_before = self.target.read_bytes()
        second = migrate(self.source, self.target, apply=True)
        self.assertFalse(second["changed"])
        self.assertEqual(second["backups"], {})
        self.assertEqual(self.target.read_bytes(), target_before)

    def test_existing_unrelated_target_records_and_backup_are_preserved(self):
        target = store.Store(backend="local", local_path=self.target, fb_url="", key="test")
        target.put("settings", "unrelated", {"name": "Keep"})
        target.flush()
        before = self.target.read_bytes()
        report = migrate(self.source, self.target, apply=True)
        self.assertEqual(Path(report["backups"]["target"]).read_bytes(), before)
        self.assertIn("unrelated", store.read_snapshot(self.target)["settings"])
        self.assertEqual(report["target_counts_after"]["settings"], 2)

    def test_failed_apply_keeps_originals_and_returns_backup_recovery_details(self):
        target = store.Store(backend="local", local_path=self.target, fb_url="", key="test")
        target.put("settings", "unrelated", {"name": "Keep"})
        target.flush()
        source_before, target_before = self.source.read_bytes(), self.target.read_bytes()
        with mock.patch("migrate_studio_state.write_snapshot", side_effect=OSError("simulated write failure")):
            with self.assertRaises(MigrationFailure) as failure:
                migrate(self.source, self.target, apply=True, remove_source=True)
        report = failure.exception.report
        self.assertEqual(Path(report["backups"]["source"]).read_bytes(), source_before)
        self.assertEqual(Path(report["backups"]["target"]).read_bytes(), target_before)
        self.assertTrue(report["rollback"])
        self.assertEqual(self.source.read_bytes(), source_before)
        self.assertEqual(self.target.read_bytes(), target_before)

    def test_conflicting_records_abort_before_backups_or_writes(self):
        target = store.Store(backend="local", local_path=self.target, fb_url="", key="test")
        target.put("candidates", "candidate-original", {"title": "Private edited value"})
        target.flush()
        before = self.target.read_bytes()
        for apply in (False, True):
            with self.assertRaises(MigrationConflict):
                migrate(self.source, self.target, apply=apply)
        self.assertEqual(self.target.read_bytes(), before)
        self.assertFalse((self.target.parent / "backups").exists())

    def test_migration_does_not_resurrect_records_deleted_in_private_state(self):
        state = store.Store(backend="local", local_path=self.target, fb_url="", key="test")
        state.put("candidates", "candidate-original", {"title": "Story"})
        state.flush()
        state.delete("candidates", "candidate-original")
        state.flush()
        original = self.target.read_bytes()
        with self.assertRaises(MigrationConflict):
            migrate(self.source, self.target, apply=True)
        self.assertEqual(self.target.read_bytes(), original)

    def test_migration_preserves_versioned_source_tombstones(self):
        self.legacy["_deleted_revisions"] = {"drafts": {"previously-deleted": 5}}
        self.source.write_text(json.dumps(self.legacy), encoding="utf-8")
        report = migrate(self.source, self.target, apply=True)
        self.assertEqual(report["source_deletion_counts"]["drafts"], 1)
        self.assertEqual(store.read_snapshot(self.target)["_deleted_revisions"]["drafts"]["previously-deleted"], 5)
        second = migrate(self.source, self.target, apply=True)
        self.assertFalse(second["changed"])

    def test_removing_source_requires_explicit_apply_flag_and_verified_backup(self):
        with self.assertRaises(ValueError):
            migrate(self.source, self.target, remove_source=True)
        before = self.source.read_bytes()
        report = migrate(self.source, self.target, apply=True, remove_source=True)
        self.assertTrue(report["source_removed"])
        self.assertFalse(self.source.exists())
        self.assertEqual(Path(report["backups"]["source"]).read_bytes(), before)
        self.assertTrue(report["rollback"])

    def test_corrupt_source_missing_source_and_same_target_are_errors(self):
        self.source.write_text("{broken", encoding="utf-8")
        with self.assertRaises(store.SchemaError):
            migrate(self.source, self.target, apply=True)
        self.assertFalse(self.target.parent.exists())
        with self.assertRaises(FileNotFoundError):
            migrate(self.directory / "missing.json", self.target)
        with self.assertRaises(ValueError):
            migrate(self.source, self.source)

    def test_migration_rejects_duplicate_and_unsafe_json_without_writes(self):
        for raw in ('{"sources": {}, "sources": {}}',
                    '{"settings":{"x":{"constructor":{"value":"unsafe"}}}}}',
                    '{"sources":{"x":{"chars":NaN}}}'):
            with self.subTest(raw=raw):
                self.source.write_text(raw, encoding="utf-8")
                with self.assertRaises(store.SchemaError):
                    migrate(self.source, self.target, apply=True)
                self.assertFalse(self.target.parent.exists())


if __name__ == "__main__":
    unittest.main()
