"""Offline acceptance gates for private creator records and legacy preservation."""

from dataclasses import FrozenInstanceError, replace
import copy
import unittest

from creator.contracts import (
    Approval, ContentVariant, DocumentRevision, EvidenceClaim, EvidencePack,
    EvidenceSpan, SourceDocument, StoryBrief, ValidationError, approval_matches,
    content_fingerprint, convert_legacy_state, invalidate_approval, loads_strict,
    preview_caption, revise_variant, text_hash, validate_json_value, validate_url,
)


NOW = "2026-10-08T10:00:00+05:00"
TEXT = "Acme reports a 20% improvement on its internal benchmark."


def source(**changes):
    values = dict(id="source-1", original_url="https://example.com/announcement?edition=2",
                  canonical_url="https://example.com/announcement?edition=2", publisher="Acme",
                  text=TEXT, content_hash=text_hash(TEXT), retrieval_time=NOW,
                  retrieval_outcome="retrieved", source_type="official")
    values.update(changes)
    return SourceDocument(**values)


def evidence():
    document = source()
    span = EvidenceSpan("span-1", document.id, document.revision, document.content_hash,
                        0, len(TEXT), TEXT)
    claim = EvidenceClaim("claim-1", TEXT, (span.id,), "attributed", "Acme")
    pack = EvidencePack("story-1", (DocumentRevision(document.id, document.content_hash),),
                        (span,), (claim,), caveats=("Vendor benchmark; no independent test.",))
    return document, pack


def draft():
    record = dict(id="draft-1", revision=3, _revision=9, post="Original generated post",
                  edited_post="Owner-edited post", first_comment="Source: https://example.com/a",
                  edited_comment=None, hashtags=["#ai"], status="approved",
                  evidence_pack_id="story-1", evidence_pack_revision=1)
    record["approval"] = dict(revision=3, content_hash=content_fingerprint(record), approved_at=NOW)
    return record


class StrictContractTests(unittest.TestCase):
    def test_roundtrip_unicode_source_preserves_meaningful_query(self):
        original = source(text="Urdu: اردو. English: AI.", content_hash=text_hash("Urdu: اردو. English: AI."))
        self.assertEqual(SourceDocument.from_dict(original.to_dict()), original)
        self.assertIn("?edition=2", original.canonical_url)

    def test_direct_dataclass_is_frozen_and_revision_is_positive_integer(self):
        document = source()
        with self.assertRaises(FrozenInstanceError):
            document.text = "different"
        for invalid in (True, False, 0, -1, 1.0, "1"):
            with self.subTest(revision=invalid), self.assertRaises(ValidationError):
                source(revision=invalid)

    def test_unknown_schema_and_unknown_fields_are_rejected(self):
        for patch in ({"schema_version": 2}, {"schema_version": True}, {"extra": "silently ignored?"}):
            raw = source().to_dict()
            raw.update(patch)
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                SourceDocument.from_dict(raw)
        raw = source().to_dict()
        del raw["schema_version"]
        with self.assertRaises(ValidationError):
            SourceDocument.from_dict(raw)

    def test_nested_prototype_keys_and_non_json_values_are_rejected(self):
        for invalid in ({"x": [{"__proto__": {"polluted": True}}]}, {"constructor": 1},
                        {"x": {"prototype": []}}, {3: "bad key"}, {"x": float("nan")},
                        {"x": float("inf")}, {"x": (1, 2)}):
            with self.subTest(value=invalid), self.assertRaises(ValidationError):
                validate_json_value(invalid)

    def test_strict_json_rejects_duplicates_nonfinite_and_markdown_repair(self):
        for raw in ('{"id":1,"id":2}', '{"a":NaN}', '{"nested":{"x":1,"x":2}}',
                    '```json\n{"post":"text"}\n```', '{"post":"text",}'):
            with self.subTest(raw=raw), self.assertRaises(ValidationError):
                loads_strict(raw)
        self.assertEqual(loads_strict('{"text":"1\\n2"}'), {"text": "1\n2"})

    def test_links_reject_script_credentials_local_hosts_and_malformed_ports(self):
        for link in ("javascript:alert(1)", "file:///etc/passwd", "https://user:pass@example.com/",
                     "https://example.com\\@127.0.0.1/", "https://example.com/a\n",
                     "http://127.0.0.1/a", "http://192.168.1.1/", "http://[::1]/",
                     "http://localhost/", "https://example.com:99999/", "https://invalid_host.com/",
                     "https://example.com:0/", "https:///article"):
            with self.subTest(link=link), self.assertRaises(ValidationError):
                validate_url(link)
        self.assertEqual(validate_url("https://example.com/story?version=1&language=ur"),
                         "https://example.com/story?version=1&language=ur")

    def test_timezones_required_and_date_only_publication_remains_date_only(self):
        self.assertEqual(source(publication_time="2026-10-01").publication_time, "2026-10-01")
        with self.assertRaises(ValidationError):
            source(retrieval_time="2026-10-08T10:00:00")

    def test_source_text_hash_cannot_be_detached_from_text(self):
        with self.assertRaises(ValidationError):
            source(text="A different statement.")


