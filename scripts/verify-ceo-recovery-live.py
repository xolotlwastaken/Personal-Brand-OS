"""Bounded REAL dispatcher recovery smoke test, separate from isolated fixtures.

Native Kanban only. One synthetic stopped specialist and its real CEO recovery;
no external actions. Re-running reads the same native idempotent submission.
"""
import json
import os
from pathlib import Path
import sys
import time

os.environ['HERMES_HOME'] = '/opt/data'
os.environ.pop('HERMES_PROFILE', None)
from tools.kanban_tools import registry


def native(name, args):
    row = json.loads(registry.get_entry(name).handler(args))
    if row.get('error'):
        raise RuntimeError(row['error'])
    return row


tenant = 'brand-os-recovery-live'
source = native('kanban_create', {
    'title': 'SYNTHETIC REAL recovery smoke: temporary Hook Writer stop',
    'body': '''This is a SYNTHETIC infrastructure fixture with REAL model inference.
No personal brand evidence or creative work is requested. On recovery retry,
start with kanban_show and write /knowledge/content/hooks/<ACTUAL_TASK_ID>-synthetic-recovery.md
with task_id, owner hook-writer, status synthetic-test, assumptions synthetic fixture,
and approval not-applicable. Content: "Synthetic recovery succeeded; no personal claims."
Read the file back and call kanban_complete with summary and metadata artifact_paths.
Do not update canonical notes or private memory. No network, external research,
publishing, DMs, media generation or rendering. Complete without new cards or human input.
''',
    'assignee': 'hook-writer', 'tenant': tenant, 'workspace_kind': 'dir',
    'workspace_path': '/knowledge', 'max_runtime_seconds': 120, 'initial_status': 'blocked',
    'idempotency_key': 'ceo-recovery-live-source-v2'})['task_id']
detail = native('kanban_show', {'task_id': source})
if detail['task']['status'] == 'blocked' and not detail['runs'] and not any(
        e['kind'] == 'blocked' and (e.get('payload') or {}).get('kind') for e in detail['events']):
    native('kanban_block', {'task_id': source, 'kind': 'transient',
        'reason': 'SYNTHETIC temporary execution error for a bounded REAL dispatcher test. '
                  'No human information, credentials, capability or approval is missing. '
                  'CEO: use brand_task_retry ONCE on this source, report the restart, '
                  'and complete the recovery; the specialist needs no further input.'})
report_path = Path('/opt/data/verification/ceo-recovery-live.json')
report_path.parent.mkdir(exist_ok=True)
print(f'REAL dispatcher recovery smoke: source {source}; synthetic content only.', flush=True)
deadline = time.monotonic() + 420
recovery = None
while time.monotonic() < deadline:
    source_detail = native('kanban_show', {'task_id': source})
    rows = native('kanban_list', {'assignee': 'brand-ceo', 'tenant': tenant, 'limit': 20})['tasks']
    matches = [r for r in rows if r['title'] == f'CEO recovery: hook-writer {source}']
    if matches:
        recovery = native('kanban_show', {'task_id': matches[-1]['id']})
    if (source_detail['task']['status'] == 'done' and recovery and
            recovery['task']['status'] == 'done' and not recovery['task']['current_run_id']):
        break
    if recovery and recovery['task']['status'] in {'blocked', 'triage'} and recovery['runs']:
        raise RuntimeError(f'REAL recovery needs attention: {recovery["task"]["id"]}; inspect native handoff')
    time.sleep(3)
else:
    raise RuntimeError(f'REAL recovery exceeded bounded wait: source {source}; inspect native board')
assert recovery['parents'] == [] and not recovery['unsatisfied_parents']
assert len([c for c in source_detail['comments'] if c['body'].startswith('Brand OS bounded retry: ')]) == 1
assert source_detail['runs'] and recovery['runs'], 'Must exercise actual named workers'
assert any(c['body'].startswith('CEO to you:') for c in recovery['comments'])
artifacts = [p for r in source_detail['runs'] for p in (r.get('metadata') or {}).get('artifact_paths', [])]
assert artifacts and all(Path(p).is_file() for p in artifacts)
report = {'test': 'REAL native dispatcher recovery; synthetic content', 'source_task_id': source,
          'recovery_task_id': recovery['task']['id'], 'status': 'passed',
          'original_task_retry_count': 1, 'artifact_paths': artifacts, 'inference': True}
report_path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2), flush=True)
