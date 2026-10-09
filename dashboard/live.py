"""Local transports for supported Hermes operations, never an execution queue."""
from collections import deque
import json
from pathlib import Path
import queue
import subprocess
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]


class LiveError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


EVENT_FIELDS = {
    'message.start': set(),
    'message.delta': {'text'},
    'message.interim': {'text', 'already_streamed'},
    'message.complete': {'text', 'status', 'warning', 'response_previewed'},
    'tool.start': {'tool_id', 'name', 'args', 'context'},
    'tool.complete': {'tool_id', 'name', 'args', 'result', 'summary', 'duration_s'},
    'tool.generating': {'name'},
    'session.title': {'title'},
    'error': {'message', 'text'},
}


def public_event(frame):
    kind = frame.get('type')
    if kind not in EVENT_FIELDS:
        return None
    payload = frame.get('payload') or {}
    public = {}
    for key, value in payload.items():
        if key not in EVENT_FIELDS[kind]:
            continue
        encoded = value if isinstance(value, str) else json.dumps(value)
        public[key] = encoded[:64000] + '\n[Display truncated]' if len(encoded) > 64000 else value
    return {'type': kind, 'session_id': frame.get('session_id'), 'payload': public}


class RPCProcess:
    """One warm Docker exec pipe. Native Hermes owns persistence and inference."""
    def __init__(self, script):
        self.script = script
        self.process = None
        self.listener = None
        self.lock = threading.Lock()
        self.pending = {}

    def _start(self):
        if self.process is not None and self.process.poll() is None:
            return
        try:
            self.process = subprocess.Popen(
                ['docker', 'compose', 'exec', '-T', '--user', 'hermes', 'hermes',
                 '/opt/hermes/.venv/bin/python', '-u', self.script, '--serve'],
                cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=True, bufsize=1)
        except OSError:
            raise LiveError('Hermes is unavailable. Check the container.', 503)
        threading.Thread(target=self._read, args=(self.process,), daemon=True).start()

    def _read(self, process):
        try:
            for line in process.stdout:
                try:
                    frame = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(frame, dict):
                    continue
                if frame.get('method') == 'event':
                    if self.listener:
                        self.listener(frame.get('params', {}))
                    continue
                with self.lock:
                    waiter = self.pending.pop(frame.get('id'), None)
                if waiter:
                    waiter.put(frame)
        finally:
            with self.lock:
                # A replacement process must not lose its own pending requests.
                if process is self.process:
                    waiters, self.pending = self.pending, {}
                else:
                    waiters = {}
            for waiter in waiters.values():
                waiter.put({'error': {'message': 'Hermes connection closed. Reopen the conversation.'}})
            if self.listener and process is self.process:
                self.listener({'type': 'transport.closed'})
            process.stdout.close()

    def call(self, method, params, timeout=30):
        rid = uuid.uuid4().hex
        waiter = queue.Queue(maxsize=1)
        with self.lock:
            self._start()
            self.pending[rid] = waiter
            try:
                self.process.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': rid,
                                                     'method': method, 'params': params}) + '\n')
                self.process.stdin.flush()
            except (OSError, ValueError):
                self.pending.pop(rid, None)
                raise LiveError('Hermes connection closed. Reopen the conversation.', 503)
        try:
            response = waiter.get(timeout=timeout)
        except queue.Empty:
            with self.lock:
                self.pending.pop(rid, None)
            # Never replay a mutation after an ambiguous timeout.
            raise LiveError('Hermes did not respond in time. Refresh before retrying.', 503)
        if response.get('error'):
            raise LiveError(response['error'].get('message', 'Native Hermes operation failed'))
        return response.get('result', {})

    def close(self):
        with self.lock:
            process = self.process
            if process and process.stdin:
                process.stdin.close()
        if process:
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.terminate()


class BridgeClient:
    def __init__(self):
        self.rpc = RPCProcess('/project/scripts/dashboard-bridge.py')

    def __call__(self, payload):
        return self.rpc.call('dispatch', payload)

    def close(self):
        self.rpc.close()


