"""Native plugin checks: factual counting, pacing, traversal, symlinks and size bounds."""
import json,os
from pathlib import Path
os.environ['HERMES_HOME']='/opt/data/profiles/brand-ceo';os.environ['HERMES_PROFILE']='brand-ceo'
from hermes_cli.plugins import discover_plugins
discover_plugins()
from tools.kanban_tools import registry
fn=registry.get_entry('brand_artifact_check').handler
base=Path('/knowledge/operations/validation-fixtures');base.mkdir(exist_ok=True)
hook='A simple planning framework you can try today' # eight literal words
remaining=' '.join(['synthetic']*97)
p=base/'good.md';p.write_text(f'---\nowner: brand-ceo\ncreated: 2026-10-09\nstatus: synthetic-test\n---\n## Spoken Script (105 words)\n\n> {hook}\n> {remaining}\n\n---\n## Timed Shots\n\n| Beat | Time | Duration | Spoken Line |\n| --- | --- | --- | --- |\n| Hook | 0–3s | 3s | {hook} |\n| Body | 3–45s | 42s | {remaining} |\n')
good=json.loads(fn({'path':str(p)}));assert good['valid'] and good['spoken_words']==105 and good['shot_total_seconds']==45,good
bad=base/'bad.md';bad.write_text(p.read_text().replace('(105 words)','(10 words)').replace('| 3s |','| 1s |').replace('| 42s |','| 44s |'))
r=json.loads(fn({'path':str(bad)}));assert not r['valid'] and any('Declared' in e for e in r['errors']) and any('words/minute' in e for e in r['errors']),r
assert json.loads(fn({'path':'/opt/data/config.yaml'})).get('error')
assert json.loads(fn({'path':'/knowledge/../../opt/data/config.yaml'})).get('error')
link=base/'outside.md';link.unlink(missing_ok=True);link.symlink_to('/opt/data/config.yaml');assert json.loads(fn({'path':str(link)})).get('error');link.unlink()
big=base/'big.md';big.write_text('x'*262145);assert json.loads(fn({'path':str(big)})).get('error');big.unlink()
Path('/opt/data/verification/validator.json').write_text(json.dumps({'status':'passed','good':good,'bad':r,'security':['outside-root','traversal','symlink-escape','oversize']},indent=2)+'\n')
print('PASS native read-only validator, accurate word/timing checks and path/size restrictions.')
