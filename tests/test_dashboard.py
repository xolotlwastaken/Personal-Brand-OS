"""Deterministic HTTP/security checks. No Docker, production state or inference."""
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dashboard_server', ROOT / 'dashboard/server.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calls = []

        def adapter(payload):
            cls.calls.append(payload)
            if payload['op'] == 'snapshot':
                return {'agents': [], 'board': {'tasks': [], 'truncated': False}, 'gateway': 'healthy'}
            return {'task_id': 't_synthetic', 'ok': True}

        cls.server = module.DashboardServer(0, adapter)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'
        cls.temp = tempfile.TemporaryDirectory()
        cls.original_vault = module.VAULT
        module.VAULT = Path(cls.temp.name) / 'knowledge'
        module.VAULT.mkdir()
        (module.VAULT / 'draft.md').write_text('# Synthetic fixture\n<script>alert(1)</script>')
        (module.VAULT / 'escape.md').symlink_to('/etc/passwd')
        (module.VAULT / '.secret.md').write_text('Synthetic private fixture')
        (module.VAULT / 'large.md').write_text('x' * 256001)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        module.VAULT = cls.original_vault
        cls.temp.cleanup()

    def request(self, path, data=None, headers=None):
        default = {'Content-Type': 'application/json'}
        default.update(headers or {})
        request = Request(self.base + path, data=json.dumps(data).encode() if data is not None else None,
                          headers=default)
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as error:
            response = error
        with response:
            return response.status, response.headers, response.read()

    def test_static_and_security_headers(self):
        for path in ('/', '/app.js', '/style.css', '/chat.js', '/chat.css', '/ceo-page.js', '/ceo-page.css'):
            status, headers, body = self.request(path)
            self.assertEqual(status, 200)
            self.assertTrue(body)
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertEqual(headers['X-Frame-Options'], 'DENY')
            self.assertIn("script-src 'self'", headers['Content-Security-Policy'])

    def test_host_rebinding_and_cross_origin_blocked(self):
        for headers in ({'Host': 'attacker.test'}, {'Origin': 'https://attacker.test'},
                        {'Sec-Fetch-Site': 'cross-site'}):
            self.assertEqual(self.request('/api/bootstrap', headers=headers)[0], 403)

    def test_write_requires_token_and_does_not_call_adapter(self):
        before = len(self.calls)
        self.assertEqual(self.request('/api/action', {'op': 'create'})[0], 403)
        self.assertEqual(len(self.calls), before)

    def test_only_allowed_actions_forwarded(self):
        headers = {'X-Dashboard-Token': self.server.token}
        for op in ('delete', 'shell', 'complete', 'publish', 'snapshot'):
            self.assertEqual(self.request('/api/action', {'op': op}, headers)[0], 400)
        self.assertEqual(self.request('/api/action', {'op': 'comment', 'task_id': 't_synthetic',
                                                    'body': 'Synthetic feedback'}, headers)[0], 200)
        self.assertEqual(self.calls[-1]['op'], 'comment')

    def test_vault_is_scoped_and_symlinks_rejected(self):
        for path in ('../.env', '/etc/passwd', 'escape.md', '.secret.md', 'missing.yaml'):
            self.assertEqual(self.request('/api/artifact?path=' + path)[0], 403)
        self.assertEqual(self.request('/api/artifact?path=missing.md')[0], 404)
        self.assertEqual(self.request('/api/artifact?path=large.md')[0], 413)
        status, _, body = self.request('/api/artifact?path=draft.md')
        self.assertEqual(status, 200)
        self.assertIn('Synthetic fixture', json.loads(body)['content'])

    def test_snapshot_cache_and_scope(self):
        before = len(self.calls)
        status, _, body = self.request('/api/snapshot?tenant=synthetic-test')
        self.assertEqual(status, 200)
        self.assertFalse(any(f['path'] in {'escape.md', '.secret.md'} for f in json.loads(body)['artifacts']))
        self.request('/api/snapshot?tenant=synthetic-test')
        self.assertEqual(len(self.calls), before + 1)
        self.assertEqual(self.calls[-1]['tenant'], 'synthetic-test')

    def test_skill_allowlist_and_private_files_not_served(self):
        self.assertEqual(self.request('/api/skill?name=../../.env')[0], 404)
        for path in ('/.env', '/data/hermes/auth.json', '/server.py', '/../README.md'):
            self.assertEqual(self.request(path)[0], 404)
        self.assertEqual(self.request('/api/skill?name=viral-hook-writer')[0], 200)

    def test_rate_limit_before_adapter(self):
        with self.server.lock:
            old = list(self.server.requests)
            self.server.requests.clear()
            self.server.requests.extend([module.time.monotonic()] * 20)
        try:
            self.assertEqual(self.request('/api/action', {'op': 'unblock'},
                                          {'X-Dashboard-Token': self.server.token})[0], 429)
        finally:
            with self.server.lock:
                self.server.requests.clear()
                self.server.requests.extend(old)

    def test_ceo_desk_and_actions_keep_existing_security_boundary(self):
        status, _, body = self.request('/api/ceo')
        self.assertEqual(status, 200)
        self.assertEqual(self.calls[-1], {'op': 'ceo_thread'})
        self.assertIn('brand_state', json.loads(body))
        for op in ('ceo_message', 'ceo_reply'):
            before = len(self.calls)
            self.assertEqual(self.request('/api/action', {'op': op})[0], 403)
            self.assertEqual(len(self.calls), before)
            self.assertEqual(self.request('/api/action', {'op': op},
                                         {'X-Dashboard-Token': self.server.token})[0], 200)
            self.assertEqual(self.calls[-1]['op'], op)

    def test_brand_state_uses_canonical_strategy_not_test_artifacts(self):
        folder = module.VAULT / 'brand'
        folder.mkdir(exist_ok=True)
        strategy = folder / 'strategy.md'
        try:
            (folder / 'verification-brand-manager.md').write_text('status: approved\napproval: human-approved')
            self.assertEqual(module.brand_state()['state'], 'missing')
            strategy.write_text('---\nstatus: starting-draft\napproval: pending-refinement\n---\n# Strategy')
            self.assertEqual(module.brand_state()['state'], 'discovery')
            strategy.write_text('---\nstatus: review\napproval: pending\n---\n# Strategy proposal')
            self.assertEqual(module.brand_state()['state'], 'review')
            strategy.write_text('---\nstatus: approved\napproval: human-approved\n---\n# Strategy')
            self.assertEqual(module.brand_state()['state'], 'approved')
            strategy.unlink()
            strategy.symlink_to('/etc/passwd')
            self.assertEqual(module.brand_state()['state'], 'missing')
        finally:
            strategy.unlink(missing_ok=True)
            (folder / 'verification-brand-manager.md').unlink(missing_ok=True)

    def test_conversation_reads_scoped_and_chat_actions_authenticated(self):
        self.assertEqual(self.request('/api/conversations?profile=brand-manager')[0], 200)
        self.assertEqual(self.calls[-1], {'op': 'conversations', 'profile': 'brand-manager'})
        self.assertEqual(self.request('/api/conversation?profile=brand-manager&id=synthetic')[0], 200)
        self.assertEqual(self.calls[-1]['session_id'], 'synthetic')
        with patch.object(self.server.chat, 'open', return_value={'session_id': 'synthetic'}) as opening:
            self.assertEqual(self.request('/api/action', {'op': 'chat_open', 'profile': 'brand-ceo'})[0], 403)
            opening.assert_not_called()
            self.assertEqual(self.request('/api/action', {'op': 'chat_open', 'profile': 'brand-ceo'},
                                          {'X-Dashboard-Token': self.server.token})[0], 200)
            opening.assert_called_once_with('brand-ceo', '')
        with patch.object(self.server.chat, 'send', return_value={'ok': True}) as sending:
            self.assertEqual(self.request('/api/action', {'op': 'chat_send', 'profile': 'brand-ceo',
                    'session_id': 'synthetic', 'body': 'Synthetic message'},
                    {'X-Dashboard-Token': self.server.token})[0], 200)
            sending.assert_called_once_with('brand-ceo', 'synthetic', 'Synthetic message')

    def test_stream_scope_and_invalid_cursor(self):
        self.assertEqual(self.request('/api/chat/events?profile=default&session=bad')[0], 400)
        self.assertEqual(self.request('/api/chat/events?profile=brand-ceo&session=bad&after=-1')[0], 400)
        self.assertEqual(self.request('/api/chat/state?profile=brand-ceo&session=absent')[0], 409)

    def test_stream_replay_is_json_encoded_and_connection_slots_released(self):
        frame = {'id': 8, 'type': 'message.delta', 'payload': {'text': 'SYNTHETIC\ndata: <script>'}}
        with patch.object(self.server.chat, 'state', return_value={'running': True}), \
             patch.object(self.server.chat, 'events', side_effect=[[frame], module.LiveError('Synthetic closure')]) as events:
            status, headers, body = self.request('/api/chat/events?profile=brand-ceo&session=synthetic',
                                                  headers={'Last-Event-ID': '7'})
            self.assertEqual(status, 200)
            self.assertIn('text/event-stream', headers['Content-Type'])
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertEqual(events.call_args_list[0].args, ('brand-ceo', 'synthetic', 7))
            self.assertEqual(json.loads(body.decode().split('data: ', 1)[1].split('\n\n')[0]), frame)
        self.assertTrue(self.server.stream_slots.acquire(blocking=False))
        self.server.stream_slots.release()

    def test_stream_limit_and_invalid_chat_profile(self):
        held = 0
        while self.server.stream_slots.acquire(blocking=False):
            held += 1
        try:
            with patch.object(self.server.chat, 'state', return_value={}):
                self.assertEqual(self.request('/api/chat/events?profile=brand-ceo&session=synthetic')[0], 429)
        finally:
            for _ in range(held):
                self.server.stream_slots.release()
        self.assertEqual(self.request('/api/action', {'op': 'chat_open', 'profile': 'default'},
                                      {'X-Dashboard-Token': self.server.token})[0], 400)


if __name__ == '__main__':
    unittest.main(verbosity=2)
