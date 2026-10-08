"""Submit seven bounded live skill-example cards, after the initial E2E review."""
import json,os
from pathlib import Path
os.environ['HERMES_HOME']='/opt/data/profiles/brand-ceo';os.environ['HERMES_PROFILE']='brand-ceo'
from hermes_cli.env_loader import load_hermes_dotenv
load_hermes_dotenv()
from tools.kanban_tools import registry

def call(name,args):
 r=json.loads(registry.get_entry(name).handler(args))
 if r.get('error'):raise RuntimeError(r)
 return r
roles=json.loads(Path('/project/config/agents.json').read_text())
board=call('kanban_list',{'tenant':'brand-os-e2e'})
reviews=[t for t in board['tasks'] if t['assignee']=='brand-ceo' and t['parents']]
assert len(reviews)==1,'First create the initial E2E graph; exactly one review expected'
review=reviews[0]['id'];submissions=[]
for name,role in roles.items():
 body=f'''Separate bounded skill intended-use smoke test, AFTER the initial Reel E2E. This is not part of the initial E2E and must do no external action.
Objective: demonstrate every assigned adapted playbook using supplied synthetic inputs. Skills are force-loaded: {', '.join(role['skills'])}. Follow their procedures but complete this task only after ALL examples below exist in one file. Do not invoke another profile, create more tasks or execute terminal commands.
Input fixture (synthetic, NOT user history): three posts P1 views=100 saves=10, P2 views=50 saves=5, P3 views=25 saves=1. Known median views=50, saves=5. Goal=saves. Hypothetical audience=nontechnical creators with many ideas and no weekly plan. Supplied mock comment C1="I have ideas but no plan", C2="How do I keep AI copy sounding like me?", C3="Can I do this without coding?". Use /knowledge/research/references/synthetic-ai-brand-planning.md for supplied format/timing observations. Use /knowledge/brand/starting-brief.md for actual starting context. For script/editing examples, read the completed demo script from the predecessor CEO review's linked artifacts. For missing proof, offer, media, audience activity or actual personal outcomes, explicitly state missing rather than invent them. Test media manifest is /media/incoming/synthetic-test-media.txt.
Output: /knowledge/{role['owned']}/<ACTUAL_TASK_ID>-skill-examples.md. YAML frontmatter with task_id, owner, created=ACTUAL DATE ONLY (never invented clock time), status=synthetic-test, sources, approval=not-required-for-draft. One section headed EXACTLY "## <skill-name>" for EACH of {', '.join(role['skills'])}. Under each give its supplied input, a small concrete intended-use output (2–6 lines, table fragments where useful), and what this does NOT validate (external integration/performance). Max 650 words total. Examples must actually implement the procedure, not say "I would do it". ai-brain can demonstrate a linked evidence/session note section without modifying canonical strategy. Content-calendar needs a small actual calendar table; analytics needs computed median/outlier and two actions; research needs observed source/pattern; hooks need actual hook variants/rank or A/B metric; scripts/shot lists need actual lines/timing; editing needs actual cut plan; captions/DMs need actual labelled DRAFT copy; schedule needs proposed times labelled hypotheses. No credential or OAuth access, posting, sending, watching unsupplied videos, scraping, rendering or expensive generation.
Acceptance: all assigned section names, evidence-labelled mini outputs, truthful missing data, real persistent artifact, native read-back. Then kanban_complete with summary and metadata containing artifact_paths and skills_tested. If inability to demonstrate one skill, explicitly report that section as unverified and mark task blocked rather than claim success.
'''
 r=call('kanban_create',{'title':f'Skill examples: {name} (synthetic local drafts)','assignee':name,'body':body,'parents':[review],'workspace_kind':'dir','workspace_path':'/knowledge','tenant':'brand-os-skills','max_runtime_seconds':300,'priority':-10,'skills':role['skills'],'idempotency_key':f'brand-os-skill-examples-v1-{name}'})
 submissions.append({'profile':name,**r})
Path('/opt/data/verification/skill-submissions.json').write_text(json.dumps(submissions,indent=2)+'\n')
print(json.dumps(submissions,indent=2))
