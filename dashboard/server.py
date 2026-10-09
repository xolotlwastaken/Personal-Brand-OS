"""Loopback-only web dashboard; requires Python 3.10+ and the Docker CLI on host."""
import argparse
from collections import deque
import json
import mimetypes
import re
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dashboard.live import BridgeClient, ChatClient, LiveError
STATIC = ROOT / 'dashboard' / 'static'
VAULT = ROOT / 'knowledge'
ROLES = json.loads((ROOT / 'config/agents.json').read_text())


class ApiError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def bridge(payload):
    try:
        result = subprocess.run(
            ['docker', 'compose', 'exec', '-T', '--user', 'hermes', 'hermes',
             '/opt/hermes/.venv/bin/python', '/project/scripts/dashboard-bridge.py'],
            cwd=ROOT, input=json.dumps(payload), capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        raise ApiError(503, 'Hermes is unavailable. Check Docker and the container, then refresh.')
    try:
        data = json.loads(result.stdout)
    except ValueError:
        raise ApiError(503, 'Hermes is unavailable. Check Docker and the container, then refresh.')
    if result.returncode or data.get('error'):
        raise ApiError(400 if result.returncode == 2 else 503,
                       data.get('error', 'The native Hermes operation failed.'))
    return data


def vault_path(relative):
    if not isinstance(relative, str) or len(relative) > 500:
        raise ApiError(400, 'Invalid artifact path')
    candidate = VAULT / relative
    if Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ApiError(403, 'Artifact paths must be relative to the knowledge vault')
    if candidate.is_symlink() or candidate.resolve().is_relative_to(VAULT.resolve()) is False:
        raise ApiError(403, 'Artifact must stay inside the knowledge vault')
    if any(part.startswith('.') for part in Path(relative).parts) or candidate.suffix != '.md':
        raise ApiError(403, 'Only vault Markdown artifacts are available')
    return candidate


def artifacts():
    files = []
    if VAULT.exists():
        for p in VAULT.rglob('*.md'):
            try:
                relative = str(p.relative_to(VAULT))
                safe = vault_path(relative)
                if safe.is_file():
                    stat = safe.stat()
                    with safe.open() as stream:
                        preview = stream.read(4096)
                    heading = re.search(r'^# (.+)$', preview, re.MULTILINE)
                    fixture = ('validation-fixtures' in safe.parts or
                               safe.name.startswith('verification-') or
                               bool(re.search(r'^status:\s*[\'"]?synthetic', preview, re.MULTILINE)))
                    files.append({'path': relative, 'name': p.stem,
                                  'title': heading[1][:160] if heading else p.stem.replace('-', ' '),
                                  'synthetic': fixture,
                                  'modified_at': stat.st_mtime, 'bytes': stat.st_size})
            except (ApiError, OSError, UnicodeError):
                continue
    return sorted(files, key=lambda f: f['modified_at'], reverse=True)[:500]


def brand_state():
    """Display only canonical strategy metadata; fixtures are never brand evidence."""
    state = {'state': 'missing', 'label': 'Strategy needs discovery', 'path': None}
    try:
        p = vault_path('brand/strategy.md')
        if not p.is_file():
            return state
        with p.open() as stream:
            content = stream.read(4096)
        frontmatter = content.split('---', 2)[1] if content.startswith('---\n') else ''
        fields = dict(re.findall(r'^(status|approval):\s*[\'"]?([\w-]+)', frontmatter, re.MULTILINE))
        state['path'] = 'brand/strategy.md'
        if fields.get('status') == 'approved' and fields.get('approval') == 'human-approved':
            state.update(state='approved', label='Human-approved strategy')
        elif fields.get('status') == 'review':
            state.update(state='review', label='Strategy awaiting your review')
        else:
            state.update(state='discovery', label='Starting draft · discovery needed')
    except (ApiError, OSError, UnicodeError, IndexError):
        pass
    return state


class DashboardServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port, adapter=None):
        super().__init__(('127.0.0.1', port), Handler)
        self.token = secrets.token_urlsafe(32)
        self.adapter = adapter if adapter is not None else BridgeClient()
        self.chat = ChatClient(ROLES, reader=self.adapter)
        self.lock = threading.Lock()
        self.snapshot_cache = {}
        self.api_slots = threading.BoundedSemaphore(3)
        self.requests = deque()
        self.reply_lock = threading.Lock()
        self.stream_slots = threading.BoundedSemaphore(8)

    def server_close(self):
        super().server_close()
        self.chat.close()
        if isinstance(self.adapter, BridgeClient):
            self.adapter.close()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass  # Task briefs, notes and vault paths never go into HTTP logs.

    def respond(self, status, body, content_type='application/json; charset=utf-8'):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; "
                         "style-src 'self'; img-src 'self' data:; connect-src 'self'; "
                         "frame-ancestors 'none'; form-action 'self'; base-uri 'none'")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def validate_site(self, write=False):
        port = self.server.server_port
        allowed = {f'127.0.0.1:{port}', f'localhost:{port}'}
        if self.headers.get('Host') not in allowed:
            raise ApiError(403, 'Only localhost access is allowed')
        origin = self.headers.get('Origin')
        if origin and origin not in {f'http://{host}' for host in allowed}:
            raise ApiError(403, 'Cross-origin access is disabled')
        if self.headers.get('Sec-Fetch-Site') == 'cross-site':
            raise ApiError(403, 'Cross-site access is disabled')
        if write and not secrets.compare_digest(self.headers.get('X-Dashboard-Token', ''), self.server.token):
            raise ApiError(403, 'Refresh the dashboard before submitting this request')

    def api(self, payload):
        if not self.server.api_slots.acquire(blocking=False):
            raise ApiError(429, 'Dashboard is busy. Try again in a moment.')
        try:
            return self.server.adapter(payload)
        finally:
            self.server.api_slots.release()

    def chat_stream(self, params):
        profile, sid = params.get('profile', [''])[0], params.get('session', [''])[0]
        raw_cursor = self.headers.get('Last-Event-ID') or params.get('after', ['0'])[0]
        if not re.fullmatch(r'\d{1,10}', raw_cursor):
            raise ApiError(400, 'Invalid stream cursor')
        after = int(raw_cursor)
        self.server.chat.state(profile, sid)  # Validate ownership before sending headers.
        if not self.server.stream_slots.acquire(blocking=False):
            raise ApiError(429, 'Too many open chat streams. Close an unused tab.')
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.connection.settimeout(12)
            until = time.monotonic() + 50
            while time.monotonic() < until:
                events = self.server.chat.events(profile, sid, after)
                for event in events:
                    self.wfile.write(f"id: {event['id']}\ndata: {json.dumps(event)}\n\n".encode())
                    after = event['id']
                self.wfile.write(b': heartbeat\n\n')
                self.wfile.flush()
        except (OSError, LiveError):
            pass
        finally:
            self.server.stream_slots.release()

    def do_GET(self):
        try:
            self.validate_site()
            url = urlsplit(self.path)
            params = parse_qs(url.query)
            if url.path == '/api/bootstrap':
                return self.respond(200, {'token': self.server.token})
            if url.path == '/api/chat/events':
                return self.chat_stream(params)
            if url.path == '/api/chat/state':
                return self.respond(200, self.server.chat.state(params.get('profile', [''])[0],
                                                               params.get('session', [''])[0]))
            if url.path in {'/api/conversations', '/api/conversation'}:
                payload = {'op': url.path.split('/')[-1], 'profile': params.get('profile', [''])[0]}
                if url.path == '/api/conversation':
                    payload['session_id'] = params.get('id', [''])[0]
                return self.respond(200, self.api(payload))
            if url.path == '/api/snapshot':
                filters = {k: params[k][0] for k in ('assignee', 'tenant', 'status') if params.get(k)}
                key = json.dumps(filters, sort_keys=True)
                with self.server.lock:
                    cached = self.server.snapshot_cache.get(key)
                if cached and time.monotonic() - cached[0] < 8:
                    return self.respond(200, cached[1])
                data = self.api({'op': 'snapshot', **filters})
                data['artifacts'] = artifacts()
                data['updated_at'] = time.time()
                with self.server.lock:
                    if len(self.server.snapshot_cache) > 40:
                        self.server.snapshot_cache.clear()
                    self.server.snapshot_cache[key] = (time.monotonic(), data)
                return self.respond(200, data)
            if url.path == '/api/task':
                return self.respond(200, self.api({'op': 'detail', 'task_id': params.get('id', [''])[0]}))
            if url.path == '/api/ceo':
                data = self.api({'op': 'ceo_thread'})
                data['brand_state'] = brand_state()
                return self.respond(200, data)
            if url.path == '/api/artifact':
                p = vault_path(params.get('path', [''])[0])
                if not p.is_file():
                    raise ApiError(404, 'Artifact no longer exists')
                if p.stat().st_size > 256000:
                    raise ApiError(413, 'Artifact exceeds the 256 KB preview limit')
                return self.respond(200, {'path': str(p.relative_to(VAULT)), 'content': p.read_text()})
            if url.path == '/api/skill':
                name = params.get('name', [''])[0]
                names = {s for role in ROLES.values() for s in role['skills']}
                if name not in names:
                    raise ApiError(404, 'Unknown project skill')
                return self.respond(200, {'name': name, 'content': (
                    ROOT / 'config/skills' / name / 'SKILL.md').read_text()})
            file = {'/': 'index.html', '/app.js': 'app.js', '/chat.js': 'chat.js',
                    '/style.css': 'style.css', '/chat.css': 'chat.css',
                    '/ceo-page.js': 'ceo-page.js', '/ceo-page.css': 'ceo-page.css'}.get(url.path)
            if file:
                return self.respond(200, (STATIC / file).read_bytes(),
                                    mimetypes.guess_type(file)[0] + '; charset=utf-8')
            raise ApiError(404, 'Page not found')
        except ApiError as exc:
            self.respond(exc.status, {'error': exc.message})
        except LiveError as exc:
            self.respond(exc.status, {'error': str(exc)})
        except (OSError, UnicodeError, ValueError):
            self.respond(500, {'error': 'Dashboard could not read this resource'})

    def do_POST(self):
        try:
            self.validate_site(write=True)
            if self.path != '/api/action':
                raise ApiError(404, 'Unknown action endpoint')
            if self.headers.get('Content-Type') != 'application/json':
                raise ApiError(415, 'JSON is required')
            length = int(self.headers.get('Content-Length', '0'))
            if length < 2 or length > 18000:
                raise ApiError(413, 'Request must be smaller than 18 KB')
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict) or payload.get('op') not in {
                'create', 'comment', 'unblock', 'request_changes', 'ceo_message', 'ceo_reply',
                'chat_open', 'chat_send'}:
                raise ApiError(400, 'Unknown dashboard action')
            now = time.monotonic()
            with self.server.lock:
                while self.server.requests and now - self.server.requests[0] > 60:
                    self.server.requests.popleft()
                if len(self.server.requests) >= 20:
                    raise ApiError(429, 'Too many actions. Wait a minute before submitting again.')
                self.server.requests.append(now)
            if payload['op'] == 'chat_open':
                result = self.server.chat.open(payload.get('profile'), payload.get('session_id', ''))
            elif payload['op'] == 'chat_send':
                result = self.server.chat.send(payload.get('profile'), payload.get('session_id'), payload.get('body'))
            elif payload['op'] == 'ceo_reply':
                with self.server.reply_lock:
                    result = self.api(payload)
            else:
                result = self.api(payload)
            with self.server.lock:
                self.server.snapshot_cache.clear()
            self.respond(200, result)
        except ApiError as exc:
            self.respond(exc.status, {'error': exc.message})
        except LiveError as exc:
            self.respond(exc.status, {'error': str(exc)})
        except (ValueError, UnicodeError):
            self.respond(400, {'error': 'Invalid JSON request'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    with DashboardServer(args.port) as server:
        print(f'Personal Brand OS → http://127.0.0.1:{server.server_port}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
