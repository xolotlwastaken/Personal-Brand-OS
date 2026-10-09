"""Synthetic transport/session fixtures; no Docker or model calls."""
import unittest
from unittest.mock import patch
import subprocess
import sys
import time
from dashboard.live import BridgeClient, ChatClient, LiveError, RPCProcess, public_event


class FakeRPC:
    def __init__(self):
        self.calls = []
        self.listener = None

    def call(self, method, params):
        self.calls.append((method, params))
        if method in {'session.create', 'session.resume'}:
            return {'session_id': 'runtime-1', 'stored_session_id': 'stored-1',
                    'messages': [{'role': 'assistant', 'text': 'Synthetic reply',
                                  'reasoning': 'Private fixture'}]}
        return {'status': 'streaming'}

    def close(self):
        pass


class ChatTests(unittest.TestCase):
    def setUp(self):
        self.rpc = FakeRPC()
        self.source = 'api_server'
        self.chat = ChatClient({'brand-ceo', 'brand-manager'}, self.rpc,
                               lambda p: {'session': {'source': self.source}, 'messages': []})

    def test_create_forces_profile_workspace_and_native_tool_surface(self):
        result = self.chat.open('brand-manager')
        method, params = self.rpc.calls[-1]
        self.assertEqual(method, 'session.create')
        self.assertEqual(params['profile'], 'brand-manager')
        self.assertEqual(params['cwd'], '/knowledge')
        self.assertEqual(params['source'], 'api_server')
        self.assertNotIn('reasoning', str(result))
        self.assertEqual(result['session_id'], 'runtime-1')

    def test_resume_cannot_take_over_worker_or_other_profile(self):
        self.source = 'kanban'
        with self.assertRaises(LiveError):
            self.chat.open('brand-ceo', 'stored-1')
        self.assertEqual(self.rpc.calls, [])
        self.source = 'api_server'
        self.chat.open('brand-ceo', 'stored-1')
        with self.assertRaises(LiveError):
            self.chat.send('brand-manager', 'runtime-1', 'Synthetic message')

    def test_unknown_profiles_and_messages_rejected(self):
        for profile in ('default', '../../brand-ceo', None):
            with self.assertRaises(LiveError):
                self.chat.open(profile)
        self.chat.open('brand-ceo')
        for body in ('', 'x' * 12001, {'text': 'invalid'}, '/model unsafe'):
            with self.assertRaises(LiveError):
                self.chat.send('brand-ceo', 'runtime-1', body)
        for sid in (None, {}, [], ''):
            with self.assertRaises(LiveError):
                self.chat.state('brand-ceo', sid)

    def test_stream_busy_and_profile_isolation(self):
        self.chat.open('brand-ceo')
        self.chat.send('brand-ceo', 'runtime-1', 'Synthetic message')
        with self.assertRaises(LiveError):
            self.chat.send('brand-ceo', 'runtime-1', 'duplicate while busy')
        self.rpc.listener({'type': 'message.delta', 'session_id': 'runtime-1',
                           'payload': {'text': 'Synthetic token', 'reasoning': 'private'}})
        self.rpc.listener({'type': 'reasoning.delta', 'session_id': 'runtime-1',
                           'payload': {'text': 'private'}})
        events = self.chat.events('brand-ceo', 'runtime-1', 0, timeout=0)
        self.assertEqual(len(events), 1)
        self.assertNotIn('reasoning', str(events))
        with self.assertRaises(LiveError):
            self.chat.events('brand-manager', 'runtime-1', 0, timeout=0)
        self.rpc.listener({'type': 'message.complete', 'session_id': 'runtime-1',
                           'payload': {'text': 'Synthetic token', 'status': 'complete'}})
        self.assertFalse(self.chat.state('brand-ceo', 'runtime-1')['running'])
        self.chat.send('brand-ceo', 'runtime-1', 'Next synthetic turn')

    def test_bounded_replay_detects_missing_events(self):
        self.chat.open('brand-ceo')
        for i in range(600):
            self.rpc.listener({'type': 'message.delta', 'session_id': 'runtime-1',
                               'payload': {'text': str(i)}})
        replay = self.chat.events('brand-ceo', 'runtime-1', 1, timeout=0)
        self.assertEqual(replay[0]['type'], 'stream.reset')
        self.assertLessEqual(len(replay), 513)

    def test_public_fields_only(self):
        self.assertIsNone(public_event({'type': 'thinking.delta', 'payload': {'text': 'private'}}))
        event = public_event({'type': 'tool.complete', 'session_id': 'r',
                              'payload': {'name': 'read_file', 'result': 'Synthetic content',
                                          'reasoning': 'private', 'rendered': 'untrusted html'}})
        self.assertEqual(event['payload'], {'name': 'read_file', 'result': 'Synthetic content'})

    def test_native_failures_preserve_retry_safety(self):
        self.chat.open('brand-ceo')
        with patch.object(self.rpc, 'call', side_effect=LiveError('Timeout', 503)):
            with self.assertRaises(LiveError):
                self.chat.send('brand-ceo', 'runtime-1', 'Synthetic uncertain delivery')
        with self.assertRaises(LiveError):
            self.chat.send('brand-ceo', 'runtime-1', 'Do not duplicate this')
        self.rpc.listener({'type': 'message.complete', 'session_id': 'runtime-1',
                           'payload': {'text': 'Recovered synthetic reply', 'status': 'complete'}})
        self.chat.send('brand-ceo', 'runtime-1', 'Next confirmed turn')
        self.rpc.listener({'type': 'transport.closed'})
        with self.assertRaises(LiveError):
            self.chat.send('brand-ceo', 'runtime-1', 'Cannot send on dead process')
        self.assertEqual(self.chat.events('brand-ceo', 'runtime-1', 0, timeout=0)[-1]['type'], 'error')

    def test_long_event_results_are_bounded(self):
        self.chat.open('brand-ceo')
        for i in range(50):
            self.rpc.listener({'type': 'tool.complete', 'session_id': 'runtime-1',
                               'payload': {'name': 'synthetic', 'result': 'x' * 200000}})
        events = self.chat.events('brand-ceo', 'runtime-1', 0, timeout=0)
        self.assertLess(len(str(events)), 2100000)
        self.assertEqual(events[0]['type'], 'stream.reset')

    def test_resume_reconciles_native_busy_without_overwriting_new_events(self):
        self.chat.open('brand-ceo')
        with patch.object(self.rpc, 'call', return_value={
                'session_id': 'runtime-1', 'running': True}):
            self.assertTrue(self.chat.open('brand-ceo', 'stored-1')['running'])
        with self.assertRaises(LiveError):
            self.chat.send('brand-ceo', 'runtime-1', 'Do not queue duplicate')
        def completing_resume(*args):
            self.rpc.listener({'type': 'message.complete', 'session_id': 'runtime-1',
                               'payload': {'text': 'Synthetic finished', 'status': 'complete'}})
            return {'session_id': 'runtime-1', 'running': True}
        with patch.object(self.rpc, 'call', side_effect=completing_resume):
            self.assertFalse(self.chat.open('brand-ceo', 'stored-1')['running'])


