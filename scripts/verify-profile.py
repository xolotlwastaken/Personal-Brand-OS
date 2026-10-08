"""Fresh-process profile checks exercise Hermes's actual skill and tool discovery."""
import json, os, sys
from pathlib import Path
profile=sys.argv[1];os.environ['HERMES_HOME']=f'/opt/data/profiles/{profile}';os.environ['HERMES_PROFILE']=profile
# Resolve CLI paths before importing Hermes tool modules.
from hermes_cli.env_loader import load_hermes_dotenv
load_hermes_dotenv()
from tools.skills_tool import skills_list, skill_view
from model_tools import get_tool_definitions
from tools.file_tools import read_file_tool, write_file_tool
roles=json.loads(Path('/project/config/agents.json').read_text());role=roles[profile]
listing=json.loads(skills_list());assert listing.get('success'),listing
found={s['name'] for s in listing['skills']};expected=set(role['skills']);assert expected <= found,(expected-found)
for skill in expected:
    view=json.loads(skill_view(skill));assert view.get('success'),(skill,view)
    assert 'Local Personal Brand OS' in (Path(os.environ['HERMES_HOME'])/'skills'/skill/'SKILL.md').read_text()
tools=get_tool_definitions(enabled_toolsets=role['tools'],quiet_mode=True,skip_tool_search_assembly=True)
names={t['function']['name'] if 'function' in t else t['name'] for t in tools}
assert {'read_file','write_file'}<=names,names
if profile!='brand-ceo': assert not names & {'kanban_list','kanban_unblock'},names
manual_names=sorted(names)
os.environ['HERMES_KANBAN_TASK']='verification-schema-discovery-only'
from model_tools import _clear_tool_defs_cache
_clear_tool_defs_cache()
worker_defs=get_tool_definitions(enabled_toolsets=role['tools'],quiet_mode=True,skip_tool_search_assembly=True)
worker_names={t['function']['name'] if 'function' in t else t['name'] for t in worker_defs}
assert {'kanban_show','kanban_complete','kanban_block'}<=worker_names,worker_names
assert not worker_names & {'kanban_list','kanban_unblock'},worker_names
os.environ.pop('HERMES_KANBAN_TASK')
assert not names & {'terminal','process','send_message','delegate_task','cronjob','browser_navigate','image_generate','skill_hub'},names
if profile=='brand-ceo':assert {'kanban_create','kanban_list'}<=names
assert ('brand_artifact_check' in names)==('brand-validation' in role['tools']),names
# Native file tools: actual authorized specialist write and cross-profile read.
file=f'/knowledge/{role["owned"]}/verification-{profile}.md'
content=f'---\nid: verification-{profile}\nowner: {profile}\nstatus: synthetic-test\n---\n# Shared vault access\nSynthetic permission test; no personal claims.\n'
# Read before overwrite to satisfy native stale-write protection on repeated checks.
if Path(file).exists(): read_file_tool(file)
written=json.loads(write_file_tool(file,content));assert not written.get('error'),written
read=json.loads(read_file_tool(file));assert not read.get('error'),read
assert Path('/knowledge/brand/starting-brief.md').is_file()
assert Path('/knowledge/operations/handoffs.md').is_file()
memory=Path(os.environ['HERMES_HOME'])/'memories'; assert (memory/'MEMORY.md').exists();assert (memory/'USER.md').exists()
result={'profile':profile,'skills_discovered':sorted(expected),'total_skills_visible':len(found),'tools':manual_names,'worker_tools':sorted(worker_names),'native_shared_write':file,'memory':str(memory),'status':'passed'}
print(json.dumps(result))
