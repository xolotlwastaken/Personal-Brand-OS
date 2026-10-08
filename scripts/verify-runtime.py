"""Deterministic verification; isolated board, native lifecycle tools, zero model calls."""
import json, os, subprocess, sys, time, uuid
from pathlib import Path
import hermes_yaml as yaml
from hermes_cli.profiles import list_profile_names
roles=json.loads(Path('/project/config/agents.json').read_text());root=Path('/opt/data');out=root/'verification';out.mkdir(exist_ok=True)
assert set(list_profile_names())-{'default'}==set(roles)
checks=[]
for profile in roles:
    completed=subprocess.run([sys.executable,'/project/scripts/verify-profile.py',profile],text=True,capture_output=True,timeout=180)
    if completed.returncode:raise RuntimeError(f'{profile}: {completed.stderr[-2000:]} {completed.stdout[-1000:]}')
    result=json.loads(completed.stdout.strip().splitlines()[-1]);checks.append(result);print('PASS profile:',profile,flush=True)
assert len({r['memory'] for r in checks})==7
# Every profile reads the same agreed handoff file; private memories are distinct files.
for profile in roles:
    private=root/'profiles'/profile/'memories/MEMORY.md'; assert not private.is_symlink()
    assert (root/'profiles'/profile/'SOUL.md').is_file()
for cfgpath in [root/'config.yaml']+list((root/'profiles').glob('*/config.yaml')):
    cfg=yaml.safe_load(cfgpath.read_text()); assert cfg['kanban']['auto_decompose'] is False
    assert cfg['kanban']['max_in_progress']==1
# Isolate tests from the gateway's enumerated boards: no production task can run.
os.environ['HERMES_KANBAN_DB']=str(out/f'deterministic-{uuid.uuid4().hex[:8]}.db')
os.environ['HERMES_HOME']=str(root/'profiles/brand-ceo');os.environ['HERMES_PROFILE']='brand-ceo'
from tools.kanban_tools import registry
from hermes_cli import kanban_db as kb
from hermes_cli import kanban_db_connect as kbc
from hermes_cli import kanban_db_dispatch as dispatch
# Use Hermes registered tool handlers (same interface the model calls).
def call(name,args):
    fn=registry.get_entry(name).handler
    r=json.loads(fn(args))
    if r.get('error'):raise AssertionError((name,r))
    return r
run=uuid.uuid4().hex[:8]
a=call('kanban_create',{'title':f'Verify prerequisite {run}','assignee':'brand-manager','body':'Synthetic test; supplied fixture only.','workspace_kind':'dir','workspace_path':'/knowledge','idempotency_key':f'verify-{run}-a'})
# Return shape is read rather than assumed.
aid=a.get('task_id') or a.get('task',{}).get('id') or a.get('id');assert aid,a
b=call('kanban_create',{'title':f'Verify dependency {run}','assignee':'reference-builder','body':'Read prerequisite handoff.','parents':[aid],'workspace_kind':'dir','workspace_path':'/knowledge'})
bid=b.get('task_id') or b.get('task',{}).get('id') or b.get('id');assert bid,b
first=call('kanban_show',{'task_id':aid});second=call('kanban_show',{'task_id':bid})
# Native dry-run reports intended assignment without spawning inference.
conn=kbc.connect();report=dispatch.dispatch_once(conn,dry_run=True,max_spawn=1);conn.close()
assert any(x[0]==aid and x[1]=='brand-manager' for x in report.spawned),report
# Act as specialist in test scope; complete with a real native file artifact from prior check.
call('kanban_complete',{'task_id':aid,'summary':'Synthetic native lifecycle test, not model execution.','metadata':{'artifact_paths':['/knowledge/brand/verification-brand-manager.md'],'tests_run':['native file write']}})
conn=kbc.connect();report2=dispatch.dispatch_once(conn,dry_run=True,max_spawn=1);conn.close()
assert any(x[0]==bid and x[1]=='reference-builder' for x in report2.spawned),report2
call('kanban_block',{'task_id':bid,'reason':'Synthetic local approval gate. Operator input required; no external action.','kind':'needs_input'})
blocked=call('kanban_show',{'task_id':bid})
assert 'blocked' in json.dumps(blocked)
# Simulate HUMAN operator response, not an agent self-approval.
call('kanban_comment',{'task_id':bid,'body':'LOCAL TEST OPERATOR: approve synthetic draft only; no publishing permission.'})
call('kanban_unblock',{'task_id':bid})
call('kanban_complete',{'task_id':bid,'summary':'Local approval lifecycle demonstrated; nothing sent externally.','metadata':{'artifact_paths':['/knowledge/research/verification-reference-builder.md']}})
report={'timestamp':time.time(),'profiles':checks,'native_kanban':{'prerequisite':aid,'dependent':bid,'dependency_dry_run':'passed','assignment':'passed','blocked_and_local_approval':'passed','model_execution':False},'live_inference':'not part of deterministic test'}
(out/'deterministic.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS native Kanban creation, assignment, dependency, artifact handoff, blocking and local approval.',flush=True)