class ProvenanceTests(unittest.TestCase):
    def test_evidence_roundtrip_checks_exact_source_revision_and_spans(self):
        document, pack = evidence()
        restored = EvidencePack.from_dict(pack.to_dict())
        self.assertEqual(restored, pack)
        self.assertIs(restored.validate_provenance({document.id: document}), restored)

    def test_same_length_changed_quote_is_rejected_at_source_boundary(self):
        document, pack = evidence()
        tampered = replace(pack.spans[0], quote=TEXT.replace("20%", "90%"))
        with self.assertRaises(ValidationError):
            tampered.validate_provenance(document)

    def test_changed_document_revision_and_content_cannot_reuse_old_evidence(self):
        document, pack = evidence()
        for changed in (replace(document, revision=2),
                        replace(document, text=TEXT + " Updated.", content_hash=text_hash(TEXT + " Updated."))):
            with self.subTest(document=changed), self.assertRaises(ValidationError):
                pack.validate_provenance({changed.id: changed})

    def test_missing_sources_unknown_spans_and_bool_offsets_are_rejected(self):
        document, pack = evidence()
        with self.assertRaises(ValidationError):
            pack.validate_provenance({})
        with self.assertRaises(ValidationError):
            replace(pack, claims=(EvidenceClaim("new", "Claim", ("missing",)),))
        with self.assertRaises(ValidationError):
            replace(pack.spans[0], start=False)
        with self.assertRaises(ValidationError):
            replace(pack, spans=pack.spans + pack.spans)

    def test_claim_attribution_and_brief_must_reference_shared_evidence(self):
        document, pack = evidence()
        brief = StoryBrief("story-1", pack.id, pack.revision, "Acme benchmark", "Vendor reports an improvement.",
                           claim_ids=(pack.claims[0].id,), caveats=pack.caveats)
        self.assertIs(brief.validate_evidence(pack), brief)
        with self.assertRaises(ValidationError):
            replace(brief, claim_ids=("invented",)).validate_evidence(pack)
        with self.assertRaises(ValidationError):
            EvidenceClaim("claim", "Supported claim", assessment="supported")
        with self.assertRaises(ValidationError):
            EvidenceClaim("claim", "Vendor claim", ("span",), "attributed")


class ApprovalRevisionTests(unittest.TestCase):
    def test_material_edits_clear_approval_and_return_pending_content_to_review(self):
        before = draft()
        for patch in ({"edited_post": "New words"}, {"edited_post": ""}, {"edited_comment": "New source"},
                      {"hashtags": ["#new"]}, {"evidence_pack_revision": 2}, {"evidence_revision": 2},
                      {"asset_ids": ["new-asset"]}, {"assets": ["new.png"]},
                      {"facts": "Different factual context"}, {"url": "https://example.com/new"},
                      {"candidate_id": "different-source"},
                      {"language": "ur"}, {"visual": "New graphic"}):
            with self.subTest(patch=patch):
                after = invalidate_approval(before, dict(before, **patch))
                self.assertIsNone(after["approval"])
                self.assertEqual(after["status"], "draft")
                self.assertFalse(approval_matches(after))
        self.assertTrue(approval_matches(before))

    def test_status_schedule_metadata_and_generated_text_under_edit_keep_approval(self):
        before = draft()
        for patch in ({"status": "scheduled", "scheduled_for": NOW}, {"_revision": 10},
                      {"rating": 4, "stats": {"impressions": 90}}, {"post": "New generated text under owner edit"},
                      {"verify": {"verdict": "warn", "issues": ["needs review"]}}):
            with self.subTest(patch=patch):
                after = invalidate_approval(before, dict(before, **patch))
                self.assertEqual(after["approval"], before["approval"])
                self.assertTrue(approval_matches(after))

    def test_approval_is_revision_bound_and_rejects_boolean_revision(self):
        before = draft()
        self.assertFalse(approval_matches(dict(before, revision=4)))
        self.assertFalse(approval_matches(dict(before, revision=True)))
        self.assertFalse(approval_matches(dict(before, approval=dict(before["approval"], revision=True))))

    def test_editing_published_history_does_not_rewrite_publication_status(self):
        before = dict(draft(), status="published", published_at=NOW)
        after = invalidate_approval(before, dict(before, edited_post="Corrected wording"))
        self.assertEqual(after["status"], "published")
        self.assertEqual(after["published_at"], NOW)
        self.assertIsNone(after["approval"])

    def test_frozen_variant_revision_approval_and_status_only_changes(self):
        variant = ContentVariant("v1", "s1", "Reviewed body")
        approved = replace(variant, approval=Approval(1, content_fingerprint(variant.to_dict()), NOW),
                           review_state="approved")
        self.assertTrue(approval_matches(approved.to_dict()))
        scheduled = revise_variant(approved, review_state="scheduled", scheduled_for=NOW)
        self.assertEqual(scheduled.revision, approved.revision)
        self.assertEqual(scheduled.approval, approved.approval)
        edited = revise_variant(scheduled, body="Revised body")
        self.assertEqual(edited.revision, 2)
        self.assertIsNone(edited.approval)
        self.assertEqual(edited.review_state, "draft")
        with self.assertRaises(ValidationError):
            revise_variant(approved, revision=50)
        with self.assertRaises(ValidationError):
            replace(approved, body="Undetected edit")