class TransportTests(unittest.TestCase):
    def launch_fixture(self, code):
        real_popen = subprocess.Popen
        def launch(*args, **kwargs):
            kwargs.pop('cwd', None)
            return real_popen([sys.executable, '-u', '-c', code], **kwargs)
        patcher = patch('dashboard.live.subprocess.Popen', side_effect=launch)
        patcher.start(); self.addCleanup(patcher.stop)
        rpc = RPCProcess('synthetic.py'); self.addCleanup(rpc.close)
        return rpc

    def test_warm_transport_events_and_native_errors(self):
        rpc = self.launch_fixture('''
import json,sys
print('synthetic non-JSON startup noise')
print('[]')
for line in sys.stdin:
    req=json.loads(line)
    if req['method']=='bad':
        print(json.dumps({'id':req['id'],'error':{'message':'Synthetic native refusal'}}))
    else:
        print(json.dumps({'method':'event','params':{'type':'message.delta','payload':{'text':'Synthetic'}}}))
        print(json.dumps({'id':req['id'],'result':{'ok':True}}))
''')
        events = []; rpc.listener = events.append
        self.assertEqual(rpc.call('ping', {}), {'ok': True})
        pid = rpc.process.pid
        self.assertEqual(rpc.call('ping', {}), {'ok': True})
        self.assertEqual(pid, rpc.process.pid)
        self.assertEqual(len(events), 2)
        with self.assertRaisesRegex(LiveError, 'Synthetic native refusal'):
            rpc.call('bad', {})
        client = BridgeClient()
        client.rpc = rpc
        self.assertEqual(client({'op': 'synthetic'}), {'ok': True})
        client.close()

    def test_transport_exit_and_timeout_do_not_replay(self):
        rpc = self.launch_fixture('''
import sys,time,json
for line in sys.stdin:
    req=json.loads(line)
    if req['method']=='exit': sys.exit(0)
    time.sleep(1)
    print(json.dumps({'id':req['id'],'result':{}}))
''')
        with self.assertRaisesRegex(LiveError, 'in time'):
            rpc.call('slow', {}, timeout=0.02)
        self.assertEqual(rpc.pending, {})
        time.sleep(1.05)
        with self.assertRaisesRegex(LiveError, 'closed'):
            rpc.call('exit', {})

    def test_missing_docker_is_reported(self):
        with patch('dashboard.live.subprocess.Popen', side_effect=OSError):
            with self.assertRaises(LiveError):
                RPCProcess('synthetic.py').call('ping', {})


if __name__ == '__main__':
    unittest.main(verbosity=2)
