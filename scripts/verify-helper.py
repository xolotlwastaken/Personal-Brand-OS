"""Run the reviewed Ootto helper on labelled synthetic input; no network."""
from pathlib import Path
import subprocess,sys,json
p=Path('/media/incoming/synthetic-hooks.csv')
p.write_text('Hook Text,Synthetic Test Views,Source\nHow to make one week of content ideas,100,synthetic-A\nStop making your content plan too complicated,50,synthetic-B\nThree questions for your next content plan,25,synthetic-C\n')
helper='/opt/data/profiles/hook-writer/skills/hook-mining/mine_hooks.py'
subprocess.run([sys.executable,helper,'--selftest'],check=True)
subprocess.run([sys.executable,helper,str(p)],check=True)
r=json.loads(p.with_suffix('.mined.json').read_text());assert r['total']==3
values=[x['metric'] for rows in r['buckets'].values() for x in rows];assert sorted(values)==[25,50,100]
print('PASS reviewed hook-mining helper synthetic CSV; measurements are fixtures, not actual account data.')
