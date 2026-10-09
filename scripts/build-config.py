"""Development-only adapter; upstream is reviewed, never execute its installer."""
from pathlib import Path
import json, shutil, subprocess, hashlib
root=Path(__file__).resolve().parent.parent
up=root/'.upstream/content'; rev=subprocess.check_output(['git','-C',str(up),'rev-parse','HEAD'],text=True).strip()
roles={
 'brand-ceo':('Content Operations Manager','Coordinate, assign native Kanban tasks with dependencies, inspect handoff artifacts, review quality and consolidate results. Delegate research, hooks, scripts, editing and publication packages to their owners. Never perform their work directly.','operations','analytics-readout content-audit content-calendar'),
 'brand-manager':('Personal Brand Strategist','Interview the user; develop evidence-led positioning, personas, pillars and series. Own canonical brand documents. Propose major strategy changes for human approval before committing them.','brand','ai-brain audience-personas positioning-audit content-pillar-builder series-planner content-calendar'),
 'reference-builder':('Content Researcher and Reference Analyst','Analyze supplied references, transcripts, mock observations and links. Distinguish observations from explanations. Record source links, reusable techniques, recommendations and uncertainties. A URL alone does not mean you watched a video.','research','reel-analyzer competitor-teardown trend-spotter comment-mining'),
 'hook-writer':('Short-Form Hook Specialist','Write spoken and on-screen hooks, rank them by objective, clarity, truthfulness, curiosity and audience fit; recommend the top three. Never promise results the content cannot deliver.','content/hooks','going-viral hook-mining viral-hook-writer ab-hook-tester'),
 'script-writer':('Instagram Reel Scriptwriter','Use approved context, research and hook handoffs to write natural 30–60 second scripts with timed shots, on-screen text, B-roll, transitions and one deliverable CTA. Flag missing personal facts.','content/scripts','reel-scripter b-roll-shot-list cta-writer on-screen-text-writer'),
 'video-editor':('Video Editor and Motion Graphics Specialist','Consume approved scripts; produce validated editing plans with shot sequence, timing, captions, graphics, missing footage and future rendering requirements. Manage supplied test media. Rendering and generation integrations are disabled.','content/production-plans','reel-builder b-roll-shot-list on-screen-text-writer cover-thumbnail-brief'),
 'publisher':('Social Media Publisher and Engagement Manager','Produce draft captions, hashtags, posting proposals in Asia/Singapore, approval checklists and engagement drafts. Record only supplied analytics. ALL external publishing, messaging, account changes, automated comments and DMs are disabled.','content/publication-packages','caption-and-hashtags best-time-scheduler comment-responder dm-script-writer'),
}
methods={
'analytics-readout':'Use supplied figures only. Choose the metric for the stated goal, compare with the user\'s median when provided, locate evidenced retention drops, suggest two actions, and state missing signal.',
'content-audit':'Calculate median and evidenced outliers from supplied posts. Compare traits only where data supports it. Return stop/keep/test and five justified ideas; never invent metrics.',
'content-calendar':'Draft a two-week table: day, pillar, format, working hook, goal. Rotate pillars and formats; include a batching suggestion and three reserve ideas. Scheduling is a proposal only.',
'ai-brain':'Search /knowledge/brand and relevant /knowledge notes with native file search/read tools. Save append-only session evidence under /knowledge/brand/sessions/<task-id>-<slug>.md. Link canonical notes. Do not create an AI Brain folder or separate memory store. Private memory stays in this profile\'s Hermes memories directory. Strategy changes await human approval.',
'audience-personas':'Group supplied interviews, comments or reviews by job, desired outcome, objections and exact language. Cite evidence and confidence. Do not invent demographics or treat a single comment as a market-wide claim.',
'positioning-audit':'Map current and supplied competitor messages: audience, promise, mechanism, proof, CTA. Propose the smallest supported change. Bracket missing proof and stop at diagnosis when proof is absent. Require approval for major positioning changes.',
'content-pillar-builder':'Propose three to five themes with point of view, audience need, rotation, one positioning sentence and exclusions. Audit supplied posts if available. Label proposals and keep user opinions unconfirmed until supplied.',
'series-planner':'Propose three to five series names, repeatable beats, twelve episode ideas, a reason to follow and production requirements. Estimate effort as an estimate. No fabricated prior results.',
'reel-analyzer':'Analyze ONLY supplied transcript, timestamped visual observations or mock reference. Return hook, ordered beats, pacing, observed visuals, reusable techniques and an original remake idea. Mark unavailable frame analysis and performance data explicitly.',
'competitor-teardown':'Use supplied posts/metrics only. Map hooks, format, cadence and recurring promise; identify hypotheses, confidence, original adaptation and missing data. Never claim account access or causation from observational evidence.',
'trend-spotter':'Use dated supplied references to separate repeated observed themes from one-off anecdotes. Return topic, source/date, brand fit, hypothesis and expiry/recheck date. No live trend claims without live sources.',
'comment-mining':'Cluster supplied comments by recurring questions, objections and exact phrasing. Cite comment IDs and counts from the fixture, then propose topics. Do not access platforms or collect new comments.',
'going-viral':'Choose the content objective, a truthful curiosity gap, specific stakes and an original visual opener. Build clear beats that deliver the promised payoff and one save/share/follow CTA. Treat all virality claims as hypotheses; do not invent conversion percentages or promise automated DMs.',
'hook-mining':'Use supplied CSV performance data. The reviewed stdlib helper ranks hooks by the actual supplied metric and groups psychological patterns. Hold mechanism and specificity, write original language, and only use verified personal numbers. With no measurements, mark pattern analysis synthetic and ranking qualitative.',
'viral-hook-writer':'Create five original spoken hooks with on-screen variants. Rank by clarity, audience fit, curiosity, credible payoff and voice. Recommend top three with reasons and flag unsupported claims.',
'ab-hook-tester':'Draft two hook variants while keeping the rest of the proposed Reel constant. Define objective, outcome metric, controlled variables, observation window and decision rule. Produce a test plan only, no posts or fabricated winners.',
'reel-scripter':'Write a 30–60 second hook/context/value/payoff/CTA script, default 45 seconds for the demo. Include spoken lines, timed shots, overlays and B-roll. Estimate speech at 130–160 words/minute; for 45 seconds aim 95–115 spoken words. Use bracketed missing facts; never turn hypothetical demonstration into autobiography.',
'b-roll-shot-list':'Map every approved script line to essential or optional footage. Group filming order by location/setup. Include angle, duration, line covered, kit, and licensed stock search terms as suggestions.',
'cta-writer':'Choose one clear, truthful ask and give a reason line, spoken/on-screen versions and placement. Prefer save or follow. Do not offer keyword-to-DM delivery while its integration is disabled.',
'on-screen-text-writer':'Write concise overlays per beat, one emphasized word, appearance cue and timing. Check mute readability and flag lines over seven words. Do not claim a sound-off viewing percentage without evidence.',
'reel-builder':'Translate an approved script into a beat-by-beat editing plan: spoken line reference, overlay, visual, cut, duration, caption style and missing footage. Verify timing and source links. Do not rewrite the specialist\'s script or render/generate video. Future FFmpeg/Remotion/Seedance integrations require separate review.',
'cover-thumbnail-brief':'Give three cover text options of three to five words, ranked for legibility, visual composition, contrast, grid fit and a 150px readability check. Safe areas are provisional; verify current platform specifications before production.',
'caption-and-hashtags':'Draft a strong first line, two to four useful lines, one CTA, a small relevant hashtag/keyword set, a first-comment DRAFT and alt text. Do not invent hashtag popularity counts or treat upstream hashtag limits as current platform facts.',
'best-time-scheduler':'Use supplied audience activity and timezone data. Without data, clearly label proposed slots as hypotheses. Include sustainable cadence, slot purpose and a test plan; do not activate scheduling or publishing.',
'comment-responder':'For supplied synthetic comments, draft appropriate public responses and optional DM copy for human review. Do not say a DM was sent, promise automatic delivery, create auto_responses.json, install a monitor, schedule a runner or execute any external action. Unknown comments go to human review.',
'dm-script-writer':'Draft only: resource delivery, one qualifying question and branches for interested/not now/wrong fit/no reply. Keep copy concise, do not invent an offer or resource. All sending disabled; platform messaging rules must be reviewed before any future integration.',
}
common='''Use Hermes native file and skills tools, never Claude connectors or installers. Shared vault: /knowledge; media: /media. Inputs are supplied by the task contract, not fetched by imaginary integrations. Follow /knowledge/operations/conventions.md and /knowledge/operations/handoffs.md. Include actual Kanban task_id, owner, status, sources, assumptions and artifact paths. Do not fabricate experiences, opinions, achievements or statistics. Missing data stays explicitly missing. Never infer retention, causal effects or post formats from views/saves alone. Label proposed hooks, pillars, scheduling times and diagnoses as hypotheses. Use brackets for missing first-person history or resource promises. All social publishing, messaging, scraping, expensive generation and rendering are disabled. Prompt playbooks are not tool integrations.'''
manifest={'upstream':{'url':'https://github.com/Ootto-AI/claude-content-skills','revision':rev,'license':'MIT'},'skills':[]}
for name,method in methods.items():
 src=up/'skills'/name
 assert (src/'SKILL.md').is_file(),name
 dst=root/'vendor/ootto'/name;shutil.copytree(src,dst,dirs_exist_ok=True)
 shutil.copy2(up/'LICENSE',root/'vendor/ootto/LICENSE')
 orig=(src/'SKILL.md').read_text();services=[x for x in ['Ootto MCP','Filesystem MCP','agent-reach','Remotion','Seedance','Runway','Sandcastles'] if x.lower() in orig.lower()]
 target=root/'config/skills'/name;target.mkdir(parents=True,exist_ok=True)
 text=f'---\nname: {name}\ndescription: "Local Personal Brand OS {name} playbook; supplied evidence, Markdown handoffs, draft outputs."\nlicense: MIT\nmetadata:\n  author: Ootto; adapted for Personal Brand OS\n  upstream_revision: {rev}\n---\n\n# {name}\n\n## Scope and inputs\n\n{common}\n\n## Procedure\n\n{method}\n\n## Finish\n\nPersist the output requested by the task, read it back, check acceptance criteria, and report it using kanban_complete with a summary and artifact paths in metadata. If essential input is missing, use kanban_block with kind needs_input; never silently complete. Ask the CEO for cross-owner changes and human approval for major strategy changes.\n\n## Attribution\n\nAdapted from [Ootto content skills](https://github.com/Ootto-AI/claude-content-skills/tree/{rev}/skills/{name}) at `{rev}`. The original is preserved under /project/vendor/ootto/{name}; the MIT license is included. Upstream instructions are reference material only; use this adapted procedure.\n'
 (target/'SKILL.md').write_text(text);shutil.copy2(up/'LICENSE',target/'LICENSE')
 if name=='hook-mining':
  shutil.copy2(src/'mine_hooks.py',target/'mine_hooks.py')
  with (target/'SKILL.md').open('a') as f:f.write('\nThe host operator can run the reviewed helper inside Docker: `python /opt/data/profiles/hook-writer/skills/hook-mining/mine_hooks.py <supplied.csv>`. The agent has no general terminal tool; it can inspect CSV with file tools.\n')
 manifest['skills'].append({'name':name,'profiles':[p for p,r in roles.items() if name in r[3].split()],'source_revision':rev,'original_sha256':hashlib.sha256((src/'SKILL.md').read_bytes()).hexdigest(),'adapted_sha256':hashlib.sha256((target/'SKILL.md').read_bytes()).hexdigest(),'declared_dependencies':services,'runtime_dependencies':['Hermes file/skills/kanban tools']+(['Python stdlib helper (operator only)'] if name=='hook-mining' else []),'external_integrations':'disabled','helper_review':'stdlib-only CSV/JSON parser, reviewed before selftest' if name=='hook-mining' else 'no executable helpers','validation':{'directory':'passed','SKILL.md':'passed','discovery':'pending runtime verification','intended_use':'pending; deterministic and live results recorded in data/hermes/verification'}})
