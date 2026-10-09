"""Container-side dashboard adapter. Native Kanban tools own every task mutation."""
import json
import hashlib
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

os.environ['HERMES_HOME'] = '/opt/data/profiles/brand-ceo'
os.environ['HERMES_PROFILE'] = 'brand-ceo'

ROLES = json.loads(Path('/project/config/agents.json').read_text())
PROFILE_ROOT = Path('/opt/data/profiles')
TASK_ID = re.compile(r't_[a-zA-Z0-9]+\Z')
CEO_TENANT = 'brand-os-ceo'
CEO_CONTRACT = '''

CEO desk operator request. You are the user's primary contact. Delegate specialist work
through native Kanban; keep all resulting cards in tenant brand-os-ceo. Read your task
and any referenced prior conversation cards with kanban_show; read the canonical brand notes.
For personal brand setup or revision, delegate to Brand Manager. Starting drafts and
synthetic verification artifacts do not constitute a completed strategy. If discovery is
incomplete, ask Brand Manager for an evidence-gap assessment and at most three useful
interview questions per round. Brand Manager should complete that preparation card with
a saved question artifact so your dependent CEO follow-up can relay the questions.
When a strategy exists, clarify what the user wants to change or add before commissioning
revisions. Pass actual user answers to Brand Manager; never invent missing personal facts.
Create a separate CEO follow-up dependent on the producing specialist card, then complete
your current orchestration card once the graph exists. Do not wait inside your running
card or create a dependency on your unfinished current card. In the follow-up, present
questions directly to the user in a kanban_comment prefixed "CEO to you:" and block
needs_input with the concise question. The dashboard can persist their answer and resume
this CEO card. When resumed, read the operator comments and commission the next Brand
Manager round, with another dependent CEO follow-up. Keep your user-facing question,
result or update in a "CEO to you:" comment as well as your saved handoff artifact.
Human approval of a specific strategy proposal is required before Brand Manager updates
the canonical strategy. An answer, task completion or unblock is not approval. Drafts only;
publishing, DMs, bulk scraping, media generation and production rendering remain disabled.
Write task-ID artifacts in your owned /knowledge folder, validate and include artifact_paths
in the native completion handoff. Each new card must have workspace dir:/knowledge and
max_runtime_seconds=300. Use native Kanban only. No polling loops or custom task queue.
'''


def native(name, args):
    from tools.kanban_tools import registry
    result = json.loads(registry.get_entry(name).handler(args))
    if result.get('error'):
        raise ValueError(result['error'])
    return result


def usage(profile):
    path = PROFILE_ROOT / profile / 'state.db'
    if not path.is_file():
        return {'sessions': 0, 'api_calls': 0, 'input_tokens': 0,
                'output_tokens': 0, 'actual_cost_usd': None, 'recent_sessions': []}
    # Usage is informational only; execution state comes exclusively from native tools.
    with sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=2) as conn:
        conn.execute('PRAGMA query_only=ON')
        row = conn.execute('''SELECT count(*), coalesce(sum(api_call_count),0),
            coalesce(sum(input_tokens),0), coalesce(sum(output_tokens),0),
            CASE WHEN count(actual_cost_usd)=count(*) AND count(*)>0
            THEN sum(actual_cost_usd) ELSE NULL END FROM sessions''').fetchone()
        recent = conn.execute('''SELECT id, title, model, started_at, ended_at,
            message_count, source FROM sessions ORDER BY started_at DESC LIMIT 40''').fetchall()
    return dict(zip(('sessions', 'api_calls', 'input_tokens', 'output_tokens',
                     'actual_cost_usd'), row), recent_sessions=[dict(zip(
        ('id', 'title', 'model', 'started_at', 'ended_at', 'message_count', 'source'), r)) for r in recent])


def conversation(profile, sid):
    """Supported native session reads; never resume or mutate a worker to observe it."""
    if not isinstance(profile, str) or profile not in ROLES:
        raise ValueError('Unknown project agent')
    if not isinstance(sid, str) or not re.fullmatch(r'[a-zA-Z0-9_.:-]{1,200}', sid):
        raise ValueError('Invalid session ID')
    from hermes_state import SessionDB
    from agent.redact import redact_sensitive_text
    db = SessionDB(PROFILE_ROOT / profile / 'state.db', read_only=True)
    try:
        row = db.get_session(sid)
        if not row:
            raise ValueError('Session does not exist for this agent')
        tip = db.get_compression_tip(sid) or sid
        row = db.get_session(tip) or row
        messages = db.get_messages(tip, include_ancestors=True, limit=201, latest=True)
        visible = []
        for message in messages[-200:]:
            if message['role'] not in {'user', 'assistant', 'tool'} or message.get('display_kind') == 'hidden':
                continue
            item = {k: message[k] for k in ('id', 'role', 'content', 'tool_name', 'tool_call_id',
                                           'tool_calls', 'timestamp') if message.get(k) is not None}
            for key in ('content', 'tool_calls'):
                if key in item:
                    value = item[key]
                    if not isinstance(value, str):
                        value = json.dumps(value)
                    item[key] = redact_sensitive_text(value, force=True)[:64000]
            visible.append(item)
        return {'session': {k: row.get(k) for k in ('id', 'title', 'source', 'model',
                                                   'started_at', 'ended_at', 'message_count')},
                'messages': visible, 'truncated': len(messages) > 200}
    finally:
        db.close()