class ChatClient:
    def __init__(self, profiles, rpc=None, reader=None):
        self.profiles = set(profiles)
        self.rpc = rpc or RPCProcess('/project/scripts/dashboard-chat.py')
        self.reader = reader
        self.rpc.listener = self._event
        self.condition = threading.Condition(threading.RLock())
        self.sessions = {}
        self.open_lock = threading.Lock()

    def _profile(self, profile):
        if not isinstance(profile, str) or profile not in self.profiles:
            raise LiveError('Unknown project agent')

    def _owned(self, profile, sid, allow_disconnected=False):
        self._profile(profile)
        if not isinstance(sid, str) or not sid or len(sid) > 200:
            raise LiveError('Invalid live session ID')
        session = self.sessions.get(sid)
        if (not session or session['profile'] != profile or
                (session.get('disconnected') and not allow_disconnected)):
            raise LiveError('Reopen this agent conversation before sending or watching.', 409)
        return session

    def open(self, profile, stored_id=''):
        self._profile(profile)
        if not isinstance(stored_id, str) or len(stored_id) > 200:
            raise LiveError('Invalid session ID')
        with self.open_lock:
            with self.condition:
                sequences = {sid: row['sequence'] for sid, row in self.sessions.items()}
            if stored_id:
                row = self.reader({'op': 'conversation', 'profile': profile, 'session_id': stored_id})
                if row['session']['source'] != 'api_server':
                    raise LiveError('Worker and external chats are read-only. Start a separate direct chat.')
                result = self.rpc.call('session.resume', {'profile': profile, 'session_id': stored_id,
                                                          'source': 'api_server', 'lazy': True})
            else:
                result = self.rpc.call('session.create', {'profile': profile, 'cwd': '/knowledge',
                                                          'source': 'api_server',
                                                          'title': 'Dashboard conversation'})
            sid = result['session_id']
            with self.condition:
                if sid not in self.sessions:
                    self.sessions[sid] = {'profile': profile, 'stored_session_id':
                        result.get('stored_session_id') or result.get('session_key') or stored_id,
                        'running': bool(result.get('running')), 'uncertain': False,
                        'sequence': 0, 'events': deque(maxlen=512)}
                elif self.sessions[sid]['sequence'] == sequences.get(sid):
                    # Resume describes native state at request time. A completion
                    # event arriving during the RPC takes precedence over it.
                    self.sessions[sid]['running'] = bool(result.get('running'))
                self.sessions[sid]['uncertain'] = False
                state = self.state(profile, sid)
            # Select visible fields only; native resume payloads can contain reasoning.
            messages = [{'role': m['role'], 'content': m.get('text', m.get('content', ''))}
                        for m in result.get('messages', []) if m.get('role') in {'user', 'assistant', 'tool'}]
            inflight = result.get('inflight') or {}
            return {'session_id': sid, **state, 'messages': messages[-200:],
                    'inflight': {k: inflight[k] for k in ('assistant', 'streaming', 'error') if k in inflight}}

    def state(self, profile, sid):
        with self.condition:
            session = self._owned(profile, sid, allow_disconnected=True)
            return {k: session[k] for k in ('stored_session_id', 'running', 'sequence')}

    def send(self, profile, sid, body):
        if not isinstance(body, str) or not body.strip() or len(body) > 12000:
            raise LiveError('Message must contain 1–12000 characters')
        if body.lstrip().startswith('/'):
            raise LiveError('Use a conversational message here. Configuration slash commands are disabled.')
        with self.condition:
            session = self._owned(profile, sid)
            if session.get('uncertain'):
                raise LiveError('Delivery is unconfirmed. Reopen the saved conversation before retrying.', 409)
            if any(s['running'] for s in self.sessions.values()):
                raise LiveError('A direct chat is responding. Wait for it to finish.', 409)
            session['running'] = True
        try:
            result = self.rpc.call('prompt.submit', {'session_id': sid, 'text': body.strip()})
            if result.get('status') != 'streaming':
                raise LiveError('Hermes did not start this message. Reopen the conversation.', 409)
            return {'ok': True, 'status': 'streaming'}
        except LiveError as exc:
            with self.condition:
                session['running'] = False
                session['uncertain'] = exc.status == 503
            raise

    def _event(self, frame):
        with self.condition:
            if frame.get('type') == 'transport.closed':
                for sid, session in self.sessions.items():
                    self._append(session, {'type': 'error', 'session_id': sid,
                        'payload': {'message': 'Connection closed. Reopen to recover saved messages.'}})
                    session.update(running=False, disconnected=True)
                self.condition.notify_all()
                return
            event = public_event(frame)
            session = self.sessions.get(frame.get('session_id'))
            if not event or not session:
                return
            self._append(session, event)
            if event['type'] == 'message.start':
                session['running'] = True
            if event['type'] in {'message.complete', 'error'}:
                session['running'] = False
                session['uncertain'] = False
            self.condition.notify_all()

    @staticmethod
    def _append(session, event):
        session['sequence'] += 1
        events = session['events']
        total = session.get('event_bytes', 0)
        if len(events) == events.maxlen:
            total -= len(json.dumps(events.popleft()))
        item = {'id': session['sequence'], **event}
        events.append(item)
        total += len(json.dumps(item))
        # Bound bytes as well as count: large tool results cannot fill host memory.
        while total > 2_000_000:
            total -= len(json.dumps(events.popleft()))
        session['event_bytes'] = total

    def events(self, profile, sid, after, timeout=10):
        with self.condition:
            session = self._owned(profile, sid, allow_disconnected=True)
            if session['sequence'] <= after:
                self.condition.wait(timeout)
            found = [e for e in session['events'] if e['id'] > after]
            if found and found[0]['id'] > after + 1:
                found.insert(0, {'id': found[0]['id'] - 1, 'type': 'stream.reset', 'payload': {}})
            return found

    def close(self):
        self.rpc.close()
