"""DETERMINISTIC native Kanban regression; isolated DB, no dispatcher/inference."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

os.environ['HERMES_HOME'] = '/opt/data/profiles/brand-ceo'
os.environ['HERMES_PROFILE'] = 'brand-ceo'
spec = importlib.util.spec_from_file_location('relay_plugin', '/project/config/plugins/artifact-validator/__init__.py')
plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plugin)

with tempfile.TemporaryDirectory(prefix='synthetic-ceo-artifact-', dir='/knowledge/operations') as fixture:
    artifact = Path(fixture) / 'synthetic.md'
    artifact.write_text('''---
created: 2026-10-09
---
## Spoken Script (3 words)
> Three synthetic words
---
| Beat | Duration | Spoken Line |
| --- | --- | --- |
| Body | 45s | Three synthetic words |
''')
    assert json.loads(plugin.handle({'path': str(artifact), 'min_words': 3, 'max_words': 3}))['valid']
    assert not json.loads(plugin.handle({'path': str(artifact)}))['valid']
    for params in ({'path': 'relative.md'}, {'path': '/opt/data/config.yaml'},
                   {'path': '/knowledge/nonexistent-synthetic.md'}, {'path': str(artifact), 'extra': True},
                   {'path': str(artifact), 'target_seconds': 0}, {}):
        assert json.loads(plugin.handle(params)).get('error')

with tempfile.TemporaryDirectory(prefix='brand-ceo-relay-synthetic-') as temporary:
    os.environ['HERMES_KANBAN_DB'] = str(Path(temporary) / 'isolated.db')
    def create(assignee, tenant='brand-os-ceo', parents=None):
        return plugin.relay_native('kanban_create', {
            'title': 'SYNTHETIC relay regression — never dispatch', 'assignee': assignee,
            'tenant': tenant, 'parents': parents or [], 'workspace_kind': 'dir',
            'workspace_path': '/knowledge', 'max_runtime_seconds': 300})['task_id']
    planner = create('brand-ceo')
    assert plugin.relay_before_tool(tool_name='kanban_create', args={
        'assignee': 'brand-manager'}) == {'action': 'modify', 'args': {'tenant': 'brand-os-ceo'}}
    assert plugin.relay_before_tool(tool_name='kanban_create', args={
        'assignee': 'brand-manager', 'tenant': 'other-tenant'}) is None
    manager = create('brand-manager', parents=[planner])
    result = plugin.relay_after_create(tool_name='kanban_create', args={
        'assignee': 'brand-manager', 'tenant': 'brand-os-ceo'},
        result=json.dumps({'task_id': manager}))
    relay = json.loads(result)['ceo_followup_task_id']
    detail = plugin.relay_native('kanban_show', {'task_id': relay})
    assert detail['parents'] == [manager]
    assert detail['task']['assignee'] == 'brand-ceo'
    assert detail['task']['tenant'] == 'brand-os-ceo'
    assert detail['task']['workspace_path'] == '/knowledge'
    assert detail['unsatisfied_parents'] and detail['runs'] == []
    assert plugin.ensure_ceo_relay(manager) == relay
    assert json.loads(plugin.relay_after_create(tool_name='kanban_create', args={
        'assignee': 'brand-manager', 'tenant': 'brand-os-ceo'},
        result=json.dumps({'task_id': manager})))['ceo_followup_task_id'] == relay
    duplicate = plugin.relay_before_tool(tool_name='kanban_create', args={
        'assignee': 'brand-ceo', 'tenant': 'brand-os-ceo', 'parents': [manager]})
    assert duplicate['action'] == 'block' and relay in duplicate['message']
    # Recover even when the model omitted pairing, including across process reloads.
    missing = create('brand-manager', parents=[planner])
    assert plugin.relay_before_tool(tool_name='kanban_complete', args={'task_id': planner}) is None
    repaired = plugin.relay_native('kanban_show', {'task_id': missing})['children']
    assert len(repaired) == 1
    plugin.relay_native('kanban_complete', {'task_id': planner, 'summary': 'SYNTHETIC planning complete'})
    plugin.relay_native('kanban_complete', {'task_id': manager, 'summary': 'SYNTHETIC questions prepared'})
    assert not plugin.relay_native('kanban_show', {'task_id': relay})['unsatisfied_parents']
    plugin.relay_native('kanban_complete', {'task_id': relay, 'summary': 'SYNTHETIC relay complete'})
    assert plugin.ensure_ceo_relay(manager) == relay, 'No duplicate after a relay completes'
    # Manually paired native cards are reused, and unrelated tenants/agents ignored.
    other_manager = create('brand-manager')
    manual = create('brand-ceo', parents=[other_manager])
    assert plugin.ensure_ceo_relay(other_manager) == manual
    for name, assignee, tenant, raw in [
        ('kanban_show', 'brand-manager', 'brand-os-ceo', '{}'),
        ('kanban_create', 'hook-writer', 'brand-os-ceo', '{}'),
        ('kanban_create', 'brand-manager', 'other-tenant', '{}'),
        ('kanban_create', 'brand-manager', 'brand-os-ceo', '{"error":"failed"}')]:
        assert plugin.relay_after_create(tool_name=name, args={'assignee': assignee, 'tenant': tenant}, result=raw) is None
    os.environ['HERMES_HOME'] = '/opt/data/profiles/script-writer'
    assert plugin.relay_after_create(tool_name='kanban_create', args={
        'assignee': 'brand-manager', 'tenant': 'brand-os-ceo'}, result=json.dumps({'task_id': manager})) is None
    assert plugin.relay_before_tool(tool_name='kanban_complete', args={'task_id': planner}) is None
    os.environ['HERMES_HOME'] = '/opt/data/profiles/brand-ceo'
    unrelated = create('brand-manager', 'other-tenant')
    try:
        plugin.ensure_ceo_relay(unrelated)
    except ValueError:
        pass
    else:
        raise AssertionError('Cross-tenant repair must be rejected')
    with patch.object(plugin, 'ensure_ceo_relay', side_effect=ValueError('SYNTHETIC failure')):
        failure = plugin.relay_before_tool(tool_name='kanban_complete', args={
            'task_id': planner, 'created_cards': [manager]})
        assert failure['action'] == 'block' and 'SYNTHETIC failure' in failure['message']
        raw = plugin.relay_after_create(tool_name='kanban_create', args={
            'assignee': 'brand-manager', 'tenant': 'brand-os-ceo'}, result=json.dumps({'task_id': manager}))
        assert 'ceo_followup_error' in json.loads(raw)
    assert plugin.relay_before_tool(tool_name='file_read', args={}) is None
    assert plugin.relay_before_tool(tool_name='kanban_complete', args={}) is None
    assert plugin.relay_before_tool(tool_name='kanban_complete', args={'task_id': manager}) is None
    assert plugin.relay_before_tool(tool_name='kanban_create', args={'assignee': 'hook-writer'}) is None
    assert plugin.relay_before_tool(tool_name='kanban_create', args={
        'assignee': 'brand-ceo', 'tenant': 'brand-os-ceo', 'parents': [planner]}) is None
    assert plugin.relay_after_create(tool_name='kanban_create', args={
        'assignee': 'brand-manager', 'tenant': 'brand-os-ceo'}, result='{}') is None
    try:
        plugin.relay_native('kanban_show', {'task_id': 't_nonexistentfixture'})
    except ValueError:
        pass
    else:
        raise AssertionError('Native tool failures must surface')
    # Exercise installed plugin registration and native hook dispatch, including
    # the context-local profile isolation used by direct dashboard conversations.
    from hermes_cli.plugins import discover_plugins
    from hermes_cli.lifecycle import invoke_hook
    from hermes_constants import set_hermes_home_override, reset_hermes_home_override
    discover_plugins()
    directives = invoke_hook('pre_tool_call', tool_name='kanban_create', args={'assignee': 'brand-manager'})
    assert {'action': 'modify', 'args': {'tenant': 'brand-os-ceo'}} in directives, directives
    hooked = create('brand-manager')
    native_results = invoke_hook('transform_tool_result', tool_name='kanban_create', args={
        'assignee': 'brand-manager', 'tenant': 'brand-os-ceo'}, result=json.dumps({'task_id': hooked}))
    assert any(isinstance(r, str) and 'ceo_followup_task_id' in r for r in native_results), native_results
    token = set_hermes_home_override('/opt/data/profiles/script-writer')
    try:
        assert not plugin.relay_scope(), 'Context-local home must override CEO env'
        untouched = create('brand-manager')
        invoke_hook('transform_tool_result', tool_name='kanban_create', args={
            'assignee': 'brand-manager', 'tenant': 'brand-os-ceo'}, result=json.dumps({'task_id': untouched}))
        assert plugin.relay_native('kanban_show', {'task_id': untouched})['children'] == []
    finally:
        reset_hermes_home_override(token)
print('PASS: isolated native CEO relay pairing, retries, completion recovery, scope, fail-closed guard; no inference')
