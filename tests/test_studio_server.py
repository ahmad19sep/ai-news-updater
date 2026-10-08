"""Offline tests for the authenticated local editing boundary."""

from pathlib import Path
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from agents.store import Store
from creator.contracts import approval_matches
from studio_server import create_app


class PrivateStudioServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / 'private' / 'state.json'
        self.docs = self.root / 'public'
        self.docs.mkdir()
        self.docs.joinpath('studio.html').write_text(
            '<script>window.STUDIO_DATA = {"lockHash":"legacy-hash","fbUrl":"https://legacy.invalid"};</script>\n', encoding='utf-8')
        self.app = create_app(state_path=self.state, passcode='test-owner-code', secret_key='test-session-secret-for-offline-tests-only', docs_dir=self.docs)
        self.app.testing = True
        self.client = self.app.test_client()
        store = self.store()
        store.put('sources', 'story', {'excerpt': 'A team released an open research tool. Its documentation describes the evaluation process.', 'quotes': [], 'title': 'Research tool'})
        store.put('drafts', 'draft', {'candidate_id': 'story', 'title': 'Research tool', 'post': 'A research tool is available.\n\nRead the evaluation process before choosing it.', 'first_comment': 'Source documentation', 'hashtags': [], 'status': 'draft'})
        store.flush()
        self.csrf = None

    def store(self):
        return Store(backend='local', local_path=self.state)

    def login(self, client=None):
        client = client or self.client
        response = client.post('/api/session', json={'passcode': 'test-owner-code'})
        self.assertEqual(response.status_code, 200)
        self.csrf = response.json['csrf_token']
        return self.csrf

    def edit(self, fields, record='draft', collection='drafts', revision=None, client=None, csrf=None):
        if revision is None:
            revision = (self.store().get(collection, record) or {}).get('_revision', 0)
        return (client or self.client).patch(f'/api/records/{collection}/{record}', json={'expected_revision': revision, 'fields': fields}, headers={'X-Studio-CSRF': csrf or self.csrf or ''})

    def approve(self, record='draft'):
        response = self.edit({'status': 'approved'}, record=record)
        self.assertEqual(response.status_code, 200, response.json)
        self.assertTrue(approval_matches(response.json['record']))
        return response.json['record']

    def future(self):
        return (datetime.now(timezone.utc) + timedelta(days=2)).replace(microsecond=0).isoformat()

    def test_private_reads_and_writes_require_session(self):
        self.assertEqual(self.client.get('/api/state').status_code, 401)
        self.assertEqual(self.edit({'post': 'unauthorized'}).status_code, 401)
        self.assertEqual(self.client.get('/api/session').json, {'authenticated': False, 'csrf_token': None})
        self.assertEqual(self.client.post('/api/session', json={'passcode': 'wrong'}).status_code, 401)
        token = self.login()
        response = self.client.get('/api/state')
        self.assertEqual(response.status_code, 200)
        self.assertIn('draft', response.json['drafts'])
        self.assertEqual(self.client.get('/api/session').json['csrf_token'], token)
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_session_cookie_rotation_logout_and_csrf(self):
        response = self.client.post('/api/session', json={'passcode': 'test-owner-code'})
        cookie = response.headers['Set-Cookie']
        self.assertIn('HttpOnly', cookie)
        self.assertIn('SameSite=Strict', cookie)
        old = response.json['csrf_token']
        self.login()
        self.assertNotEqual(old, self.csrf)
        self.assertEqual(self.edit({'notes': 'stale token'}, csrf=old).status_code, 403)
        self.assertEqual(self.client.delete('/api/session').status_code, 403)
        self.assertEqual(self.client.delete('/api/session', headers={'X-Studio-CSRF': self.csrf}).status_code, 200)
        self.assertEqual(self.client.get('/api/state').status_code, 401)
        with self.client.session_transaction() as session:
            self.assertNotIn('owner', session)

    def test_forged_session_does_not_authorize(self):
        self.client.set_cookie('creator_studio_session', 'forged-value')
        self.assertEqual(self.client.get('/api/state').status_code, 401)

    def test_expired_signed_session_requires_login(self):
        with patch('itsdangerous.timed.time.time', return_value=time.time() - 9 * 3600):
            self.login()
        self.assertEqual(self.client.get('/api/state').status_code, 401)

    def test_host_remote_address_and_origin_guards(self):
        self.assertEqual(self.client.get('/api/session', base_url='http://evil.example').status_code, 403)
        self.assertEqual(self.client.get('/api/session', environ_overrides={'REMOTE_ADDR': '10.1.2.3'}).status_code, 403)
        self.assertEqual(self.client.post('/api/session', json={'passcode': 'test-owner-code'}, headers={'Origin': 'https://evil.example'}).status_code, 403)
        self.assertEqual(self.client.post('/api/session', json={'passcode': 'test-owner-code'}, headers={'Sec-Fetch-Site': 'cross-site'}).status_code, 403)
        self.assertEqual(self.client.post('/api/session', data='passcode=test-owner-code').status_code, 400)
        self.assertEqual(self.client.post('/api/session', json={'passcode': 'test-owner-code'}, headers={'Origin': 'http://localhost'}).status_code, 200)

    def test_request_json_is_strict_and_failures_do_not_write(self):
        self.login()
        original = self.state.read_bytes()
        for body in ['{"expected_revision":1,"expected_revision":0,"fields":{"post":"bad"}}', '{"expected_revision":NaN,"fields":{"post":"bad"}}', '{"expected_revision":1,"fields":{"__proto__":{"owner":true}}}', '{broken']:
            with self.subTest(body=body):
                response = self.client.patch('/api/records/drafts/draft', data=body, content_type='application/json', headers={'X-Studio-CSRF': self.csrf})
                self.assertEqual(response.status_code, 422)
                self.assertEqual(self.state.read_bytes(), original)
        self.assertEqual(self.client.post('/api/session', data='{"passcode":"a","passcode":"b"}', content_type='application/json').status_code, 422)
        self.assertEqual(self.client.post('/api/session', json={'passcode': 'x' * 100000}).status_code, 413)

    def test_protected_fields_and_invalid_types_are_rejected(self):
        self.login()
        for fields in [{'approval': {}}, {'revision': 9}, {'published_at': 'yesterday'}, {'evidence_revision': 4}, {'automation_enabled': True}, {'post': []}, {'hashtags': 'wrong'}, {'claims': ['wrong']}, {'rating': 11}, {'score': True}, {'stats': {'views': -1}}, {'channel': 'instagram'}, {'url': 'javascript:alert(1)'}, {'url': 'https://owner:secret@example.com'}]:
            with self.subTest(fields=fields):
                self.assertEqual(self.edit(fields).status_code, 422)
        self.assertEqual(self.edit({'slots': ['Tue 99:00']}, collection='settings', record='profile').status_code, 422)
        self.assertEqual(self.edit({'postsPerWeek': 15}, collection='settings', record='profile').status_code, 422)
        self.assertEqual(self.edit({'post': 'bad'}, collection='runs').status_code, 404)
        self.assertEqual(self.edit({'post': 'bad'}, record='bad.id').status_code, 404)
        self.assertEqual(self.edit({'url': ''}).status_code, 200)

    def test_stale_writer_conflicts_and_latest_edit_is_preserved(self):
        first_token = self.login()
        other = self.app.test_client()
        other_token = self.login(other)
        revision = self.store().get('drafts', 'draft')['_revision']
        first = self.edit({'edited_post': 'First session edit'}, revision=revision, csrf=first_token)
        self.assertEqual(first.status_code, 200)
        stale = self.edit({'edited_post': 'Second stale edit'}, revision=revision, client=other, csrf=other_token)
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.json['current']['edited_post'], 'First session edit')
        self.assertEqual(self.store().get('drafts', 'draft')['edited_post'], 'First session edit')

    def test_approval_requires_saved_content_and_support_and_checks(self):
        self.login()
        self.assertEqual(self.edit({'post': 'Changed content', 'status': 'approved'}).status_code, 422)
        self.assertEqual(self.edit({'post': 'This is a game changer.'}).status_code, 200)
        self.assertEqual(self.edit({'status': 'approved'}).status_code, 422)
        self.assertEqual(self.edit({'post': 'A useful tool.', 'candidate_id': 'missing'}).status_code, 200)
        self.assertEqual(self.edit({'status': 'approved'}).status_code, 422)
        self.assertEqual(self.edit({'facts': 'The team released a tool.'}).status_code, 200)
        approved = self.approve()
        self.assertEqual(approved['approval']['kind'], 'owner_manual')
        self.assertEqual(approved['approval']['verification_state'], 'deterministic_screen')
        self.assertNotIn('published_at', approved)

    def test_material_edits_invalidate_current_approval_and_status_only_does_not(self):
        self.login()
        approved = self.approve()
        notes = self.edit({'notes': 'Review note'}).json['record']
        self.assertEqual(notes['revision'], approved['revision'])
        self.assertTrue(approval_matches(notes))
        changed = self.edit({'edited_post': ''}).json['record']
        self.assertEqual(changed['status'], 'draft')
        self.assertIsNone(changed['approval'])
        self.assertEqual(changed['edited_post'], '')
        self.assertGreater(changed['revision'], approved['revision'])
        self.assertEqual(self.edit({'status': 'approved'}).status_code, 422)

    def test_source_update_invalidates_linked_approval_atomically(self):
        self.login()
        approved = self.approve()
        response = self.edit({'excerpt': 'Updated source evidence.'}, collection='sources', record='story')
        self.assertEqual(response.status_code, 200, response.json)
        linked = response.json['related_drafts']['draft']
        self.assertIsNone(linked['approval'])
        self.assertEqual(linked['status'], 'draft')
        self.assertGreater(linked['revision'], approved['revision'])
        self.assertEqual(linked['evidence_revision'], response.json['record']['_revision'])
        self.assertEqual(self.store().get('drafts', 'draft'), linked)

    def test_schedule_and_manual_post_require_current_approval(self):
        self.login()
        self.assertEqual(self.edit({'status': 'scheduled', 'scheduled_for': self.future()}).status_code, 422)
        self.assertEqual(self.edit({'status': 'published'}).status_code, 422)
        self.approve()
        for value in ['2000-01-01T00:00:00+00:00', '2099-01-01T00:00:00', 'bad']:
            self.assertEqual(self.edit({'status': 'scheduled', 'scheduled_for': value}).status_code, 422)
        scheduled = self.edit({'status': 'scheduled', 'scheduled_for': self.future()})
        self.assertEqual(scheduled.status_code, 200, scheduled.json)
        posted = self.edit({'status': 'published'})
        self.assertEqual(posted.status_code, 200, posted.json)
        self.assertEqual(posted.json['record']['publication_confirmation'], 'owner_manual')
        self.assertIn('published_at', posted.json['record'])
        first_time = posted.json['record']['published_at']
        with patch('studio_server.now_iso', return_value='2099-01-01T00:00:00+00:00'):
            repeated = self.edit({'status': 'published'})
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(repeated.json['record']['published_at'], first_time)
        self.assertEqual(self.edit({'status': 'draft'}).status_code, 422)

    def test_deleted_source_invalidates_approval_before_scheduling(self):
        self.login()
        self.approve()
        store = self.store()
        store.delete('sources', 'story')
        store.flush()
        self.assertEqual(self.edit({'status': 'scheduled', 'scheduled_for': self.future()}).status_code, 422)
        self.assertIsNone(self.store().get('drafts', 'draft')['approval'])

    def test_partial_schedule_edits_require_approval_and_valid_time(self):
        self.login()
        store = self.store()
        store.patch('drafts', 'draft', status='scheduled', scheduled_for=self.future())
        store.flush()
        self.assertEqual(self.edit({'scheduled_for': self.future()}).status_code, 422)
        self.assertEqual(self.edit({'status': 'draft'}).status_code, 200)
        self.approve()
        self.assertEqual(self.edit({'status': 'scheduled', 'scheduled_for': self.future()}).status_code, 200)
        self.assertEqual(self.edit({'scheduled_for': '2000-01-01T00:00:00'}).status_code, 422)
        changed = self.edit({'post': 'An edited scheduled post.', 'scheduled_for': 'legacy invalid value'})
        self.assertEqual(changed.status_code, 200, changed.json)
        self.assertEqual(changed.json['record']['status'], 'draft')

    def test_schedule_conflicts_compare_instants_not_offsets(self):
        self.login()
        self.approve()
        when = self.future()
        self.assertEqual(self.edit({'status': 'scheduled', 'scheduled_for': when}).status_code, 200)
        store = self.store()
        source = store.get('drafts', 'draft')
        store.put('drafts', 'other', dict({key: value for key, value in source.items() if key not in {'id', '_revision', 'approval'}}, status='draft'))
        store.flush()
        self.approve('other')
        same_instant = datetime.fromisoformat(when).astimezone(timezone(timedelta(hours=5))).isoformat()
        response = self.edit({'status': 'scheduled', 'scheduled_for': same_instant}, record='other')
        self.assertEqual(response.status_code, 422, response.json)
        self.assertIn('occupied', response.json['error'])

    def test_schedule_is_rechecked_against_latest_merged_snapshot(self):
        self.login()
        self.approve()
        when = self.future()
        original_flush = Store.flush
        injected = False

        def concurrent_flush(store, *, validator=None):
            nonlocal injected
            if validator is not None and not injected:
                injected = True
                other = self.store()
                other.put('drafts', 'concurrent', {'post': 'Other post', 'status': 'draft'})
                other.patch('drafts', 'concurrent', status='scheduled', scheduled_for=when)
                original_flush(other)
            return original_flush(store, validator=validator)

        with patch.object(Store, 'flush', concurrent_flush):
            response = self.edit({'status': 'scheduled', 'scheduled_for': when})
        self.assertEqual(response.status_code, 422, response.json)
        self.assertEqual(self.store().get('drafts', 'draft')['status'], 'approved')
        self.assertIsNotNone(self.store().get('drafts', 'concurrent'))

    def test_deleted_id_cannot_be_silently_recreated(self):
        self.login()
        store = self.store()
        store.delete('drafts', 'draft')
        store.flush()
        conflict = self.edit({'post': 'recreate'}, revision=0)
        self.assertEqual(conflict.status_code, 409)
        deleted_revision = conflict.json['deleted_revision']
        self.assertGreater(deleted_revision, 0)
        self.assertIsNone(self.store().get('drafts', 'draft'))
        restored = self.edit({'post': 'Explicitly restored owner work'}, revision=deleted_revision)
        self.assertEqual(restored.status_code, 200, restored.json)
        self.assertEqual(restored.json['record']['status'], 'draft')
        self.assertGreater(restored.json['record']['_revision'], deleted_revision)

    def test_manual_draft_creation_and_legacy_source_binding_remain_editable(self):
        self.login()
        created = self.edit({'candidate_id': 'story', 'title': 'Owner draft', 'post': '', 'status': 'draft'}, record='manual', revision=0)
        self.assertEqual(created.status_code, 200, created.json)
        self.assertEqual(created.json['record']['evidence_revision'], 1)
        self.assertEqual(self.edit({'post': 'Saved owner draft.'}, record='manual').status_code, 200)
        self.approve('manual')

    def test_corrupt_store_is_reported_without_replacing_original(self):
        self.login()
        self.state.write_text('{broken', encoding='utf-8')
        response = self.client.get('/api/state')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.state.read_text(encoding='utf-8'), '{broken')

    def test_generated_shell_contains_no_private_state_or_auth_hash(self):
        response = self.client.get('/studio.html')
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn('"privateApi": "/api"', text)
        for private in ['test-owner-code', 'test-session-secret', 'legacy-hash', 'https://legacy.invalid', 'evaluation process']:
            self.assertNotIn(private, text)
        for path in ['/pipeline.json', '/.studio-private/pipeline.json', '/private/state.json', '/studio/private-state.js']:
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_public_state_configuration_and_missing_passcode_fail_closed(self):
        with self.assertRaises(ValueError):
            create_app(state_path=self.docs / 'pipeline.json', docs_dir=self.docs, passcode='test-owner-code')
        with self.assertRaises(ValueError):
            create_app(state_path=self.state, docs_dir=self.docs, passcode='short')
        with self.assertRaises(ValueError):
            create_app(state_path=self.state, docs_dir=self.docs, passcode='test-owner-code', secret_key='weak')
        self.docs.joinpath('studio.html').write_text('outdated shell', encoding='utf-8')
        self.assertEqual(self.client.get('/studio.html').status_code, 503)


if __name__ == '__main__':
    unittest.main()
