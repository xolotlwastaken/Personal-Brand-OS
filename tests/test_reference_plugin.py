"""Synthetic native-tool adapter checks. No external requests or model calls."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import io
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(os.environ.get('BRAND_REFERENCE_TEST_ROOT', Path(__file__).resolve().parents[1]))
spec = importlib.util.spec_from_file_location('reference_plugin', ROOT / 'config/plugins/reference-acquisition/__init__.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PluginTest(unittest.TestCase):
    def test_register_exact_tools(self):
        registered = []
        p.register(types.SimpleNamespace(register_tool=lambda **kw: registered.append(kw)))
        self.assertEqual({x['name'] for x in registered}, {'brand_reference_search', 'brand_reference_fetch',
                                                        'brand_reference_prepare', 'brand_reference_visual'})
        self.assertTrue(all(x['toolset'] == 'brand-references' for x in registered))

    def test_handler_unknown_fields_not_forwarded(self):
        with patch.object(p, 'worker') as mock:
            self.assertIn('error', json.loads(p.search({'query': 'x', 'shell': 'id'})))
            self.assertIn('error', json.loads(p.fetch({'url': 'x', 'cookies': 'secret'})))
            self.assertIn('error', json.loads(p.prepare({'media_path': 'x', 'cmd': 'id'})))
            mock.assert_not_called()

    def test_worker_timeout_and_absent_runtime(self):
        with patch.object(p.Path, 'is_file', return_value=False):
            self.assertIn('setup', p.worker({'action': 'search', 'query': 'x'})['error'])
        proc = types.SimpleNamespace(communicate=lambda **kw: (_ for _ in ()).throw(subprocess.TimeoutExpired('worker', 60)), pid=99999)
        with patch.object(p.Path, 'is_file', return_value=True), patch.object(p.subprocess, 'Popen', return_value=proc), \
             patch.object(p.os, 'killpg') as killed, patch.object(p, 'stop_worker') as stop:
            self.assertEqual(p.worker({'action': 'fetch', 'url': 'x'})['status'], 'unavailable')
            stop.assert_called_once()

    def test_worker_strips_credentials_and_proxies(self):
        proc = types.SimpleNamespace(communicate=lambda **kw: ('{"results":[]}', ''), returncode=0)
        with patch.object(p.Path, 'is_file', return_value=True), patch.object(p.subprocess, 'Popen', return_value=proc) as start, \
             patch.dict(os.environ, {'NVIDIA_API_KEY': 'sentinel', 'HTTPS_PROXY': 'sentinel'}):
            self.assertEqual(p.worker({'action': 'search', 'query': 'x'})['results'], [])
            env = start.call_args.kwargs['env']
            self.assertNotIn('NVIDIA_API_KEY', env)
            self.assertNotIn('HTTPS_PROXY', env)
            self.assertTrue(start.call_args.kwargs['start_new_session'])

    def test_visual_rejects_outside_and_missing_evidence(self):
        for args in [{'evidence_path': '/etc/passwd'}, {'evidence_path': '/media/working/references/missing.json'},
                     {'evidence_path': '/media/working/references/a.json', 'prompt': 'override'}]:
            self.assertIn('error', json.loads(p.visual(args)))

    def test_visual_uses_only_local_sheet_saves_observations_and_caches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / 'working'
            folder.mkdir()
            sheet = folder / 'contact-sheet.jpg'
            sheet.write_bytes(b'jpeg')
            evidence = folder / 'evidence.json'
            evidence.write_text(json.dumps({'source_url': 'https://instagram.com/reel/a/',
                                            'contact_sheet_path': str(sheet), 'frames': [{'seconds': 0}]}))
            with patch.object(p, 'WORKING', root), patch.object(p, 'vision_request', return_value={'observations': 'Visible title', 'usage': {}}) as req:
                first = json.loads(p.visual({'evidence_path': str(evidence)}))
                self.assertEqual(first['observations'], 'Visible title')
                self.assertTrue(Path(first['artifact_path']).is_file())
                self.assertTrue(json.loads(p.visual({'evidence_path': str(evidence)}))['cached'])
                self.assertEqual(req.call_count, 1)

    def test_vision_request_fixed_endpoint_credential_and_sanitized_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            sheet = Path(tmp) / 'sheet.jpg'
            sheet.write_bytes(b'jpeg')
            response = io.BytesIO(json.dumps({'choices': [{'message': {'content': 'observed'}}], 'usage': {'total_tokens': 10}}).encode())
            with patch.dict(os.environ, {'NVIDIA_API_KEY': 'synthetic-sentinel'}), patch.object(p, 'urlopen', return_value=response) as request:
                result = p.vision_request(sheet, [{'seconds': 0}])
                self.assertEqual(result['observations'], 'observed')
                self.assertEqual(request.call_args.args[0].full_url, 'https://integrate.api.nvidia.com/v1/chat/completions')
            with patch.dict(os.environ, {'NVIDIA_API_KEY': 'synthetic-sentinel'}), patch.object(p, 'urlopen', side_effect=RuntimeError('secret-sentinel')):
                with self.assertRaises(RuntimeError) as error:
                    p.vision_request(sheet, [{'seconds': 0}])
                self.assertNotIn('secret-sentinel', str(error.exception))
            with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
                p.vision_request(sheet, [{'seconds': 0}])


if __name__ == '__main__':
    unittest.main()
