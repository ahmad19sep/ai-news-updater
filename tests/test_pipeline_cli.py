"""The private UI's copied command must not silently select legacy Firebase."""
import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agents.store import Store
import run_pipeline


class LocalPipelineCommandTests(unittest.TestCase):
    def test_explicit_local_status_uses_private_state_with_legacy_firebase_configured(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / 'state.json'
            store = Store(backend='local', local_path=state)
            store.put('drafts', 'local_draft', {'post': 'Local owner work.', 'status': 'draft'})
            store.flush()
            with patch.dict(os.environ, {'FIREBASE_URL': 'https://legacy.invalid', 'STUDIO_STATE_PATH': str(state)}), patch('agents.store.requests.get') as network, patch('run_pipeline.log', side_effect=print), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(run_pipeline.main(['--store', 'local', '--status']), 0)
                network.assert_not_called()
            self.assertIn('drafts', output.getvalue())
            self.assertEqual(Store(backend='local', local_path=state).get('drafts', 'local_draft')['post'], 'Local owner work.')


if __name__ == '__main__':
    unittest.main()
