import json,subprocess,sys
from pathlib import Path
from hermes_cli.profiles import list_profile_names
root=Path('/opt/data');roles=json.loads(Path('/project/config/agents.json').read_text())
assert set(list_profile_names())-{'default'}==set(roles)
mem=root/'profiles/brand-manager/memories/MEMORY.md';mem.write_text('IDEMPOTENCE TEST: preserve runtime private memory\n')
key=root/'profiles/publisher/.env';key.write_text('# synthetic sentinel, not a usable credential\nNVIDIA_API_KEY=synthetic-do-not-use\n')
knowledge=Path('/knowledge/brand/voice.md');knowledge.write_text('IDEMPOTENCE TEST: preserve runtime vault edits\n')
sentinels={p:p.read_bytes() for p in [mem,key,knowledge]}
subprocess.run([sys.executable,'/project/scripts/provision.py'],check=True)
assert all(p.read_bytes()==data for p,data in sentinels.items())
print('PASS exactly seven named profiles; memory, credential file and edited vault survive repeat provisioning.')
soul=root/'profiles/brand-manager/SOUL.md';soul.write_text('SYNTHETIC runtime identity drift\n')
drift=soul.read_bytes()
result=subprocess.run([sys.executable,'/project/scripts/provision.py'],capture_output=True,text=True)
assert result.returncode==2 and 'DRIFT preserved:' in result.stdout and soul.read_bytes()==drift
subprocess.run([sys.executable,'/project/scripts/provision.py','--apply-drift'],check=True)
assert soul.read_bytes()==Path('/project/config/agents/brand-manager/SOUL.md').read_bytes()
assert (root/'config-backups/profiles/brand-manager/SOUL.md').read_bytes()==drift
assert all(p.read_bytes()==data for p,data in sentinels.items())
print('PASS unknown config drift preserved/reported; explicit apply retains prior copy and private state.')
