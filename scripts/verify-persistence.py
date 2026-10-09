"""Snapshot/compare stable state around an idle container recreation (no model calls)."""
import hashlib, json, sqlite3, sys
from pathlib import Path

root=Path('/opt/data');roles=json.loads(Path('/project/config/agents.json').read_text())
def snapshot():
    files={}
    selected=[root/'config.yaml']+list(Path('/knowledge').rglob('*.md'))+list(Path('/media').rglob('*'))
    for name in roles:
        p=root/'profiles'/name
        selected += [p/'config.yaml',p/'profile.yaml',p/'SOUL.md',p/'.env']
        selected += list((p/'skills').rglob('*'))+list((p/'memories').rglob('*'))+list((p/'sessions').rglob('*'))+list((p/'plugins').rglob('*.py'))
    for p in selected:
        if p.is_file() and '__pycache__' not in p.parts:
            files[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    databases={}
    for p in [root/'kanban.db']+[root/'profiles'/n/'state.db' for n in roles]:
        if not p.exists():continue
        c=sqlite3.connect(f'file:{p}?mode=ro',uri=True)
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok',p
        table='tasks' if p.name=='kanban.db' else 'sessions'
        rows=c.execute(f'SELECT id'+(', status' if table=='tasks' else '')+f' FROM {table} ORDER BY id').fetchall()
        databases[str(p)]=rows;c.close()
    assert databases[str(root/'kanban.db')] and files
    assert not any(status=='running' for _,status in databases[str(root/'kanban.db')]),'Wait for active workers before recreation'
    return {'files':files,'databases':databases}
path=root/'verification/persistence-before.json'
if sys.argv[1]=='before':
    path.write_text(json.dumps(snapshot(),indent=2)+'\n');print('Saved stable file hashes and historical task/session IDs.')
elif sys.argv[1]=='after':
    before=json.loads(path.read_text());after=snapshot()
    assert before==json.loads(json.dumps(after)),'Persistent files or task/session records changed during recreation'
    report={'status':'passed','files_checked':len(after['files']),'databases_checked':len(after['databases']),'scope':'profile config, skills, SOUL, memories, sessions, plugins, vault, media; SQLite integrity and historical task/session IDs'}
    (root/'verification/persistence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
else:raise SystemExit('Use before or after')
