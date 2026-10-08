"""Ask CEO to create measured specialist revision and follow-up review through Kanban."""
import os,json,datetime
from pathlib import Path
from zoneinfo import ZoneInfo
os.environ['HERMES_HOME']='/opt/data/profiles/brand-ceo';os.environ['HERMES_PROFILE']='brand-ceo'
from tools.kanban_tools import registry
from hermes_cli.plugins import discover_plugins
discover_plugins()
rows=json.loads(registry.get_entry('kanban_list').handler({'tenant':'brand-os-e2e'}))['tasks']
original=next(t for t in rows if t['assignee']=='script-writer')
artifact=next(Path('/knowledge/content/scripts').glob(original['id']+'-*.md'))
measured=json.loads(registry.get_entry('brand_artifact_check').handler({'path':str(artifact)}))
if measured.get('valid'):
    print('Original draft passes deterministic validation; no revision needed.');raise SystemExit(0)
body='''Operator review of the initial completed E2E draft found issues missed by the first review. Read /knowledge/content/scripts/t_b81ce578-reel-script.md and run brand_artifact_check on it. Actual spoken count is 116, not the declared 103, and the first shot is 18 words in 3 seconds (360 WPM). The creation timestamp is invented/future. "Everyone" is an unsupported universal claim, and "prompts in caption" promises a missing resource. The new read-only native validation tool is installed in your profile and the script-writer profile.
Your planning responsibility ONLY: create ONE script-writer revision task under tenant brand-os-e2e-revision with parents=[t_b81ce578], workspace dir:/knowledge, max_runtime_seconds=300, priority=20, then ONE brand-ceo follow-up review under same tenant with parent=[returned revision ID], same workspace/runtime/priority. Do not rewrite the script yourself. Complete this planning card with both returned IDs.
Revision task acceptance: read original brief/research/hooks/script; revise spoken copy to 95–115 ACTUAL words, accurately state count, shorten hook and allocate realistic beat timings totaling 45 seconds. Use ## Spoken Script and one timed table with columns Beat, Time, Duration, Spoken Line, On-Screen Text, Visual, Transition. The validation tool measures rates; every spoken shot <=180 WPM. Preserve hypothetical/missing-personal-details label, audience/voice, B-roll, captions, ONE truthful save/follow CTA; remove unsupported universal claim and unavailable caption resource promise. Use creation date 2026-10-09 without fabricated clock time. Write a NEW task-ID named script artifact /knowledge/content/scripts/<ACTUAL_TASK_ID>-revised-reel-script.md; do not overwrite original. Call brand_artifact_check, fix errors until valid=true, read back, then kanban_complete metadata artifact_paths and measured_words/duration.
Follow-up CEO acceptance: read revised artifact and brand_artifact_check result; validate valid=true, factual limitations, shot/B-roll/caption completeness and actual count. Write /knowledge/operations/reviews/<ACTUAL_TASK_ID>-revised-e2e-review.md with original graph IDs, revision ID, validation measurements, linked artifacts and user-input requirements. Complete only once checks pass; publishing remains disabled/unapproved. This final review supersedes the first CEO review's mistaken measurement acceptance.
No video-editor or publisher tasks in this revision workflow. No external actions or temporary subagents.
'''
body=body.replace('/knowledge/content/scripts/t_b81ce578-reel-script.md',str(artifact)).replace('t_b81ce578',original['id']).replace('2026-10-09',str(datetime.datetime.now(ZoneInfo('Asia/Singapore')).date()))
body=body.replace('Actual spoken count is 116, not the declared 103, and the first shot is 18 words in 3 seconds (360 WPM). The creation timestamp is invented/future.', 'Measured validation result: '+json.dumps(measured)+'.')
r=json.loads(registry.get_entry('kanban_create').handler({'title':'CEO: coordinate measured E2E script revision','assignee':'brand-ceo','body':body,'workspace_kind':'dir','workspace_path':'/knowledge','tenant':'brand-os-e2e-revision','max_runtime_seconds':300,'priority':20,'idempotency_key':'brand-os-e2e-measured-revision-v1'}))
print(json.dumps(r,indent=2))
