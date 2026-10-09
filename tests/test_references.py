"""Synthetic security and workflow tests; no live search, inference or task queue."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(os.environ.get('BRAND_REFERENCE_TEST_ROOT', Path(__file__).resolve().parents[1]))
spec = importlib.util.spec_from_file_location('references', ROOT / 'scripts/reference-worker.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class ReferencesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.media = self.base / 'media'
        self.vault = self.base / 'vault'
        self.media.mkdir()
        self.vault.mkdir()
        self.patches = [patch.object(r, 'MEDIA', self.media), patch.object(r, 'VAULT', self.vault)]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def test_canonical_urls(self):
        self.assertEqual(r.canonical_url('https://www.instagram.com/reel/ABC-12_/?igsh=x'),
                         'https://www.instagram.com/reel/ABC-12_/')
        self.assertEqual(r.canonical_url('https://youtu.be/abcdefghijk?t=1'),
                         'https://www.youtube.com/watch?v=abcdefghijk')
        self.assertEqual(r.canonical_url('https://www.youtube.com/shorts/abcdefghijk'),
                         'https://www.youtube.com/watch?v=abcdefghijk')

    def test_reject_untrusted_urls(self):
        for url in ['http://instagram.com/reel/a/', 'file:///etc/passwd',
                    'https://instagram.com.evil.test/reel/a/', 'https://127.0.0.1/reel/a/',
                    'https://user:password@instagram.com/reel/a/',
                    'https://instagram.com:8443/reel/a/', 'https://instagram.com/someone/',
                    'https://youtube.com/playlist?list=abc', 'https://youtu.be/bad',
                    'https://instagram.com/reel/a/../../secret', 'https://instagram.com/reel/a/#x']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                r.canonical_url(url)

    def test_search_filters_deduplicates_and_saves_attribution(self):
        rows = [{'title': 'Example', 'href': 'https://instagram.com/reel/ABC/?x=1', 'body': 'snippet'},
                {'href': 'https://www.instagram.com/reel/ABC/'},
                {'href': 'https://evil.test/'}, {'href': 'https://youtube.com/shorts/abcdefghijk'}]
        with patch.object(r, 'search_backend', return_value=rows):
            result = r.search('AI workflows', 'instagram', 3)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['evidence_status'], 'search-snippet-only')
        self.assertTrue(Path(result['artifact_path']).is_file())
        self.assertIn('retrieved_at', result)

    def test_search_empty_is_not_claimed_as_analysis(self):
        with patch.object(r, 'search_backend', return_value=[]):
            result = r.search('AI workflows', 'youtube', 1)
        self.assertEqual(result['results'], [])
        self.assertIn('not', result['limits'])

    def test_search_bounds(self):
        for args in [('', 'instagram', 2), ('x'*241, 'instagram', 2),
                     ('x', 'tiktok', 2), ('x', 'instagram', 0), ('x', 'instagram', 11),
                     ('x', 'instagram', True)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                r.search(*args)

    def test_path_rejects_escape_symlink_and_large_media(self):
        outside = self.base / 'outside.mp4'
        outside.write_bytes(b'x')
        (self.media / 'link.mp4').symlink_to(outside)
        for path in [outside, self.media / 'link.mp4', self.media / '../outside.mp4']:
            with self.assertRaises(ValueError):
                r.local_media(str(path))
        inside = self.media / 'large.mp4'
        inside.write_bytes(b'x' * 20)
        with patch.object(r, 'MAX_BYTES', 10), self.assertRaises(ValueError):
            r.local_media(str(inside))
        with self.assertRaises(ValueError):
            r.local_media('relative.mp4')

    def test_probe_enforces_duration_dimensions_and_video(self):
        path = self.media / 'good.mp4'
        path.write_bytes(b'x')
        for data in [{'format': {'duration': '181'}, 'streams': [{'codec_type': 'video'}]},
                     {'format': {'duration': 'nan'}, 'streams': [{'codec_type': 'video'}]},
                     {'format': {'duration': '3'}, 'streams': []},
                     {'format': {'duration': '3'}, 'streams': [{'codec_type': 'video', 'width': 5000}]}]:
            with patch.object(r, 'command', return_value=json.dumps(data)), self.assertRaises(ValueError):
                r.probe(path)
        good = {'format': {'duration': '3'}, 'streams': [{'codec_type': 'video', 'width': 640, 'height': 480}]}
        with patch.object(r, 'command', return_value=json.dumps(good)):
            self.assertEqual(r.probe(path)['duration'], 3)

    def test_fetch_success_cache_and_failed_download_cleanup(self):
        def download(url, folder):
            path = folder / 'reference.mp4'
            path.write_bytes(b'video')
            return path, {'title': 'Actual source', 'view_count': None, 'creator': 'creator'}
        with patch.object(r, 'download', side_effect=download) as mock, patch.object(r, 'probe', return_value={'duration': 10}):
            result = r.fetch('https://instagram.com/reel/ABC/')
            again = r.fetch('https://instagram.com/reel/ABC/?x=1')
            self.assertEqual(result['media_path'], again['media_path'])
            self.assertTrue(again['cached'])
            self.assertEqual(mock.call_count, 1)
        with patch.object(r, 'download', side_effect=RuntimeError('blocked')), self.assertRaises(RuntimeError):
            r.fetch('https://instagram.com/reel/DEF/')
        self.assertFalse(list((self.media / 'incoming/references').glob('.stage-*')))

    def test_fetch_corrupt_cache_is_rejected(self):
        folder = self.media / 'incoming/references' / r.identity('https://www.instagram.com/reel/ABC/')
        folder.mkdir(parents=True)
        (folder / 'source.json').write_text(json.dumps({'media_path': '/etc/passwd'}))
        with self.assertRaises(ValueError):
            r.fetch('https://instagram.com/reel/ABC/')

    def test_prepare_preserves_partial_evidence_and_caches(self):
        path = self.media / 'reference.mp4'
        path.write_bytes(b'real fixture bytes')
        def frames(p, dest, duration):
            (dest / 'contact-sheet.jpg').write_bytes(b'jpeg')
            return [{'seconds': 0, 'file': 'frame-00.jpg'}]
        with patch.object(r, 'probe', return_value={'duration': 3, 'audio': True}), \
             patch.object(r, 'extract_frames', side_effect=frames), \
             patch.object(r, 'transcribe', side_effect=RuntimeError('missing model')):
            result = r.prepare(str(path), 'https://instagram.com/reel/ABC/')
            self.assertEqual(result['transcript_status'], 'unavailable')
            self.assertIn('missing model', result['transcript_error'])
            self.assertTrue(Path(result['evidence_path']).is_file())
            self.assertTrue(r.prepare(str(path), 'https://instagram.com/reel/ABC/')['cached'])

    def test_prepare_transcript_and_silent_clip(self):
        path = self.media / 'reference.mp4'
        path.write_bytes(b'fixture')
        with patch.object(r, 'probe', return_value={'duration': 3, 'audio': True}), \
             patch.object(r, 'extract_frames', return_value=[]), \
             patch.object(r, 'transcribe', return_value={'segments': [{'start': 0, 'end': 1, 'text': 'hello'}], 'language': 'en'}):
            result = r.prepare(str(path), None)
            self.assertEqual(result['transcript_status'], 'machine-transcribed')
            self.assertIn('hello', Path(result['artifact_path']).read_text())
        path.write_bytes(b'different')
        with patch.object(r, 'probe', return_value={'duration': 3, 'audio': False}), \
             patch.object(r, 'extract_frames', return_value=[]), patch.object(r, 'transcribe') as mock:
            self.assertEqual(r.prepare(str(path), None)['transcript_status'], 'no-audio')
            mock.assert_not_called()

    def test_private_destination_dns_rejected(self):
        for ip in ['127.0.0.1', '10.0.0.1', '169.254.169.254', '::1']:
            with patch.object(r, 'ORIGINAL_GETADDRINFO', return_value=[(2, 1, 6, '', (ip, 443))]), self.assertRaises(ValueError):
                r.public_getaddrinfo('example.com', 443)

    def test_dispatch_rejects_unknown_fields_and_actions(self):
        for payload in [{'action': 'shell', 'command': 'id'}, {'action': 'fetch', 'url': 'x', 'cookies': '/secret'}]:
            with self.assertRaises(ValueError):
                r.dispatch(payload)

    def test_command_error_and_success(self):
        with patch.object(r.subprocess, 'run', return_value=types.SimpleNamespace(returncode=0, stdout='data')):
            self.assertEqual(r.command(['ffprobe']), 'data')
        with patch.object(r.subprocess, 'run', return_value=types.SimpleNamespace(returncode=1)), self.assertRaises(RuntimeError):
            r.command(['ffprobe'])

    def test_download_backend_enforces_public_cdn_single_video_and_byte_limit(self):
        folder = self.media / 'download'
        folder.mkdir()
        class YDL:
            info = {'url': 'https://video.cdninstagram.com/file.mp4', 'id': 'abc', 'title': 'title'}
            def __init__(self, opts):
                self.opts = opts
                YDL.opts = opts
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def extract_info(self, *args, **kwargs):
                return self.info
            def process_info(self, info):
                (folder / 'reference.mp4').write_bytes(b'video')
        with patch.dict(sys.modules, {'yt_dlp': types.SimpleNamespace(YoutubeDL=YDL)}):
            media, meta = r.download('https://instagram.com/reel/abc/', folder)
            self.assertTrue(media.is_file())
            self.assertIsNone(meta['view_count'])
            self.assertNotIn('cookiefile', YDL.opts)
            with self.assertRaises(ValueError):
                YDL.opts['progress_hooks'][0]({'downloaded_bytes': r.MAX_BYTES + 1})
            self.assertIn('180', YDL.opts['match_filter']({'duration': 181}))
            self.assertIn('unsupported', YDL.opts['match_filter']({'is_live': True}))
            for info in [{'_type': 'playlist'}, {'url': 'http://video.cdninstagram.com/f.mp4'},
                         {'url': 'https://evil.test/f.mp4'}, None]:
                YDL.info = info
                with self.assertRaises(ValueError):
                    r.download('https://instagram.com/reel/abc/', folder)

    def test_transcribe_uses_pinned_local_model_and_cleans_audio(self):
        model = self.base / 'model'
        model.mkdir()
        (model / 'model.bin').write_bytes(b'fixture')
        folder = self.media / 'transcription'
        folder.mkdir()
        def extract(args, timeout=30):
            (folder / 'audio.wav').write_bytes(b'fixture')
        instance = types.SimpleNamespace(transcribe=lambda *a, **kw: (
            iter([types.SimpleNamespace(start=0, end=1, text=' hello ')]),
            types.SimpleNamespace(language='en', language_probability=.9)))
        with patch.object(r, 'MODEL', model), patch.object(r, 'command', side_effect=extract), \
             patch.dict(sys.modules, {'faster_whisper': types.SimpleNamespace(WhisperModel=lambda *a, **kw: instance)}):
            result = r.transcribe(self.media / 'video.mp4', folder)
            self.assertEqual(result['segments'][0]['text'], 'hello')
            self.assertFalse((folder / 'audio.wav').exists())
        with patch.object(r, 'MODEL', model / 'missing'), self.assertRaises(RuntimeError):
            r.transcribe(self.media / 'video.mp4', folder)

    def test_frame_extraction_creates_timed_contact_sheet_and_handles_failure(self):
        folder = self.media / 'frames'
        folder.mkdir()
        def extract(args, timeout=30):
            Path(args[-1]).write_bytes(b'jpeg')
        with patch.object(r, 'command', side_effect=extract):
            frames = r.extract_frames(self.media / 'video.mp4', folder, 45)
        self.assertTrue((folder / 'contact-sheet.jpg').is_file())
        self.assertEqual(len(frames), 12)
        for file in folder.iterdir():
            file.unlink()
        with patch.object(r, 'command'), self.assertRaises(RuntimeError):
            r.extract_frames(self.media / 'video.mp4', folder, 45)

    def test_dispatch_routes_only_reference_operations(self):
        with patch.object(r, 'search', return_value={}) as search, patch.object(r, 'fetch', return_value={}) as fetch, patch.object(r, 'prepare', return_value={}) as prepare:
            r.dispatch({'action': 'search', 'query': 'AI'})
            r.dispatch({'action': 'fetch', 'url': 'URL'})
            r.dispatch({'action': 'prepare', 'media_path': '/media/video.mp4'})
            search.assert_called_once()
            fetch.assert_called_once()
            prepare.assert_called_once()

    def test_operator_cli_preserves_literal_inputs(self):
        self.assertEqual(r.cli_payload(['search', 'AI; $(id)']), {'action': 'search', 'query': 'AI; $(id)', 'platform': 'instagram'})
        self.assertEqual(r.cli_payload(['fetch', 'URL']), {'action': 'fetch', 'url': 'URL'})
        self.assertEqual(r.cli_payload(['prepare', '/media/a.mp4', 'URL'])['source_url'], 'URL')
        with self.assertRaises(ValueError):
            r.cli_payload(['shell', 'id'])

    def test_timestamps_include_opening_and_end(self):
        times = r.frame_times(45)
        self.assertEqual(times[:3], [0.0, 1.0, 3.0])
        self.assertLessEqual(len(times), 12)
        self.assertGreater(times[-1], 40)
        self.assertLess(max(r.frame_times(.5)), .5)


if __name__ == '__main__':
    unittest.main()
