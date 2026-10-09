"""DETERMINISTIC native recovery tests; isolated DB, fake spawn, no inference."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

os.environ['HERMES_HOME'] = '/opt/data'
os.environ.pop('HERMES_PROFILE', None)
spec = importlib.util.spec_from_file_location('recovery', '/project/config/plugins/ceo-recovery/__init__.py')
plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plugin)

with tempfile.TemporaryDirectory(prefix='synthetic-ceo-recovery-') as temporary:
    os.environ['HERMES_KANBAN_DB'] = str(Path(temporary) / 'isolated.db')
    def native(name, **args):
        return plugin.native(name, args, 'default')
    def create(assignee, **args):
        return native('kanban_create', title='SYNTHETIC recovery — never infer',
                      assignee=assignee, tenant='brand-os-ceo', workspace_kind='dir',
                      workspace_path='/knowledge', max_runtime_seconds=300, **args)['task_id']
    def detail(tid):
        return native('kanban_show', task_id=tid)
    def recoveries():
        return [t for t in native('kanban_list', limit=200)['tasks']
                if plugin.recovery_context(detail(t['id'])['task']['body'])]

    planner = create('brand-ceo')
    native('kanban_complete', task_id=planner, summary='SYNTHETIC planning only')
    os.environ['HERMES_KANBAN_TASK'] = planner
    specialist = create('brand-manager')
    os.environ.pop('HERMES_KANBAN_TASK')
    followup = create('brand-ceo', parents=[specialist])
    native('kanban_block', task_id=specialist, kind='needs_input', reason='SYNTHETIC missing supplied evidence')
    plugin.dispatch_tick(board='default', dry_run=True)
    assert not recoveries(), 'Dry-run observer must not mutate'
    plugin.dispatch_tick(board='default')
    rows = recoveries()
    assert len(rows) == 1
    rid = rows[0]['id']
    recovery = detail(rid)
    assert recovery['parents'] == [] and not recovery['unsatisfied_parents']
    context = plugin.recovery_context(recovery['task']['body'])
    assert context['source_task_id'] == specialist and context['origin_task_id'] == planner
    assert any(c['body'].startswith('CEO to you:') for c in recovery['comments'])
    assert detail(followup)['unsatisfied_parents'], 'Never bypass the producing dependency'
    plugin.dispatch_tick(board='default')
    assert len(recoveries()) == 1, 'Repeated ticks deduplicate the incident'
    # Reload loses all process state: native incident identity still deduplicates.
    reloaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reloaded)
    reloaded.dispatch_tick(board='default')
    assert len(recoveries()) == 1

    # CEO waiting on a human is normal. Unspecified triage, reviews, other profiles
    # and other workspaces must not produce false failure notifications.
    waiting = create('brand-ceo')
    native('kanban_block', task_id=waiting, kind='needs_input', reason='SYNTHETIC interview')
    create('hook-writer', initial_status='blocked')
    create('brand-ceo', triage=True)
    foreign = native('kanban_create', title='SYNTHETIC unrelated', assignee='unrelated',
                     tenant='brand-os-ceo', workspace_kind='dir', workspace_path='/knowledge')['task_id']
    native('kanban_block', task_id=foreign, kind='capability', reason='SYNTHETIC')
    plugin.dispatch_tick(board='default')
    assert len(recoveries()) == 1

    # CEO recovery itself stops: show an actionable input gate without recursive
    # recovery cards, even if the model/provider cannot produce a response.
    native('kanban_block', task_id=rid, kind='transient', reason='SYNTHETIC CEO provider failed')
    plugin.dispatch_tick(board='default')
    fallback = detail(rid)
    assert fallback['task']['status'] == 'blocked'
    assert plugin.blocker(fallback)[1] == 'needs_input'
    assert len(recoveries()) == 1
    plugin.dispatch_tick(board='default')
    assert len(recoveries()) == 1

    # Deterministic dispatcher error: spawn stub raises; no model process exists.
    crashed = create('hook-writer')
    from hermes_cli import kanban_db_connect, kanban_db_dispatch
    conn = kanban_db_connect.connect()
    try:
        def fail_spawn(*args, **kwargs):
            raise RuntimeError('SYNTHETIC spawn failure')
        result = kanban_db_dispatch.dispatch_once(conn, spawn_fn=fail_spawn, max_spawn=20, failure_limit=1)
    finally:
        conn.close()
    assert detail(crashed)['task']['status'] in {'blocked', 'triage'}
    plugin.dispatch_tick(board='default', result=result)
    assert any(plugin.recovery_context(detail(t['id'])['task']['body'])['source_task_id'] == crashed
               for t in recoveries())
    assert all(not d['runs'] or all(r['outcome'] in {'completed', 'blocked', 'spawn_failed', 'gave_up'} for r in d['runs'])
               for d in (detail(t['id']) for t in native('kanban_list', limit=200)['tasks']))

    # Explicit retry can only address the source of the current CEO recovery.
    os.environ['HERMES_HOME'] = '/opt/data/profiles/brand-ceo'
    os.environ['HERMES_PROFILE'] = 'brand-ceo'
    os.environ['HERMES_KANBAN_TASK'] = rid
    assert json.loads(plugin.retry({'task_id': crashed})).get('error')
    assert json.loads(plugin.retry({'task_id': specialist})).get('error'), 'Human input cannot be bypassed'
    os.environ.pop('HERMES_KANBAN_TASK')
    # Retry a transient specialist using the supported CLI; preserves the original
    # task ID and downstream edges and has a durable one-retry budget.
    transient = create('script-writer')
    os.environ['HERMES_HOME'] = '/opt/data'
    os.environ.pop('HERMES_PROFILE', None)
    native('kanban_block', task_id=transient, kind='transient', reason='SYNTHETIC temporary failure')
    plugin.dispatch_tick(board='default')
    retry_card = next(t['id'] for t in recoveries()
                      if plugin.recovery_context(detail(t['id'])['task']['body'])['source_task_id'] == transient)
    os.environ['HERMES_HOME'] = '/opt/data/profiles/brand-ceo'
    os.environ['HERMES_PROFILE'] = 'brand-ceo'
    os.environ['HERMES_KANBAN_TASK'] = retry_card
    result = json.loads(plugin.retry({'task_id': transient}))
    assert result.get('ok'), result
    assert detail(transient)['task']['status'] == 'ready'
    assert json.loads(plugin.retry({'task_id': transient})).get('already_retried')
    os.environ.pop('HERMES_KANBAN_TASK')
    native('kanban_block', task_id=transient, kind='transient', reason='SYNTHETIC second failure')
    os.environ['HERMES_KANBAN_TASK'] = retry_card
    assert json.loads(plugin.retry({'task_id': transient})).get('error'), 'Never loop retries'
    os.environ.pop('HERMES_KANBAN_TASK')
    # Timeout through native dispatcher helpers with a nonexistent synthetic PID
    # and injected clock/signal function. No direct SQL or real worker process.
    os.environ['HERMES_HOME'] = '/opt/data'
    os.environ.pop('HERMES_PROFILE', None)
    os.environ['HERMES_KANBAN_DB'] = str(Path(temporary) / 'timeout-isolated.db')
    conn = kanban_db_connect.connect()
    try:
        import time
        past = time.time() - 301
        with patch.object(kanban_db_dispatch.time, 'time', return_value=past):
            timed = create('reference-builder')
            kanban_db_dispatch.dispatch_once(conn, spawn_fn=lambda *a, **k: 2147483000, max_spawn=1)
        assert detail(timed)['task']['current_run_id']
        plugin.dispatch_tick(board='default')
        assert not recoveries(), 'Active claims must not be treated as stopped'
        signals = []
        timed_out = kanban_db_dispatch.enforce_max_runtime(conn, signal_fn=lambda *a: signals.append(a))
        assert timed_out == [timed] and signals
    finally:
        conn.close()
    from types import SimpleNamespace
    plugin.dispatch_tick(board='default', result=SimpleNamespace(timed_out=timed_out))
    assert detail(timed)['task']['status'] == 'blocked'
    assert len(recoveries()) == 1
    timeout_recovery = recoveries()[0]['id']
    os.environ['HERMES_HOME'] = '/opt/data/profiles/brand-ceo'
    os.environ['HERMES_PROFILE'] = 'brand-ceo'
    os.environ['HERMES_KANBAN_TASK'] = timeout_recovery
    assert json.loads(plugin.retry({'task_id': timed})).get('ok')
    os.environ.pop('HERMES_KANBAN_TASK')
    native('kanban_block', task_id=timed, kind='transient', reason='SYNTHETIC timeout repeated')
    os.environ['HERMES_KANBAN_TASK'] = timeout_recovery
    assert json.loads(plugin.retry({'task_id': timed})).get('error')
    os.environ.pop('HERMES_KANBAN_TASK')
    # Provider authentication is an operator fix, never an automatic retry.
    auth = create('publisher')
    native('kanban_block', task_id=auth, kind='transient', reason='SYNTHETIC 401 invalid API key')
    os.environ['HERMES_HOME'] = '/opt/data'
    os.environ.pop('HERMES_PROFILE', None)
    plugin.dispatch_tick(board='default')
    auth_recovery = next(t['id'] for t in recoveries()
                         if plugin.recovery_context(detail(t['id'])['task']['body'])['source_task_id'] == auth)
    os.environ['HERMES_HOME'] = '/opt/data/profiles/brand-ceo'
    os.environ['HERMES_PROFILE'] = 'brand-ceo'
    os.environ['HERMES_KANBAN_TASK'] = auth_recovery
    assert json.loads(plugin.retry({'task_id': auth})).get('error')
    os.environ.pop('HERMES_KANBAN_TASK')
    print('PASS DETERMINISTIC isolated native CEO recovery: independent notification, '
          'restart deduplication, human gates, failed CEO fallback, fake spawn failure/timeout, '
          'scoped bounded retry. No inference or production mutations.')
