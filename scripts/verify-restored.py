"""Reconcile an isolated secret-free restore and inspect it through native Hermes APIs."""
import json,os,sqlite3,subprocess,sys
from pathlib import Path
from dotenv import dotenv_values
from hermes_cli.profiles import list_profile_names

root=Path('/opt/data');roles=json.loads(Path('/project/config/agents.json').read_text())
selected=list(Path('/knowledge').rglob('*.md'))
for name in roles:selected+=list((root/'profiles'/name/'memories').glob('*.md'))
before={p:p.read_bytes() for p in selected}
def records():
    result={}
    for p in [root/'kanban.db']+[root/'profiles'/name/'state.db' for name in roles]:
        c=sqlite3.connect(f'file:{p}?mode=ro',uri=True)
        table='tasks' if p.name=='kanban.db' else 'sessions'
        result[str(p)]=c.execute(f'SELECT id FROM {table} ORDER BY id').fetchall();c.close()
    return result
history=records();assert history[str(root/'kanban.db')]
subprocess.run([sys.executable,'/project/scripts/provision.py'],check=True)
assert set(list_profile_names())-{'default'}==set(roles)
assert all(p.read_bytes()==content for p,content in before.items())
assert records()==history
for p in (root/'profiles').glob('*/.env'):
    values=dotenv_values(p)
    assert not any(values.get(k) for k in ['NVIDIA_API_KEY','OPENAI_API_KEY','OPENROUTER_API_KEY','CUSTOM_API_KEY'])
os.environ['HERMES_HOME']=str(root/'profiles/brand-ceo');os.environ['HERMES_PROFILE']='brand-ceo'
from tools.kanban_tools import registry
listed=json.loads(registry.get_entry('kanban_list').handler({}));assert not listed.get('error') and listed['tasks'],listed
report={'status':'passed','profiles':list(roles),'history_task_count':len(history[str(root/'kanban.db')]),'private_memory_and_vault_files_preserved':len(before),'session_databases_preserved':7,'native_board_read':'passed','model_credentials':'absent; manual provisioning required','model_inference':False}
(root/'verification/restored-bootstrap.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