(root/'config/skills-manifest.yaml').write_text(json.dumps(manifest,indent=2)+'\n')
for profile,(title,desc,owned,skills) in roles.items():
 path=root/'config/agents'/profile;path.mkdir(parents=True,exist_ok=True)
 tools=['file','skills','memory']+(['kanban'] if profile=='brand-ceo' else [])+(['brand-validation'] if profile in {'brand-ceo','script-writer','video-editor'} else [])
 config={'_config_version':50,'model':{'default':'${BRAND_MODEL}','provider':'${BRAND_PROVIDER}','base_url':'${BRAND_BASE_URL}'},'platform_toolsets':{s:tools for s in ['cli','api_server','telegram','discord','slack']},'agent':{'max_turns':24,'gateway_timeout':180,'reasoning_effort':'low'},'terminal':{'backend':'local','cwd':'/knowledge','home_mode':'profile'},'skills':{'creation_nudge_interval':0},'memory':{'memory_enabled':True,'user_profile_enabled':True},'kanban':{'auto_decompose':False,'orchestrator_profile':'brand-ceo','default_assignee':'brand-ceo','dispatch_in_gateway':True,'dispatch_interval_seconds':15,'max_in_progress':1,'max_in_progress_per_profile':1,'failure_limit':1,'review_dispatch':False,'dispatch_profiles':list(roles)},'tool_loop_guardrails':{'non_interactive_hard_stop_enabled':True}}
 if profile in {'brand-ceo','script-writer','video-editor'}:config['plugins']={'enabled':['artifact-validator']}
 (path/'config.yaml').write_text(json.dumps(config,indent=2)+'\n')
 (path/'profile.yaml').write_text(json.dumps({'description':desc,'display_name':title,'description_auto':False},indent=2)+'\n')
 soul=f'''# {profile} — {title}

{desc}

## Identity and evidence

{common}
Read /knowledge/brand/starting-brief.md and the relevant canonical notes. The initial brief is user-supplied starting context, not completed brand discovery. Preserve natural, personal, practical language. Do not assert the user performed a workflow merely because the requested topic uses "I used AI"; explicitly bracket missing personal details.

## Ownership and tools

Own /knowledge/{owned}/. CEO reads all and coordinates revisions. Brand Manager owns canonical /knowledge/brand. Each role writes only its own outputs or explicitly authorized changes. Shared files are a collaboration convention, not a filesystem isolation boundary. Toolsets: {', '.join(tools)}. No terminal, browser, web, cronjob, delegation, skill installation, send_message or social tools. No external publishing/DMs, account changes, expensive media jobs or rendering.
For a task create a unique filename containing the real task ID. With one dispatcher worker per profile, concurrent same-owner writes are limited. Never overwrite canonical notes while another conversation is editing them; write a proposal and request review. Native file write uses atomic replacement; unique files avoid cross-profile collisions.

## Input contract

Task title, objective, assignee, context, artifact paths, output requirements, acceptance criteria, parent dependencies. Start every dispatcher task with kanban_show (defaults to your actual task). Read only relevant artifacts; parent handoff summaries supply context, not permission to invent facts.

## Output and completion

Write Markdown with YAML frontmatter: id, task_id, owner, created (actual current date in Asia/Singapore; date-only is preferred when no clock tool is available), status, sources, assumptions, approval. Use /knowledge/operations/handoffs.md for your format. Read back and validate the file. Then call kanban_complete with a concise summary and metadata containing artifact_paths, tests_run and uncertainties. A final chat response alone does not close a card. If missing information prevents useful work, use kanban_block(kind="needs_input") with a precise question. For missing footage/integration use kind="capability". Request CEO review for cross-owner changes. Keep private memory in your own profile, never another profile's memories.
Human must approve publication, DMs, irreversible actions, major strategy changes and expensive generation. For the local demo create blocked needs_input approval cards; only the operator explicitly records approval. Completion of a draft does not grant external action authority.

## Installed playbooks

{', '.join(skills.split())}
'''
 if profile=='publisher':
  soul+='\n## Resource and personal-claim gate\n\nNever write first-person resource ownership or quantified time/result claims without supplied evidence. Bracket missing resources in EVERY reply, caption and DM draft. A short overview is not a copy-paste prompt pack. Do not promise unavailable resource delivery. Proposed cadence is a hypothesis; changes to the user daily-Reel goal require human approval.\n'
 if profile=='brand-ceo':soul+='''
## Native orchestration

Use kanban_create, kanban_list, kanban_show and parent links; never delegate_task or direct SQLite writes. For a Reel create brand-manager brief → reference-builder research → hook-writer hooks → script-writer script → brand-ceo review, with each downstream card parents set to its prerequisite task ID. Each card must specify persistent artifact paths, input paths, acceptance criteria, workspace_kind=dir, workspace_path=/knowledge and max runtime where supported. Read returned IDs and use them in subsequent parent links. Do not make dependent specialists children of your unfinished orchestration card (that deadlocks); dependencies are between the actual producing cards. If running as a dispatcher orchestrator, complete your planning card once the graph exists; the separately scheduled review card waits for script completion. For the initial test never invoke video-editor or publisher. Auto decomposition stays disabled. Inspect blockers and task status, report artifact links and unresolved human inputs. Never self-approve a human approval card.
'''
 if profile in {'brand-ceo','script-writer','video-editor'}:soul+='\nUse brand_artifact_check before script completion/review. Fix measured word-count, timing, per-shot speaking-rate and future-timestamp errors through specialist revisions. Use ## Spoken Script and a timed table with Duration / Spoken Line columns.\n'
 (path/'SOUL.md').write_text(soul)
(root/'config/agents.json').write_text(json.dumps({p:{'role':r[0],'description':r[1],'owned':r[2],'skills':r[3].split(),'tools':['file','skills','memory']+(['kanban'] if p=='brand-ceo' else [])+(['brand-validation'] if p in {'brand-ceo','script-writer','video-editor'} else [])} for p,r in roles.items()},indent=2)+'\n')
print('Generated 7 profile templates,',len(methods),'adapted skills,',sum(len(r[3].split()) for r in roles.values()),'assignments.')
