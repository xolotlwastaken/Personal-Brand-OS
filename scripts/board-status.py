"""Compact native-board snapshot; does not run inference or mutate SQL."""
import os,json,sys
os.environ['HERMES_HOME']='/opt/data/profiles/brand-ceo';os.environ['HERMES_PROFILE']='brand-ceo'
from tools.kanban_tools import registry
r=json.loads(registry.get_entry('kanban_list').handler({'tenant':sys.argv[1] if len(sys.argv)>1 else 'brand-os-e2e'}))
if r.get('error'):raise RuntimeError(r)
for task in r['tasks']:print(task['id'],task['assignee'],task['status'],task['title'])
