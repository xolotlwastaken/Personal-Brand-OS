# Skill adaptation review

Reviewed Ootto upstream revision: `5263be7b209fee3f98a59ec185446b8144bca88f`. MIT license and original selected content are preserved under vendor/ootto. All 26 requested skill directories and SKILL.md files exist; 29 profile assignments include three reused skills. The manifest records original/adapted SHA256, upstream revision, dependencies, assignment and validation state.

The third-party install.sh clones a moving repository and copies every skill into ~/.claude/skills. It was inspected and never executed. This project instead ships selected reviewed/adapted native Hermes SKILL.md files. Runtime skill discovery uses Hermes's own skills_list/skill_view, not directory existence alone.

Prompt instructions were rewritten as bounded local procedures based on the reviewed upstream playbooks. Claude-specific wording/paths and connector setup were removed. Native file read/search/write reaches the one /knowledge vault; no Filesystem MCP is required. ai-brain stores evidence in canonical brand/session notes, rather than creating a competing AI Brain memory tree. Private Hermes memory remains independent.

reel-analyzer, competitor-teardown and trend-spotter can consume supplied evidence or evidence retrieved through the bounded reference-acquisition native plugin. Search snippets and URLs alone are not viewed-video evidence; actual machine transcripts and sampled-frame observations have explicit limitations. Comment-mining still requires supplied comments; reference retrieval does not enable comment scraping. Numeric claims, unsupported algorithm guarantees, fixed sound-off percentages and hashtag popularity/limit assertions from upstream are not treated as verified facts.

reel-builder is editing-plan only, with source-script references, timing, overlays, missing footage and future renderer requirements. Seedance/Runway, FFmpeg rendering and Remotion are not enabled. going-viral becomes an honest objective/curiosity/retention playbook without fabricated performance promises, lead delivery or automatic DM wiring. comment-responder produces human-reviewable reply/DM drafts only; it does not install a monitor, auto_responses.json or scheduled runner.

The sole executable selected helper is hook-mining/mine_hooks.py. Reviewed before execution: Python standard-library CSV parsing, regex bucketing, supplied-metric ranking and JSON output. No network, install, credential reads or shell execution. The operator may run it inside Docker on supplied data; the hook agent itself has no general terminal tool. Upstream selftest and a labelled synthetic CSV example are part of verification.

content-factory was studied for stage ordering, quality checkpoints and deliverables. Its end-to-end integrations were not run or installed as an active profile skill. Native Kanban owns all orchestration instead.

agent-reach remains reference-only; its installer and router are not executed. The project implements a narrower native integration with pinned DDGS, yt-dlp and faster-whisper packages, official-image FFmpeg, and a fixed Neuralwatt vision endpoint. It uses no platform login/cookies and retrieves one public clip at a time. See [reference capability](references.md) for exact scope and live evidence. Other Agent Reach backends remain uninstalled.

Ootto MCP, Filesystem MCP, Apify, Composio, authenticated Instagram APIs, Sandcastles, Remotion, Seedance/Runway, Agent Reach and paid media generation remain disabled. No prompts are evidence of a working integration. Deterministic checks prove discovery and native file/lifecycle functions; live intended-use examples are separately recorded in the verification report and per-skill manifest.
