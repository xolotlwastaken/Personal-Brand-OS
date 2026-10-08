# Skill adaptation review

Reviewed Ootto upstream revision: `5263be7b209fee3f98a59ec185446b8144bca88f`. MIT license and original selected content are preserved under vendor/ootto. All 26 requested skill directories and SKILL.md files exist; 29 profile assignments include three reused skills. The manifest records original/adapted SHA256, upstream revision, dependencies, assignment and validation state.

The third-party install.sh clones a moving repository and copies every skill into ~/.claude/skills. It was inspected and never executed. This project instead ships selected reviewed/adapted native Hermes SKILL.md files. Runtime skill discovery uses Hermes's own skills_list/skill_view, not directory existence alone.

Prompt instructions were rewritten as bounded local procedures based on the reviewed upstream playbooks. Claude-specific wording/paths and connector setup were removed. Native file read/search/write reaches the one /knowledge vault; no Filesystem MCP is required. ai-brain stores evidence in canonical brand/session notes, rather than creating a competing AI Brain memory tree. Private Hermes memory remains independent.

reel-analyzer consumes supplied transcript/visual observations and clearly marks unavailable visual analysis; it cannot claim to have watched a link. competitor-teardown, trend-spotter and comment-mining need supplied dated evidence; no scraping or live trend integration is installed. Numeric claims, unsupported algorithm guarantees, fixed sound-off percentages and hashtag popularity/limit assertions from upstream are not treated as verified facts.

reel-builder is editing-plan only, with source-script references, timing, overlays, missing footage and future renderer requirements. Seedance/Runway, FFmpeg rendering and Remotion are not enabled. going-viral becomes an honest objective/curiosity/retention playbook without fabricated performance promises, lead delivery or automatic DM wiring. comment-responder produces human-reviewable reply/DM drafts only; it does not install a monitor, auto_responses.json or scheduled runner.

The sole executable selected helper is hook-mining/mine_hooks.py. Reviewed before execution: Python standard-library CSV parsing, regex bucketing, supplied-metric ranking and JSON output. No network, install, credential reads or shell execution. The operator may run it inside Docker on supplied data; the hook agent itself has no general terminal tool. Upstream selftest and a labelled synthetic CSV example are part of verification.

content-factory was studied for stage ordering, quality checkpoints and deliverables. Its end-to-end integrations were not run or installed as an active profile skill. Native Kanban owns all orchestration instead.

agent-reach is reference-only. Its router mentions mcporter, OpenCLI, per-platform CLIs, Jina/Exa, GitHub tooling and yt-dlp; several routes need logged-in browser state/cookies, APIs, proxies or downloads. Those introduce dependency/authentication, reliability, rate-limit, consent, copyright and current platform-policy questions that have not been independently verified. A future phase must review each specific backend and platform before installation. This does not claim any route currently works, is policy-compliant, or is enabled.

Dependencies such as Ootto MCP, Filesystem MCP, Apify, Composio, Instagram APIs, Sandcastles, Remotion, Seedance/Runway, Agent Reach and paid media generation are disabled. No prompts are evidence of a working integration. Deterministic checks prove discovery and native file/lifecycle functions; live intended-use examples are separately recorded in the verification report and per-skill manifest.