def text(value, field, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f'{field} must contain 1–{maximum} characters')
    return value.strip()


def task_id(value):
    if not isinstance(value, str) or not TASK_ID.fullmatch(value):
        raise ValueError('Invalid task ID')
    return value


def request_key(value):
    key = text(value, 'request key', 100)
    if not re.fullmatch(r'dashboard-[a-f0-9-]{36}', key):
        raise ValueError('Invalid request key')
    return key


def ceo_task(value):
    detail = native('kanban_show', {'task_id': task_id(value)})
    if detail['task']['assignee'] != 'brand-ceo' or detail['task']['tenant'] != CEO_TENANT:
        raise ValueError('Reply must refer to a card in your CEO conversation')
    return detail


def question(detail):
    for event in reversed(detail.get('events', [])):
        if event['kind'] in {'blocked', 'block_loop_detected'}:
            payload = event['payload']
            key = hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()[:20]
            return payload.get('reason', ''), payload.get('kind'), key
    return '', None, ''


def recovery_context(body):
    first = (body or '').splitlines()[:1]
    if first and first[0].startswith('Brand OS recovery: '):
        try:
            value = json.loads(first[0][len('Brand OS recovery: '):])
            if isinstance(value, dict):
                return value
        except ValueError:
            pass
    return {}


