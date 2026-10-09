"""DETERMINISTIC isolated native Kanban integration. Never dispatches or runs inference."""
import importlib.util
import os
from pathlib import Path
import tempfile
import uuid

with tempfile.TemporaryDirectory(prefix='brand-dashboard-native-') as temporary:
    os.environ['HERMES_KANBAN_DB'] = str(Path(temporary) / 'isolated.db')
    spec = importlib.util.spec_from_file_location('dashboard_bridge', '/project/scripts/dashboard-bridge.py')
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)

    payload = {'op': 'create', 'assignee': 'hook-writer', 'title': 'SYNTHETIC dashboard fixture',
               'body': 'SYNTHETIC input for deterministic integration. Do not execute.',
               'tenant': 'synthetic-dashboard-test', 'idempotency_key': 'dashboard-' + str(uuid.uuid4())}
    first = bridge.dispatch(payload)
    second = bridge.dispatch(payload)
    assert first['task_id'] == second['task_id'], (first, second)
    tid = first['task_id']
    detail = bridge.native('kanban_show', {'task_id': tid})
    assert detail['task']['assignee'] == 'hook-writer'
    assert detail['task']['workspace_path'] == '/knowledge'
    assert 'drafts only' in detail['task']['body']
    assert detail['runs'] == [], 'Isolated fixtures must never run inference'
    bridge.dispatch({'op': 'comment', 'task_id': tid, 'body': 'SYNTHETIC operator feedback'})
    detail = bridge.native('kanban_show', {'task_id': tid})
    assert any('SYNTHETIC operator feedback' in c['body'] for c in detail['comments'])
    child = bridge.dispatch({**payload, 'parents': [tid], 'idempotency_key': 'dashboard-' + str(uuid.uuid4())})
    child_detail = bridge.native('kanban_show', {'task_id': child['task_id']})
    assert child_detail['parents'] == [tid]
    assert child_detail['unsatisfied_parents'], child_detail
    bridge.native('kanban_block', {'task_id': tid, 'reason': 'SYNTHETIC block', 'kind': 'needs_input'})
    bridge.dispatch({'op': 'unblock', 'task_id': tid})
    assert bridge.native('kanban_show', {'task_id': tid})['task']['status'] in {'ready', 'running'}

    message = {'op': 'ceo_message', 'body': 'SYNTHETIC brand discovery request',
               'assignee': 'publisher', 'tenant': 'untrusted-override',
               'idempotency_key': 'dashboard-' + str(uuid.uuid4())}
    ceo = bridge.dispatch(message)['task_id']
    assert bridge.dispatch(message)['task_id'] == ceo
    ceo_detail = bridge.native('kanban_show', {'task_id': ceo})
    assert ceo_detail['task']['assignee'] == 'brand-ceo'
    assert ceo_detail['task']['tenant'] == bridge.CEO_TENANT
    assert 'Brand Manager' in ceo_detail['task']['body']
    bridge.native('kanban_block', {'task_id': ceo, 'reason': 'SYNTHETIC interview question', 'kind': 'needs_input'})
    thread = bridge.dispatch({'op': 'ceo_thread'})
    assert thread['tasks'][0]['question'] == 'SYNTHETIC interview question'
    reply = {'op': 'ceo_reply', 'task_id': ceo, 'body': 'SYNTHETIC personal answer',
             'idempotency_key': 'dashboard-' + str(uuid.uuid4())}
    try:
        bridge.dispatch({**reply, 'question_key': 'stale-question'})
    except ValueError:
        pass
    else:
        raise AssertionError('Stale question reply accepted')
    assert bridge.native('kanban_show', {'task_id': ceo})['comments'] == []
    bridge.dispatch(reply)
    bridge.dispatch(reply)
    resumed = bridge.native('kanban_show', {'task_id': ceo})
    assert len(resumed['comments']) == 1, 'Retry must not duplicate an answer'
    assert resumed['task']['status'] in {'ready', 'running'}
    try:
        bridge.dispatch({**reply, 'body': 'Changed answer under reused key'})
    except ValueError:
        pass
    else:
        raise AssertionError('Conflicting retry accepted')
    loop = bridge.dispatch({**message, 'idempotency_key': 'dashboard-' + str(uuid.uuid4())})['task_id']
    bridge.native('kanban_block', {'task_id': loop, 'reason': 'SYNTHETIC first loop question', 'kind': 'needs_input'})
    loop_reply = {**reply, 'task_id': loop, 'idempotency_key': 'dashboard-' + str(uuid.uuid4())}
    bridge.dispatch(loop_reply)
    bridge.native('kanban_block', {'task_id': loop, 'reason': 'SYNTHETIC next loop question', 'kind': 'needs_input'})
    before_retry = bridge.native('kanban_show', {'task_id': loop})['task']['status']
    bridge.dispatch(loop_reply)
    assert bridge.native('kanban_show', {'task_id': loop})['task']['status'] == before_retry, 'Old retry must not answer a new question or undo native triage'
    try:
        bridge.dispatch({**loop_reply, 'question_key': 'stale-question',
                         'idempotency_key': 'dashboard-' + str(uuid.uuid4())})
    except ValueError:
        pass
    else:
        raise AssertionError('Stale question reply accepted')
    bridge.native('kanban_complete', {'task_id': ceo, 'summary': 'SYNTHETIC round complete'})
    next_round = bridge.dispatch({**message, 'reply_to': ceo,
                                 'idempotency_key': 'dashboard-' + str(uuid.uuid4())})['task_id']
    assert bridge.native('kanban_show', {'task_id': next_round})['parents'] == [ceo]
    bridge.native('kanban_block', {'task_id': next_round, 'kind': 'transient', 'reason': 'SYNTHETIC provider error'})
    for invalid_reply in ({**reply, 'task_id': tid}, {**reply, 'task_id': next_round},
                          {**reply, 'idempotency_key': 'invalid'},
                          {**message, 'reply_to': tid}, {**message, 'body': ''}):
        try:
            bridge.dispatch(invalid_reply)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid CEO input accepted')
    for invalid in ({**payload, 'assignee': 'default'}, {**payload, 'parents': ['../escape']},
                    {**payload, 'tenant': 'invalid/project'}, {**payload, 'body': ''},
                    {'op': 'shell', 'body': 'anything'}, {**payload, 'idempotency_key': 'bad'}):
        try:
            bridge.dispatch(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid input was accepted')
    # Creation provenance joins dispatcher relays even without a dependency on
    # the planning CEO card. This is presentation data, never a new execution edge.
    os.environ['HERMES_KANBAN_TASK'] = ceo
    try:
        relay = bridge.native('kanban_create', {'title': 'SYNTHETIC provenance fixture',
            'assignee': 'brand-ceo', 'tenant': bridge.CEO_TENANT,
            'workspace_kind': 'dir', 'workspace_path': '/knowledge'})['task_id']
    finally:
        os.environ.pop('HERMES_KANBAN_TASK', None)
    joined = next(d for d in bridge.dispatch({'op': 'ceo_thread'})['tasks'] if d['task']['id']==relay)
    assert joined['creator_task_id'] == ceo and joined['parents'] == []
    print('PASS DETERMINISTIC isolated dashboard/native Kanban: create, deduplicate, dependencies, '
          'operator note, unblock, CEO routing, interview replies, retry safety, and input restrictions. '
          'No production mutations or inference.')

    # Native session API writes into an isolated fixture store; production transcripts are read-only.
    from hermes_state import SessionDB
    original_profiles = bridge.PROFILE_ROOT
    bridge.PROFILE_ROOT = Path(temporary) / 'profiles'
    fixture_home = bridge.PROFILE_ROOT / 'brand-manager'
    fixture_home.mkdir(parents=True)
    db = SessionDB(fixture_home / 'state.db')
    try:
        db.create_session('synthetic-dashboard-session', 'api_server')
        db.append_message('synthetic-dashboard-session', 'system', 'SYNTHETIC hidden instructions')
        db.append_message('synthetic-dashboard-session', 'user', 'SYNTHETIC user question')
        db.append_message('synthetic-dashboard-session', 'assistant', 'SYNTHETIC visible answer',
                          reasoning='SYNTHETIC private reasoning')
        db.append_message('synthetic-dashboard-session', 'assistant', 'SYNTHETIC hidden carrier', display_kind='hidden')
        db.append_message('synthetic-dashboard-session', 'tool', 'SYNTHETIC tool result', tool_name='read_file')
        result = bridge.dispatch({'op': 'conversation', 'profile': 'brand-manager',
                                  'session_id': 'synthetic-dashboard-session'})
        assert [m['role'] for m in result['messages']] == ['user', 'assistant', 'tool']
        assert 'reasoning' not in str(result) and 'hidden' not in str(result)
        assert result['session']['source'] == 'api_server'
        assert len(bridge.dispatch({'op': 'conversations', 'profile': 'brand-manager'})['sessions']) == 1
        for i in range(205):
            db.append_message('synthetic-dashboard-session', 'assistant', f'SYNTHETIC bounded row {i}')
        result = bridge.conversation('brand-manager', 'synthetic-dashboard-session')
        assert result['truncated'] and len(result['messages']) == 200
        assert result['messages'][-1]['content'] == 'SYNTHETIC bounded row 204'
        for profile, sid in [('default', 'synthetic-dashboard-session'), ('brand-manager', '../escape'),
                             ('brand-manager', 'absent')]:
            try:
                bridge.conversation(profile, sid)
            except ValueError:
                pass
            else:
                raise AssertionError('Unscoped native history was accepted')
        try:
            bridge.dispatch({'op': 'conversations', 'profile': 'default'})
        except ValueError:
            pass
        else:
            raise AssertionError('Infrastructure profile was exposed as an agent')
    finally:
        db.close()
        bridge.PROFILE_ROOT = original_profiles
    print('PASS DETERMINISTIC native session history: isolated API-created fixtures, profile scope, '
          'visible messages/tool results, private reasoning/hidden rows excluded, bounded transcript. No inference.')

    # Test the output wrapper without importing/starting a native chat backend.
    import sys
    import types
    original_tui = sys.modules.get('tui_gateway')
    original_home, original_profile = os.environ.get('HERMES_HOME'), os.environ.get('HERMES_PROFILE')
    fake_tui = types.ModuleType('tui_gateway')
    fake_tui.entry = types.SimpleNamespace()
    sys.modules['tui_gateway'] = fake_tui
    try:
        chat_spec = importlib.util.spec_from_file_location('dashboard_chat', '/project/scripts/dashboard-chat.py')
        chat = importlib.util.module_from_spec(chat_spec)
        chat_spec.loader.exec_module(chat)
        cleaned = chat.visible({'reasoning': 'SYNTHETIC private', 'result': {'password': 'SYNTHETIC_SECRET'},
                                'text': 'SYNTHETIC visible', 'rendered': '<script>fixture</script>'})
        assert cleaned == {'result': {'password': '[REDACTED]'}, 'text': 'SYNTHETIC visible'}
        sent = []
        transport = chat.PublicTransport(types.SimpleNamespace(write=lambda f: sent.append(f) or True,
                                                               close=lambda: None))
        assert transport.write({'method': 'event', 'params': {'type': 'reasoning.delta', 'payload': {'text': 'private'}}})
        assert not sent
        transport.write({'method': 'event', 'params': {'type': 'message.delta', 'payload': {'text': 'SYNTHETIC visible'}}})
        assert len(sent) == 1
        transport.close()
    finally:
        if original_tui is None:
            sys.modules.pop('tui_gateway', None)
        else:
            sys.modules['tui_gateway'] = original_tui
        for name, value in [('HERMES_HOME', original_home), ('HERMES_PROFILE', original_profile)]:
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    print('PASS DETERMINISTIC chat event wrapper: visible text preserved, credentials redacted, '
          'reasoning events and rendered HTML excluded. No native backend startup or inference.')