class LegacyPreservationTests(unittest.TestCase):
    def test_migration_preview_preserves_links_edits_schedules_publication_and_unknown_metadata(self):
        state = {"sources": {"candidate-1": {"id": "candidate-1", "url": "https://example.com/story",
                    "original_url": "https://example.com/feed?ref=1", "source": "Acme", "excerpt": TEXT,
                    "ok": True, "numbers": ["20%"], "published": "2026-10-01"}},
                 "drafts": {"draft-1": {"id": "draft-1", "candidate_id": "candidate-1",
                    "title": "Original title", "post": "Generated words", "edited_post": "Owner edits",
                    "first_comment": "Original comment", "edited_comment": "Edited https://example.com/story",
                    "hashtags": ["#ai"], "status": "scheduled", "scheduled_for": NOW,
                    "verify": {"verdict": "pass"}, "custom_metadata": {"owner": "Ahmad"}},
                    "posted-1": {"post": "Already published", "status": "published", "published_at": NOW}},
                 "settings": {"automation_enabled": True}, "runs": {}, "candidates": {}, "updated": NOW}
        original = copy.deepcopy(state)
        imported = convert_legacy_state(state)
        self.assertEqual(state, original)
        self.assertEqual(imported["legacy_state"], original)
        self.assertFalse(imported["automation_enabled"])
        self.assertEqual(imported["id_map"]["drafts"], {"draft-1": "draft-1", "posted-1": "posted-1"})
        variant = imported["content_variants"]["draft-1"]
        self.assertEqual(variant["body"], "Owner edits")
        self.assertEqual(variant["source_comment"], "Edited https://example.com/story")
        self.assertEqual(variant["review_state"], "scheduled")
        self.assertEqual(variant["scheduled_for"], NOW)
        self.assertIsNone(variant["approval"])
        self.assertEqual(imported["content_variants"]["posted-1"]["published_at"], NOW)
        self.assertEqual(imported["source_documents"]["candidate-1"]["retrieval_outcome"], "not_checked")
        self.assertEqual(imported["source_documents"]["candidate-1"]["publication_time"], "2026-10-01")
        self.assertIsNone(imported["source_documents"]["candidate-1"]["truncated"])
        self.assertEqual(imported["evidence_packs"]["candidate-1"]["assessment"], "not_checked")
        self.assertEqual(imported["evidence_packs"]["candidate-1"]["claims"], [])

    def test_migration_does_not_silently_repair_invalid_old_source_links(self):
        with self.assertRaises(ValidationError):
            convert_legacy_state({"sources": {"bad": {"url": "javascript:alert(1)"}}})

    def test_future_format_preview_uses_shared_brief_rather_than_linkedin_output(self):
        brief = StoryBrief("s1", "e1", 2, "Title", "Neutral evidence summary", claim_ids=("c1",))
        caption = preview_caption(brief)
        self.assertEqual(caption.body, brief.summary)
        self.assertEqual(caption.claim_refs, brief.claim_ids)
        self.assertEqual(caption.evidence_pack_revision, 2)
        self.assertEqual(caption.review_state, "draft")
        self.assertEqual(caption.platform, "test_caption")
        self.assertIsNone(caption.approval)
        self.assertIs(caption.validate_story(brief), caption)
        with self.assertRaises(ValidationError):
            caption.validate_story(replace(brief, revision=2))
        with self.assertRaises(ValidationError):
            replace(caption, claim_refs=("untraced",)).validate_story(brief)
        with self.assertRaises(ValidationError):
            preview_caption({"post": "Edited LinkedIn post"})


if __name__ == "__main__":
    unittest.main()