def dispatch(request):
    op = request.get('op')
    if op == 'conversation':
        return conversation(request.get('profile'), request.get('session_id'))
    if op == 'conversations':
        profile = request.get('profile')
        if not isinstance(profile, str) or profile not in ROLES:
            raise ValueError('Unknown project agent')
        return {'sessions': usage(profile)['recent_sessions']}
    if op == 'ceo_thread':
        board = native('kanban_list', {'assignee': 'brand-ceo', 'tenant': CEO_TENANT, 'limit': 50})
        tasks = []
        for card in board['tasks']:
            detail = native('kanban_show', {'task_id': card['id']})
            reason, kind, key = question(detail)
            recovery = recovery_context(detail['task']['body'])
            tasks.append({'task': detail['task'], 'parents': detail['parents'],
                          'recovery_origin_task_id': recovery.get('origin_task_id'),
                          'recovery_source_task_id': recovery.get('source_task_id'),
                          'children': detail['children'], 'runs': detail.get('runs', [])[-10:],
                          'creator_task_id': next((e['payload'].get('creator_task_id')
                              for e in detail.get('events', []) if e['kind'] == 'created'
                              and isinstance(e.get('payload'), dict)), None),
                          'comments': detail.get('comments', []),
                          'question': reason if card['status'] in {'blocked', 'triage'} else '',
                          'question_kind': kind if card['status'] == 'blocked' else None,
                          'question_key': key if card['status'] == 'blocked' else ''})
        return {'tasks': sorted(tasks, key=lambda d: (d['task']['created_at'], d['task']['id'])),
                'truncated': board.get('truncated', False)}
    if op == 'ceo_message':
        body = text(request.get('body'), 'Message', 12000)
        parents = []
        if request.get('reply_to'):
            previous = ceo_task(request['reply_to'])
            if previous['task']['status'] != 'done':
                raise ValueError('Wait for this CEO response, or answer its pending question')
            parents = [previous['task']['id']]
        return native('kanban_create', {
            'title': ('Continue CEO conversation: ' if parents else 'CEO request: ') + body.splitlines()[0][:160],
            'body': body + CEO_CONTRACT + (f'\nContinue prior CEO card {parents[0]}; read its questions and handoff.' if parents else ''),
            'assignee': 'brand-ceo', 'tenant': CEO_TENANT, 'parents': parents,
            'workspace_kind': 'dir', 'workspace_path': '/knowledge',
            'max_runtime_seconds': 300, 'priority': 0, 'triage': False,
            'idempotency_key': request_key(request.get('idempotency_key'))})
    if op == 'ceo_reply':
        key = request_key(request.get('idempotency_key'))
        body = text(request.get('body'), 'Answer', 12000)
        detail = ceo_task(request.get('task_id'))
        tid = detail['task']['id']
        prefix = f'Operator answer via CEO desk [{key}]'
        prior = next((c['body'] for c in detail.get('comments', []) if c['body'].startswith(prefix)), None)
        reason, kind, question_key = question(detail)
        if prior:
            if prior.split('\n\n', 1)[-1] != body:
                raise ValueError('This request key was already used for a different answer')
            if (detail['task']['status'] != 'blocked' or f'[question:{question_key}]' not in prior):
                return {'ok': True, 'task_id': tid, 'already_submitted': True}
        if detail['task']['status'] != 'blocked' or kind != 'needs_input' or detail['task']['current_run_id']:
            raise ValueError('Only a CEO card waiting for your input can be resumed here')
        if request.get('question_key') and request['question_key'] != question_key:
            raise ValueError('The CEO question changed. Refresh before answering')
        if not prior:
            native('kanban_comment', {'task_id': tid,
                   'body': f'{prefix} [question:{question_key}]\n\n{body}'})
        native('kanban_unblock', {'task_id': tid})
        return {'ok': True, 'task_id': tid}
    if op == 'snapshot':
        filters = {'limit': 200}
        for field in ('assignee', 'tenant', 'status'):
            if request.get(field):
                filters[field] = text(request[field], field, 100)
        if filters.get('assignee') and filters['assignee'] not in ROLES:
            raise ValueError('Unknown project profile')
        board = native('kanban_list', filters)
        for card in board['tasks']:
            if card['status'] not in {'done', 'archived', 'todo'}:
                detail = native('kanban_show', {'task_id': card['id']})
                runs = detail.get('runs', [])
                if runs:
                    card['last_outcome'] = runs[-1].get('outcome')
                    card['last_error'] = runs[-1].get('error')
        agents = []
        for profile, role in ROLES.items():
            try:
                stats = usage(profile)
            except sqlite3.Error:
                stats = {'error': 'Session usage temporarily unavailable'}
            agents.append({'id': profile, **role, 'usage': stats,
                           'provisioned': (PROFILE_ROOT / profile / 'config.yaml').is_file()})
        probe = subprocess.run([sys.executable, '/project/scripts/healthcheck.py'],
                               capture_output=True, timeout=5)
        return {'agents': agents, 'board': board,
                'gateway': 'healthy' if probe.returncode == 0 else 'unavailable'}
    if op == 'detail':
        tid = task_id(request.get('task_id'))
        detail = native('kanban_show', {'task_id': tid})
        detail.pop('worker_context', None)
        # Console logs mix visible output with internal reasoning. Public session
        # transcripts expose the supported visible messages and tool activity.
        detail['log'] = ''
        return detail
    if op == 'create':
        assignee = request.get('assignee')
        if not isinstance(assignee, str) or assignee not in ROLES:
            raise ValueError('Unknown project profile')
        parents = request.get('parents', [])
        if not isinstance(parents, list) or len(parents) > 12:
            raise ValueError('At most 12 parent tasks are allowed')
        parents = [task_id(p) for p in parents]
        key = text(request.get('idempotency_key'), 'request key', 100)
        if not re.fullmatch(r'dashboard-[a-f0-9-]{36}', key):
            raise ValueError('Invalid request key')
        args = {'title': text(request.get('title'), 'Title', 200),
                'body': text(request.get('body'), 'Brief', 12000), 'assignee': assignee,
                'tenant': text(request.get('tenant', 'brand-os-dashboard'), 'Project', 80),
                'parents': parents, 'workspace_kind': 'dir', 'workspace_path': '/knowledge',
                'max_runtime_seconds': 300, 'priority': 0, 'triage': False,
                'idempotency_key': key}
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}', args['tenant']):
            raise ValueError('Project uses letters, numbers, hyphens and underscores')
        args['body'] += ('\n\nDashboard operator request. Preserve project safeguards: '
                         'drafts only; no publishing, DMs, scraping, media generation or rendering. '
                         'Do not invent personal facts. Major strategy changes require human approval. '
                         'Write task-ID artifacts in your owned /knowledge folder and include '
                         'artifact_paths in your native Kanban completion handoff. '
                         'CEO: delegate specialist work through native Kanban.')
        return native('kanban_create', args)
    if op in {'comment', 'unblock', 'request_changes'}:
        args = {'task_id': task_id(request.get('task_id'))}
        if op == 'comment':
            args['body'] = 'Operator via dashboard: ' + text(request.get('body'), 'Note', 4000)
        if op == 'request_changes':
            args['reason'] = text(request.get('body'), 'Revision reason', 4000)
        return native('kanban_' + op, args)
    raise ValueError('Unknown dashboard operation')


def serve():
    """Warm request adapter; all execution remains in native Hermes."""
    for line in sys.stdin:
        rid = None
        try:
            request = json.loads(line)
            rid = request.get('id')
            if request.get('method') != 'dispatch' or not isinstance(request.get('params'), dict):
                raise ValueError('Invalid adapter request')
            response = {'id': rid, 'result': dispatch(request['params'])}
        except ValueError as exc:
            response = {'id': rid, 'error': {'message': str(exc)}}
        except Exception:
            response = {'id': rid, 'error': {'message': 'Hermes could not read this resource'}}
        print(json.dumps(response), flush=True)


if __name__ == '__main__' and '--serve' in sys.argv:
    serve()
elif __name__ == '__main__':
    try:
        payload = json.loads(sys.stdin.read(20000))
        if not isinstance(payload, dict):
            raise ValueError('Request must be an object')
        result = dispatch(payload)
        print(json.dumps(result))
    except ValueError as exc:
        print(json.dumps({'error': str(exc)}))
        sys.exit(2)
