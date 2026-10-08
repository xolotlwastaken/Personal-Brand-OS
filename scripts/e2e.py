"""Submit a bounded real CEO task. Only native gateway dispatch executes agents."""
import json, os, sys, time
from pathlib import Path
os.environ['HERMES_HOME']='/opt/data/profiles/brand-ceo';os.environ['HERMES_PROFILE']='brand-ceo'
from hermes_cli.env_loader import load_hermes_dotenv
load_hermes_dotenv()
from tools.kanban_tools import registry

def call(name,args):
    r=json.loads(registry.get_entry(name).handler(args))
    if r.get('error'):raise RuntimeError(r)
    return r
body='''User request: "Create a 45-second Instagram Reel about how I used AI to plan my personal brand."
This is a bounded synthetic end-to-end infrastructure test with a REAL model and REAL named workers. Do not invoke video-editor or publisher. No external research, posts, messages, renders, or generation.

Your ONLY job on this planning card is create exactly FIVE downstream native Kanban cards in this sequence, then complete THIS planning card. Each card uses workspace_kind=dir, workspace_path=/knowledge, max_runtime_seconds=300, tenant=brand-os-e2e. Use returned real task IDs for parents. Do NOT set this planning card as a parent (that would deadlock). Capture graph IDs in your completion metadata. Do not write their deliverables yourself.

1. brand-manager: Read /knowledge/brand/starting-brief.md and canonical voice/audience notes. Create a short brand brief for the request. Explicitly say no actual AI planning steps or results were provided; authorize a hypothetical process with placeholders, not a fabricated first-person experience. Output /knowledge/content/ideas/<ACTUAL_TASK_ID>-brand-brief.md. Acceptance: topic, objective, audience, angle, voice, missing facts, source links. No major strategy changes. Use skills content-pillar-builder and audience-personas.
2. reference-builder: parents=[step1 ID]. Read predecessor handoff artifact and /knowledge/research/references/synthetic-ai-brand-planning.md. Produce research brief ONLY from those synthetic supplied references. Include source IDs and mock URLs, observed format/beat patterns, five useful hook angles, qualitative hypotheses, performance data unavailable. Output /knowledge/research/references/<ACTUAL_TASK_ID>-research.md. Use reel-analyzer and comment-mining.
3. hook-writer: parents=[step2 ID]. Read preceding research and brief. Write exactly five original spoken hooks with on-screen variants, rank by truthfulness, relevance, clarity and curiosity, recommend top three and choose one. No made-up personal experiences/numbers, no keyword-DM CTA. Output /knowledge/content/hooks/<ACTUAL_TASK_ID>-hooks.md. Use viral-hook-writer and going-viral.
4. script-writer: parents=[step3 ID]. Read brief, research and hooks from persistent predecessor artifacts. Write a complete 45-second Reel draft, 95–115 actual spoken words, chosen hook, timed shot table totaling 45 seconds, captions/on-screen text, B-roll, transitions and ONE save/follow CTA. Use ## Spoken Script and a shot table with Duration / Spoken Line columns; call brand_artifact_check and fix errors until valid=true before completion. Use actual current date without invented clock time. Avoid unsupported universal claims and promising unavailable caption resources. Since actual user steps/results are missing, keep first-person autobiographical specifics as explicit brackets; prominently label the process hypothetical and not publishable until confirmed. Output /knowledge/content/scripts/<ACTUAL_TASK_ID>-reel-script.md. Use reel-scripter, b-roll-shot-list, on-screen-text-writer and cta-writer.
5. brand-ceo: parents=[step4 ID]. Inspect all four actual files by reading ancestor handoffs. Review exactly five hooks/top three, truthfulness, missing personal details, measured word count, 45-second shot timings, audience fit, B-roll, captions and CTA. Call brand_artifact_check on the script and require valid=true. If criteria fail, request revisions via separate named specialist tasks; do not rewrite their work. Persist a review /knowledge/operations/reviews/<ACTUAL_TASK_ID>-e2e-review.md with graph IDs, artifact links, findings and remaining user inputs. Complete after review. The draft may pass infrastructure acceptance while remaining explicitly unapproved for publishing.

EVERY task body must include objective, context, input artifacts, output format, acceptance criteria and dependency IDs. Every worker starts with kanban_show, writes a Markdown artifact with real task_id/owner/status/sources, reads it back, calls kanban_complete(summary, metadata={artifact_paths:[...]}) only after acceptance. Final chat text alone is not completion. Use kanban_block only if infrastructure cannot execute; supplied mock references suffice. Run goal_mode=false, no auxiliary judge.
'''
result=call('kanban_create',{'title':'E2E: CEO plan 45-second AI personal brand Reel','assignee':'brand-ceo','body':body,'workspace_kind':'dir','workspace_path':'/knowledge','tenant':'brand-os-e2e','max_runtime_seconds':300,'idempotency_key':'brand-os-e2e-v1','completion_contract':'local-only'})
Path('/opt/data/verification').mkdir(exist_ok=True)
Path('/opt/data/verification/e2e-submission.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
